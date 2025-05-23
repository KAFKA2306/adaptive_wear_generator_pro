# core/mesh_generator.py

import bpy
import bmesh
from . import bone_utils
from ..services import logging_service


def generate_wear_mesh(base_obj, wear_type, fit_settings):
    """指定された素体と衣装タイプに基づいてメッシュを生成するメイン関数"""
    if base_obj is None or base_obj.type != "MESH":
        logging_service.log_error("有効な素体オブジェクトが指定されていません")
        return None

    logging_service.log_info(f"{wear_type} メッシュ生成開始: 素体={base_obj.name}")

    generator_functions = {
        "PANTS": create_pants_mesh,
        "BRA": create_bra_mesh,
        "T_SHIRT": create_tshirt_mesh,
        "SOCKS": create_socks_mesh,
        "GLOVES": create_gloves_mesh,
    }

    generator_func = generator_functions.get(wear_type)
    if not generator_func:
        logging_service.log_error(f"未対応の衣装タイプ '{wear_type}' が指定されました")
        return None

    try:
        generated_mesh_obj = generator_func(base_obj, fit_settings)
        if generated_mesh_obj:
            logging_service.log_info(
                f"{wear_type} メッシュ生成完了: {generated_mesh_obj.name}"
            )
        return generated_mesh_obj
    except Exception as e:
        logging_service.log_error(f"{wear_type} メッシュ生成エラー: {str(e)}")
        return None


def create_pants_mesh(base_obj, fit_settings):
    """minimal_value_productを参考にしたパンツメッシュ生成"""
    logging_service.log_info(f"パンツメッシュ生成開始: 素体={base_obj.name}")

    # 腰部の頂点グループを柔軟に検索
    hip_patterns = ["hip", "hips", "pelvis", "waist", "腰"]
    hip_vg = bone_utils.find_vertex_group_by_patterns(base_obj, hip_patterns)

    if hip_vg is None:
        logging_service.log_error("腰部の頂点グループが見つかりません")
        return None

    logging_service.log_info(f"腰部頂点グループを使用: {hip_vg.name}")

    # メッシュを複製
    mesh = base_obj.data.copy()
    pants_obj = bpy.data.objects.new(base_obj.name + "_pants", mesh)
    bpy.context.collection.objects.link(pants_obj)

    try:
        # bmeshを使用して頂点を処理
        bm = bmesh.new()
        bm.from_mesh(mesh)

        # デフォームレイヤーを取得
        deform_layer = bm.verts.layers.deform.verify()

        # 腰部頂点グループのウェイトが高い頂点だけを残す
        hip_group_index = hip_vg.index
        selected_verts = []

        for vert in bm.verts:
            if hip_group_index in vert[deform_layer]:
                weight = vert[deform_layer][hip_group_index]
                if weight > 0.3:  # 閾値は調整可能
                    selected_verts.append(vert)

        # 選択されなかった頂点を削除
        verts_to_remove = [v for v in bm.verts if v not in selected_verts]
        bmesh.ops.delete(bm, geom=verts_to_remove, context="VERTS")

        # 軽く押し出して厚みを作る
        for vert in bm.verts:
            vert.co += vert.normal * fit_settings.thickness

        # メッシュに適用
        bm.to_mesh(mesh)
        bm.free()

        # スムーズシェード
        pants_obj.select_set(True)
        bpy.context.view_layer.objects.active = pants_obj
        bpy.ops.object.shade_smooth()

        logging_service.log_info("パンツメッシュ生成完了")
        return pants_obj

    except Exception as e:
        logging_service.log_error(f"パンツメッシュ生成エラー: {str(e)}")
        if pants_obj and pants_obj.name in bpy.data.objects:
            bpy.data.objects.remove(pants_obj, do_unlink=True)
        return None


def create_gloves_mesh(base_obj, fit_settings):
    """手袋メッシュ生成（画像のボーン構造に対応）"""
    logging_service.log_info(f"手袋メッシュ生成開始: 素体={base_obj.name}")

    # 手関連の頂点グループを検索
    left_hand, right_hand = bone_utils.find_hand_vertex_groups(base_obj)

    if not left_hand and not right_hand:
        logging_service.log_error("手の頂点グループが見つかりません")
        # 利用可能な頂点グループをログ出力
        if base_obj.vertex_groups:
            available_groups = [vg.name for vg in base_obj.vertex_groups]
            logging_service.log_info(f"利用可能な頂点グループ: {available_groups}")
        return None

    # 手関連の追加頂点グループも検索（指など）
    hand_related_groups = bone_utils.find_vertex_groups_by_type(base_obj, "hand")

    # メッシュを複製
    mesh = base_obj.data.copy()
    gloves_obj = bpy.data.objects.new(base_obj.name + "_gloves", mesh)
    bpy.context.collection.objects.link(gloves_obj)

    try:
        # bmeshを使用して頂点を処理
        bm = bmesh.new()
        bm.from_mesh(mesh)

        # デフォームレイヤーを取得
        deform_layer = bm.verts.layers.deform.verify()

        # 手関連の頂点を選択
        selected_verts = []
        target_groups = []

        if left_hand:
            target_groups.append(left_hand)
        if right_hand:
            target_groups.append(right_hand)

        # 追加の手関連グループも含める
        target_groups.extend(hand_related_groups)

        for vert in bm.verts:
            for vg in target_groups:
                if vg.index in vert[deform_layer]:
                    weight = vert[deform_layer][vg.index]
                    if weight > 0.1:  # 手袋は低い閾値で広範囲をカバー
                        selected_verts.append(vert)
                        break

        if not selected_verts:
            logging_service.log_error("手袋生成用の頂点が選択されませんでした")
            bm.free()
            bpy.data.objects.remove(gloves_obj, do_unlink=True)
            return None

        # 選択されなかった頂点を削除
        verts_to_remove = [v for v in bm.verts if v not in selected_verts]
        bmesh.ops.delete(bm, geom=verts_to_remove, context="VERTS")

        # 指なし手袋の処理
        if hasattr(fit_settings, "glove_fingers") and not fit_settings.glove_fingers:
            # 指部分を削除（実装は必要に応じて拡張）
            logging_service.log_info("指なし手袋モード（基本実装）")

        # 厚みを追加
        for vert in bm.verts:
            vert.co += vert.normal * fit_settings.thickness

        # メッシュに適用
        bm.to_mesh(mesh)
        bm.free()

        # スムーズシェード
        gloves_obj.select_set(True)
        bpy.context.view_layer.objects.active = gloves_obj
        bpy.ops.object.shade_smooth()

        logging_service.log_info("手袋メッシュ生成完了")
        return gloves_obj

    except Exception as e:
        logging_service.log_error(f"手袋メッシュ生成エラー: {str(e)}")
        if gloves_obj and gloves_obj.name in bpy.data.objects:
            bpy.data.objects.remove(gloves_obj, do_unlink=True)
        return None


def create_bra_mesh(base_obj, fit_settings):
    """ブラメッシュ生成"""
    logging_service.log_info(f"ブラメッシュ生成開始: 素体={base_obj.name}")

    # 胸部の頂点グループを検索
    chest_groups = bone_utils.find_vertex_groups_by_type(base_obj, "chest")

    if not chest_groups:
        logging_service.log_warning(
            "胸部の頂点グループが見つかりません。デフォルト処理を使用します。"
        )

    # メッシュを複製
    mesh = base_obj.data.copy()
    bra_obj = bpy.data.objects.new(base_obj.name + "_bra", mesh)
    bpy.context.collection.objects.link(bra_obj)

    try:
        # bmeshを使用して頂点を処理
        bm = bmesh.new()
        bm.from_mesh(mesh)

        if chest_groups:
            # 胸部頂点グループを使用
            deform_layer = bm.verts.layers.deform.verify()
            selected_verts = []

            for vert in bm.verts:
                for vg in chest_groups:
                    if vg.index in vert[deform_layer]:
                        weight = vert[deform_layer][vg.index]
                        if weight > 0.1:
                            selected_verts.append(vert)
                            break

            # 選択されなかった頂点を削除
            verts_to_remove = [v for v in bm.verts if v not in selected_verts]
            bmesh.ops.delete(bm, geom=verts_to_remove, context="VERTS")
        else:
            # デフォルト：Z軸上半分の簡易選択
            avg_z = sum(v.co.z for v in bm.verts) / len(bm.verts)
            verts_to_remove = [v for v in bm.verts if v.co.z < avg_z]
            bmesh.ops.delete(bm, geom=verts_to_remove, context="VERTS")

        # 厚みを追加
        for vert in bm.verts:
            vert.co += vert.normal * fit_settings.thickness

        # メッシュに適用
        bm.to_mesh(mesh)
        bm.free()

        # スムーズシェード
        bra_obj.select_set(True)
        bpy.context.view_layer.objects.active = bra_obj
        bpy.ops.object.shade_smooth()

        logging_service.log_info("ブラメッシュ生成完了")
        return bra_obj

    except Exception as e:
        logging_service.log_error(f"ブラメッシュ生成エラー: {str(e)}")
        if bra_obj and bra_obj.name in bpy.data.objects:
            bpy.data.objects.remove(bra_obj, do_unlink=True)
        return None


def create_tshirt_mesh(base_obj, fit_settings):
    """Tシャツメッシュ生成"""
    logging_service.log_info(f"Tシャツメッシュ生成開始: 素体={base_obj.name}")

    # 胴体・腕部の頂点グループを検索
    torso_groups = bone_utils.find_vertex_groups_by_type(base_obj, "chest")
    arm_groups = bone_utils.find_vertex_groups_by_type(base_obj, "arm")

    all_groups = torso_groups + arm_groups

    if not all_groups:
        logging_service.log_warning(
            "Tシャツ用の頂点グループが見つかりません。デフォルト処理を使用します。"
        )

    # メッシュを複製
    mesh = base_obj.data.copy()
    tshirt_obj = bpy.data.objects.new(base_obj.name + "_tshirt", mesh)
    bpy.context.collection.objects.link(tshirt_obj)

    try:
        # bmeshを使用して頂点を処理
        bm = bmesh.new()
        bm.from_mesh(mesh)

        if all_groups:
            # 頂点グループを使用
            deform_layer = bm.verts.layers.deform.verify()
            selected_verts = []

            for vert in bm.verts:
                for vg in all_groups:
                    if vg.index in vert[deform_layer]:
                        weight = vert[deform_layer][vg.index]
                        if weight > 0.1:
                            selected_verts.append(vert)
                            break

            # 選択されなかった頂点を削除
            verts_to_remove = [v for v in bm.verts if v not in selected_verts]
            bmesh.ops.delete(bm, geom=verts_to_remove, context="VERTS")
        else:
            # デフォルト：上半身の簡易選択
            avg_z = sum(v.co.z for v in bm.verts) / len(bm.verts)
            verts_to_remove = [v for v in bm.verts if v.co.z < avg_z * 0.5]
            bmesh.ops.delete(bm, geom=verts_to_remove, context="VERTS")

        # 厚みを追加
        for vert in bm.verts:
            vert.co += vert.normal * fit_settings.thickness

        # メッシュに適用
        bm.to_mesh(mesh)
        bm.free()

        # スムーズシェード
        tshirt_obj.select_set(True)
        bpy.context.view_layer.objects.active = tshirt_obj
        bpy.ops.object.shade_smooth()

        logging_service.log_info("Tシャツメッシュ生成完了")
        return tshirt_obj

    except Exception as e:
        logging_service.log_error(f"Tシャツメッシュ生成エラー: {str(e)}")
        if tshirt_obj and tshirt_obj.name in bpy.data.objects:
            bpy.data.objects.remove(tshirt_obj, do_unlink=True)
        return None


def create_socks_mesh(base_obj, fit_settings):
    """靴下メッシュ生成"""
    logging_service.log_info(f"靴下メッシュ生成開始: 素体={base_obj.name}")

    # 足部の頂点グループを検索
    foot_groups = bone_utils.find_vertex_groups_by_type(base_obj, "foot")
    leg_groups = bone_utils.find_vertex_groups_by_type(base_obj, "leg")

    all_groups = foot_groups + leg_groups

    if not all_groups:
        logging_service.log_error("靴下用の頂点グループが見つかりません")
        return None

    # メッシュを複製
    mesh = base_obj.data.copy()
    socks_obj = bpy.data.objects.new(base_obj.name + "_socks", mesh)
    bpy.context.collection.objects.link(socks_obj)

    try:
        # bmeshを使用して頂点を処理
        bm = bmesh.new()
        bm.from_mesh(mesh)

        # 頂点グループを使用
        deform_layer = bm.verts.layers.deform.verify()
        selected_verts = []

        for vert in bm.verts:
            for vg in all_groups:
                if vg.index in vert[deform_layer]:
                    weight = vert[deform_layer][vg.index]
                    # 靴下の長さを考慮した重み調整
                    min_weight = 0.1 * fit_settings.sock_length
                    if weight > min_weight:
                        selected_verts.append(vert)
                        break

        if not selected_verts:
            logging_service.log_error("靴下生成用の頂点が選択されませんでした")
            bm.free()
            bpy.data.objects.remove(socks_obj, do_unlink=True)
            return None

        # 選択されなかった頂点を削除
        verts_to_remove = [v for v in bm.verts if v not in selected_verts]
        bmesh.ops.delete(bm, geom=verts_to_remove, context="VERTS")

        # 厚みを追加
        for vert in bm.verts:
            vert.co += vert.normal * fit_settings.thickness

        # メッシュに適用
        bm.to_mesh(mesh)
        bm.free()

        # スムーズシェード
        socks_obj.select_set(True)
        bpy.context.view_layer.objects.active = socks_obj
        bpy.ops.object.shade_smooth()

        logging_service.log_info("靴下メッシュ生成完了")
        return socks_obj

    except Exception as e:
        logging_service.log_error(f"靴下メッシュ生成エラー: {str(e)}")
        if socks_obj and socks_obj.name in bpy.data.objects:
            bpy.data.objects.remove(socks_obj, do_unlink=True)
        return None


# 登録用のクラスリスト（空のタプル）
classes = ()
