import bpy
import bmesh
import re
import mathutils
from bpy.types import PropertyGroup, Operator
from bpy.props import (
    PointerProperty,
    EnumProperty,
    BoolProperty,
    FloatProperty,
    StringProperty,
)


# =============================================================================
# ロギングシステム
# =============================================================================
def log_info(message):
    """情報ログ出力"""
    print(f"[AWG INFO] {message}")


def log_warning(message):
    """警告ログ出力"""
    print(f"[AWG WARNING] {message}")


def log_error(message):
    """エラーログ出力"""
    print(f"[AWG ERROR] {message}")


def log_debug(message):
    """デバッグログ出力"""
    print(f"[AWG DEBUG] {message}")


# =============================================================================
# ボーン名正規化・頂点グループユーティリティ（bone_utils.py準拠）
# =============================================================================
BONE_ALIASES = {
    "pelvis": "hips",
    "waist": "hips",
    "spine0": "spine",
    "spine_0": "spine",
    "spine1": "spine",
    "spine_1": "spine",
    "spine2": "chest",
    "spine_2": "chest",
    "upperchest": "chest",
    "upper_chest": "chest",
    "thorax": "chest",
    "collar": "clavicle",
    "upperarm": "arm",
    "upper_arm": "arm",
    "lowerarm": "forearm",
    "lower_arm": "forearm",
    "elbow": "forearm",
    "thigh": "upperleg",
    "upleg": "upperleg",
    "upper_leg": "upperleg",
    "shin": "lowerleg",
    "calf": "lowerleg",
    "leg": "lowerleg",
    "ankle": "foot",
    "toebase": "toes",
    "bust": "breast",
    "breast_root": "breast_root",
    "breast1": "breast_1",
    "breast_1": "breast_1",
    "breast2": "breast_2",
    "breast_2": "breast_2",
    "bustdynamicbone": "breast",
    "boobs": "breast",
    "front_chest": "breast_upper",
}


def normalize_bone_name(bone_name, custom_prefix=None, custom_suffix=None):
    """ボーン名を正規化してBlender標準形式に変換（bone_utils.py準拠）"""
    if not bone_name:
        return ""

    name = bone_name.lower()
    log_debug(f"ボーン名正規化開始: '{bone_name}' -> '{name}'")

    # _endサフィックスの処理
    ends_with_end_suffix = False
    if name.endswith("_end"):
        ends_with_end_suffix = True
        name = name[:-4]  # "_end"を削除

    # カスタムプレフィックス・サフィックス除去
    if custom_prefix and name.startswith(custom_prefix.lower()):
        name = name[len(custom_prefix) :]
    if custom_suffix and name.endswith(custom_suffix.lower()):
        name = name[: -len(custom_suffix)]

    # 一般的なプレフィックス除去
    common_prefixes = ["mixamorig", "bip01", "bip", "character", "bone", "rig"]
    for prefix in common_prefixes:
        if name.startswith(prefix):
            name = re.sub(
                f"^{re.escape(prefix)}[\\._\\s]*", "", name, flags=re.IGNORECASE
            )
            break

    # 前後の区切り文字を削除
    name = name.strip("_. ")

    # サイド情報の正規化
    side_suffix = ""
    # 左右プレフィックスのチェック
    left_prefix_match = re.match(r"^(l|left)[\._\s]*", name, re.IGNORECASE)
    if left_prefix_match:
        side_suffix = "_l"
        name = name[left_prefix_match.end() :]
    else:
        right_prefix_match = re.match(r"^(r|right)[\._\s]*", name, re.IGNORECASE)
        if right_prefix_match:
            side_suffix = "_r"
            name = name[right_prefix_match.end() :]

    # 左右サフィックスのチェック（プレフィックスが見つからなかった場合）
    if not side_suffix:
        left_suffix_match = re.search(r"[\._\s]*(l|left)$", name, re.IGNORECASE)
        if left_suffix_match:
            side_suffix = "_l"
            name = name[: left_suffix_match.start()]
        else:
            right_suffix_match = re.search(r"[\._\s]*(r|right)$", name, re.IGNORECASE)
            if right_suffix_match:
                side_suffix = "_r"
                name = name[: right_suffix_match.start()]

    # 前後の区切り文字を再度削除
    name = name.strip("_. ")

    # 区切り文字の正規化
    name = re.sub(r"[\.\-\s]", "_", name)

    # キャメルケースをスネークケースに変換
    name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    name = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", name)
    name = re.sub(r"([A-Z])([A-Z])(?=[a-z])", r"\1_\2", name)

    # 小文字に変換
    name = name.lower()

    # 数字のサフィックスを削除
    name = re.sub(r"\.\d+$", "", name)
    name = re.sub(r"_\d+$", "", name)

    # エイリアス適用
    base_name_for_alias = name
    temp_side_suffix_for_alias = ""
    if base_name_for_alias.endswith("_l"):
        temp_side_suffix_for_alias = "_l"
        base_name_for_alias = base_name_for_alias[:-2].rstrip("_")
    elif base_name_for_alias.endswith("_r"):
        temp_side_suffix_for_alias = "_r"
        base_name_for_alias = base_name_for_alias[:-2].rstrip("_")

    if base_name_for_alias in BONE_ALIASES:
        name = BONE_ALIASES[base_name_for_alias] + temp_side_suffix_for_alias
    elif name in BONE_ALIASES:
        name = BONE_ALIASES[name]

    # _endサフィックスを復元
    if ends_with_end_suffix:
        name += "_end"

    # サイド情報を追加（まだ付いていない場合）
    if side_suffix and not name.endswith(("_l", "_r")):
        if not name.endswith(side_suffix[1:]):  # 既に"l"や"r"で終わっていない場合
            name += side_suffix

    # 連続するアンダースコアを正規化
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")

    log_debug(f"ボーン名正規化完了: '{bone_name}' -> '{name}'")
    return name


def find_vertex_group_by_patterns(mesh_obj, patterns):
    """指定されたパターンリストに基づいて頂点グループを柔軟に検索（bone_utils.py準拠）"""
    if not mesh_obj or not mesh_obj.vertex_groups:
        return None

    for pattern in patterns:
        # 完全一致
        for vg in mesh_obj.vertex_groups:
            if vg.name.lower() == pattern.lower():
                log_debug(f"頂点グループ完全一致: '{pattern}' -> '{vg.name}'")
                return vg

        # 正規化して比較
        normalized_pattern = normalize_bone_name(pattern)
        for vg in mesh_obj.vertex_groups:
            normalized_vg_name = normalize_bone_name(vg.name)
            if normalized_vg_name == normalized_pattern:
                log_debug(f"頂点グループ正規化一致: '{pattern}' -> '{vg.name}'")
                return vg

        # 部分一致
        for vg in mesh_obj.vertex_groups:
            if pattern.lower() in vg.name.lower():
                log_debug(f"頂点グループ部分一致: '{pattern}' -> '{vg.name}'")
                return vg

    log_warning(f"頂点グループが見つかりません: {patterns}")
    return None


def find_hand_vertex_groups(mesh_obj):
    """手関連の頂点グループを柔軟に検索（bone_utils.py準拠）"""
    if not mesh_obj or not mesh_obj.vertex_groups:
        return None, None

    # 画像で確認されたボーン構造に基づく検索パターン
    left_patterns = [
        "Hand_L",  # 画像で確認された形式
        "hand_l",
        "hand.l",
        "lefthand",
        "left_hand",
        "l_hand",
        "hand_left",
        "LeftHand",
        "Left_Hand",
    ]

    right_patterns = [
        "Hand_R",  # 画像で確認された形式
        "hand_r",
        "hand.r",
        "righthand",
        "right_hand",
        "r_hand",
        "hand_right",
        "RightHand",
        "Right_Hand",
    ]

    left_hand = find_vertex_group_by_patterns(mesh_obj, left_patterns)
    right_hand = find_vertex_group_by_patterns(mesh_obj, right_patterns)

    if left_hand:
        log_info(f"左手頂点グループ発見: '{left_hand.name}'")
    if right_hand:
        log_info(f"右手頂点グループ発見: '{right_hand.name}'")

    return left_hand, right_hand


def find_vertex_groups_by_type(mesh_obj, group_type):
    """指定されたタイプ（chest, hip, footなど）の頂点グループを検索（bone_utils.py準拠）"""
    if not mesh_obj or not mesh_obj.vertex_groups:
        return []

    type_patterns = {
        "chest": ["chest", "breast", "bust", "thorax", "upper_chest", "胸"],
        "hip": ["hip", "hips", "pelvis", "waist", "腰"],
        "foot": ["foot", "feet", "ankle", "toe", "足"],
        "leg": ["leg", "thigh", "shin", "calf", "upperleg", "lowerleg", "脚"],
        "arm": ["arm", "shoulder", "upperarm", "lowerarm", "forearm", "腕", "肩"],
        "hand": [
            "hand",
            "finger",
            "thumb",
            "index",
            "middle",
            "ring",
            "little",
            "手",
            "指",
        ],
    }

    patterns = type_patterns.get(group_type, [group_type])
    found_groups = []

    for pattern in patterns:
        for vg in mesh_obj.vertex_groups:
            if pattern.lower() in vg.name.lower() and vg not in found_groups:
                found_groups.append(vg)
                log_debug(f"'{group_type}'タイプ頂点グループ発見: '{vg.name}'")

    return found_groups


# =============================================================================
# 高品質メッシュ生成エンジン（mesh_generator.py準拠）
# =============================================================================
def generate_wear_mesh(base_obj, wear_type, fit_settings):
    """指定された素体と衣装タイプに基づいてメッシュを生成するメイン関数（mesh_generator.py準拠）"""
    if base_obj is None or base_obj.type != "MESH":
        log_error("有効な素体オブジェクトが指定されていません")
        return None

    log_info(f"{wear_type} メッシュ生成開始: 素体={base_obj.name}")

    generator_functions = {
        "PANTS": create_pants_mesh,
        "BRA": create_bra_mesh,
        "T_SHIRT": create_tshirt_mesh,
        "SOCKS": create_socks_mesh,
        "GLOVES": create_gloves_mesh,
    }

    generator_func = generator_functions.get(wear_type)
    if not generator_func:
        log_error(f"未対応の衣装タイプ '{wear_type}' が指定されました")
        return None

    try:
        generated_mesh_obj = generator_func(base_obj, fit_settings)
        if generated_mesh_obj:
            log_info(f"{wear_type} メッシュ生成完了: {generated_mesh_obj.name}")
        return generated_mesh_obj
    except Exception as e:
        log_error(f"{wear_type} メッシュ生成エラー: {str(e)}")
        import traceback

        traceback.print_exc()
        return None


def create_pants_mesh(base_obj, fit_settings):
    """パンツメッシュ生成（mesh_generator.py準拠）"""
    log_info(f"パンツメッシュ生成開始: 素体={base_obj.name}")

    # 腰部の頂点グループを柔軟に検索
    hip_patterns = ["hip", "hips", "pelvis", "waist", "腰"]
    hip_vg = find_vertex_group_by_patterns(base_obj, hip_patterns)

    if hip_vg is None:
        log_error("腰部の頂点グループが見つかりません")
        return None

    log_info(f"腰部頂点グループを使用: {hip_vg.name}")

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
        if verts_to_remove:
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

        log_info("パンツメッシュ生成完了")
        return pants_obj

    except Exception as e:
        log_error(f"パンツメッシュ生成エラー: {str(e)}")
        if pants_obj and pants_obj.name in bpy.data.objects:
            bpy.data.objects.remove(pants_obj, do_unlink=True)
        return None


def create_gloves_mesh(base_obj, fit_settings):
    """手袋メッシュ生成（mesh_generator.py準拠）"""
    log_info(f"手袋メッシュ生成開始: 素体={base_obj.name}")

    # 手関連の頂点グループを検索
    left_hand, right_hand = find_hand_vertex_groups(base_obj)

    if not left_hand and not right_hand:
        log_error("手の頂点グループが見つかりません")
        # 利用可能な頂点グループをログ出力
        if base_obj.vertex_groups:
            available_groups = [vg.name for vg in base_obj.vertex_groups]
            log_info(f"利用可能な頂点グループ: {available_groups}")
        return None

    # 手関連の追加頂点グループも検索（指など）
    hand_related_groups = find_vertex_groups_by_type(base_obj, "hand")

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
            log_error("手袋生成用の頂点が選択されませんでした")
            bm.free()
            bpy.data.objects.remove(gloves_obj, do_unlink=True)
            return None

        # 選択されなかった頂点を削除
        verts_to_remove = [v for v in bm.verts if v not in selected_verts]
        if verts_to_remove:
            bmesh.ops.delete(bm, geom=verts_to_remove, context="VERTS")

        # 指なし手袋の処理
        if hasattr(fit_settings, "glove_fingers") and not fit_settings.glove_fingers:
            log_info("指なし手袋モード（基本実装）")

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

        log_info("手袋メッシュ生成完了")
        return gloves_obj

    except Exception as e:
        log_error(f"手袋メッシュ生成エラー: {str(e)}")
        if gloves_obj and gloves_obj.name in bpy.data.objects:
            bpy.data.objects.remove(gloves_obj, do_unlink=True)
        return None


def create_bra_mesh(base_obj, fit_settings):
    """ブラメッシュ生成（mesh_generator.py準拠）"""
    log_info(f"ブラメッシュ生成開始: 素体={base_obj.name}")

    # 胸部の頂点グループを検索
    chest_groups = find_vertex_groups_by_type(base_obj, "chest")

    if not chest_groups:
        log_warning("胸部の頂点グループが見つかりません。デフォルト処理を使用します。")

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
            if verts_to_remove:
                bmesh.ops.delete(bm, geom=verts_to_remove, context="VERTS")
        else:
            # デフォルト：Z軸上半分の簡易選択
            avg_z = sum(v.co.z for v in bm.verts) / len(bm.verts)
            verts_to_remove = [v for v in bm.verts if v.co.z < avg_z]
            if verts_to_remove:
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

        log_info("ブラメッシュ生成完了")
        return bra_obj

    except Exception as e:
        log_error(f"ブラメッシュ生成エラー: {str(e)}")
        if bra_obj and bra_obj.name in bpy.data.objects:
            bpy.data.objects.remove(bra_obj, do_unlink=True)
        return None


def create_tshirt_mesh(base_obj, fit_settings):
    """Tシャツメッシュ生成（mesh_generator.py準拠）"""
    log_info(f"Tシャツメッシュ生成開始: 素体={base_obj.name}")

    # 胴体・腕部の頂点グループを検索
    torso_groups = find_vertex_groups_by_type(base_obj, "chest")
    arm_groups = find_vertex_groups_by_type(base_obj, "arm")

    all_groups = torso_groups + arm_groups

    if not all_groups:
        log_warning(
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
            if verts_to_remove:
                bmesh.ops.delete(bm, geom=verts_to_remove, context="VERTS")
        else:
            # デフォルト：上半身の簡易選択
            avg_z = sum(v.co.z for v in bm.verts) / len(bm.verts)
            verts_to_remove = [v for v in bm.verts if v.co.z < avg_z * 0.5]
            if verts_to_remove:
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

        log_info("Tシャツメッシュ生成完了")
        return tshirt_obj

    except Exception as e:
        log_error(f"Tシャツメッシュ生成エラー: {str(e)}")
        if tshirt_obj and tshirt_obj.name in bpy.data.objects:
            bpy.data.objects.remove(tshirt_obj, do_unlink=True)
        return None


def create_socks_mesh(base_obj, fit_settings):
    """靴下メッシュ生成（mesh_generator.py準拠）"""
    log_info(f"靴下メッシュ生成開始: 素体={base_obj.name}")

    # 足部の頂点グループを検索
    foot_groups = find_vertex_groups_by_type(base_obj, "foot")
    leg_groups = find_vertex_groups_by_type(base_obj, "leg")

    all_groups = foot_groups + leg_groups

    if not all_groups:
        log_error("靴下用の頂点グループが見つかりません")
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
                    min_weight = 0.1 * getattr(fit_settings, "sock_length", 1.0)
                    if weight > min_weight:
                        selected_verts.append(vert)
                        break

        if not selected_verts:
            log_error("靴下生成用の頂点が選択されませんでした")
            bm.free()
            bpy.data.objects.remove(socks_obj, do_unlink=True)
            return None

        # 選択されなかった頂点を削除
        verts_to_remove = [v for v in bm.verts if v not in selected_verts]
        if verts_to_remove:
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

        log_info("靴下メッシュ生成完了")
        return socks_obj

    except Exception as e:
        log_error(f"靴下メッシュ生成エラー: {str(e)}")
        if socks_obj and socks_obj.name in bpy.data.objects:
            bpy.data.objects.remove(socks_obj, do_unlink=True)
        return None


# =============================================================================
# ウェイト転送（weight_transfer.py準拠）
# =============================================================================
def transfer_weights(source_obj, target_obj):
    """素体オブジェクトから衣装オブジェクトへウェイト情報を転送する（weight_transfer.py準拠）"""
    if source_obj is None or source_obj.type != "MESH":
        log_error("ウェイト転送元として有効な素体オブジェクトが指定されていません")
        return False

    if target_obj is None or target_obj.type != "MESH":
        log_error("ウェイト転送先として有効な衣装オブジェクトが指定されていません")
        return False

    log_info(
        f"ウェイト転送処理を開始します (元: {source_obj.name}, 先: {target_obj.name})"
    )

    # 現在の状態を保存
    original_active_obj = bpy.context.view_layer.objects.active
    original_select_state = [obj for obj in bpy.context.selected_objects if obj]

    try:
        # ターゲットオブジェクトをアクティブにして選択
        bpy.ops.object.select_all(action="DESELECT")
        target_obj.select_set(True)
        bpy.context.view_layer.objects.active = target_obj

        # 既存のData Transferモディファイアを削除
        remove_existing_data_transfer_modifiers(target_obj)

        # Data Transferモディファイアを追加
        data_transfer_modifier = target_obj.modifiers.new(
            name="DataTransfer", type="DATA_TRANSFER"
        )
        data_transfer_modifier.object = source_obj

        # 頂点グループ転送の設定
        data_transfer_modifier.use_vert_data = True
        data_transfer_modifier.data_types_verts = {"VGROUP_WEIGHTS"}
        data_transfer_modifier.vert_mapping = "NEAREST"

        # 高品質設定
        data_transfer_modifier.layers_vgroup_select_src = "ALL"
        data_transfer_modifier.layers_vgroup_select_dst = "NAME"

        # モディファイアを適用（安全なコンテキストで）
        with bpy.context.temp_override(active_object=target_obj):
            bpy.ops.object.modifier_apply(modifier=data_transfer_modifier.name)

        log_info("ウェイト転送処理完了")
        return True

    except Exception as e:
        log_error(f"ウェイト転送中にエラーが発生しました: {str(e)}")
        return False

    finally:
        # 元の選択状態を復元
        try:
            bpy.ops.object.select_all(action="DESELECT")
            for obj in original_select_state:
                if obj and obj.name in bpy.data.objects:
                    obj.select_set(True)
            if original_active_obj and original_active_obj.name in bpy.data.objects:
                bpy.context.view_layer.objects.active = original_active_obj
            else:
                bpy.context.view_layer.objects.active = None
        except Exception as e:
            log_warning(f"選択状態復元中に警告: {str(e)}")


def remove_existing_data_transfer_modifiers(obj):
    """既存のData Transferモディファイアを削除"""
    modifiers_to_remove = [mod for mod in obj.modifiers if mod.type == "DATA_TRANSFER"]
    for modifier in modifiers_to_remove:
        obj.modifiers.remove(modifier)


# =============================================================================
# リギング処理（bone_brendshape_weight_transfer.py準拠）
# =============================================================================
def apply_rigging(garment_obj, base_obj, base_armature_obj):
    """生成された衣装メッシュに素体のボーン構造をコピーし、リギングを設定する"""
    if garment_obj is None or garment_obj.type != "MESH":
        log_error("有効な衣装オブジェクトが指定されていません")
        return False

    if base_obj is None or base_obj.type != "MESH":
        log_error("有効な素体メッシュオブジェクトが指定されていません")
        return False

    if base_armature_obj is None or base_armature_obj.type != "ARMATURE":
        log_error("有効な素体アーマチュアオブジェクトが指定されていません")
        return False

    log_info(
        f"リギング処理を開始します (衣装: {garment_obj.name}, 素体: {base_obj.name}, アーマチュア: {base_armature_obj.name})"
    )

    try:
        # 既存のArmatureモディファイアを削除
        remove_existing_armature_modifiers(garment_obj)

        # Armatureモディファイアを追加
        armature_modifier = garment_obj.modifiers.new(name="Armature", type="ARMATURE")
        armature_modifier.object = base_armature_obj
        armature_modifier.use_deform_preserve_volume = True

        # ウェイト転送処理
        if not transfer_weights(base_obj, garment_obj):
            log_error("ウェイト転送に失敗しました")
            return False

        log_info("リギング処理完了")
        return True

    except Exception as e:
        log_error(f"リギング処理中にエラーが発生しました: {str(e)}")
        return False


def remove_existing_armature_modifiers(obj):
    """既存のArmatureモディファイアを削除"""
    modifiers_to_remove = [mod for mod in obj.modifiers if mod.type == "ARMATURE"]
    for modifier in modifiers_to_remove:
        obj.modifiers.remove(modifier)


# =============================================================================
# フィッティングエンジン（fit_engine.py準拠）
# =============================================================================
def apply_fitting(garment_obj, base_obj, fit_settings):
    """生成された衣装メッシュを素体メッシュにフィットさせる（fit_engine.py準拠）"""
    if garment_obj is None or garment_obj.type != "MESH":
        log_error("有効な衣装オブジェクトが指定されていません")
        return False

    if base_obj is None or base_obj.type != "MESH":
        log_error("有効な素体オブジェクトが指定されていません")
        return False

    log_info(
        f"フィッティング処理を開始します (衣装: {garment_obj.name}, 素体: {base_obj.name})"
    )

    try:
        # 既存のShrinkwrapモディファイアを削除
        remove_existing_shrinkwrap_modifiers(garment_obj)

        # 現在のアクティブオブジェクトを保存
        original_active = bpy.context.view_layer.objects.active

        # 衣装オブジェクトをアクティブに設定
        bpy.context.view_layer.objects.active = garment_obj

        # Shrinkwrapモディファイアを追加
        shrinkwrap_modifier = garment_obj.modifiers.new(
            name="Shrinkwrap", type="SHRINKWRAP"
        )
        shrinkwrap_modifier.target = base_obj

        # フィット設定を反映
        configure_shrinkwrap_modifier(shrinkwrap_modifier, fit_settings)

        # モディファイアを適用（安全なコンテキストで）
        with bpy.context.temp_override(active_object=garment_obj):
            bpy.ops.object.modifier_apply(modifier=shrinkwrap_modifier.name)

        # 元のアクティブオブジェクトを復元
        if original_active:
            bpy.context.view_layer.objects.active = original_active

        log_info("フィッティング処理完了")
        return True

    except Exception as e:
        log_error(f"フィッティング処理中にエラーが発生しました: {str(e)}")
        return False


def remove_existing_shrinkwrap_modifiers(obj):
    """既存のShrinkwrapモディファイアを削除"""
    modifiers_to_remove = [mod for mod in obj.modifiers if mod.type == "SHRINKWRAP"]
    for modifier in modifiers_to_remove:
        obj.modifiers.remove(modifier)


def configure_shrinkwrap_modifier(modifier, fit_settings):
    """Shrinkwrapモディファイアの設定"""
    if getattr(fit_settings, "tight_fit", False):
        # 密着設定
        modifier.wrap_method = "PROJECT"
        modifier.use_project_x = True
        modifier.use_project_y = True
        modifier.use_project_z = True
        modifier.use_negative_direction = True
        modifier.use_positive_direction = True
        modifier.offset = 0.001  # 最小限のオフセット
    else:
        # 通常のフィット
        modifier.wrap_method = "NEAREST_SURFACEPOINT"
        modifier.offset = (
            fit_settings.thickness * 0.5
        )  # 厚みの半分をオフセットとして使用

    # 品質設定
    modifier.use_keep_above_surface = True


# =============================================================================
# マテリアル生成（material_generator.py準拠）
# =============================================================================
def create_principled_material(
    name, base_color=(0.8, 0.8, 0.8, 1.0), alpha=1.0, specular=0.5, roughness=0.5
):
    """Principled BSDFを使用したマテリアルを作成（material_generator.py準拠）"""
    # 既存のマテリアルをチェック
    if name in bpy.data.materials:
        return bpy.data.materials[name]

    # 新しいマテリアルを作成
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    # ブレンドモードを設定
    mat.blend_method = "OPAQUE" if alpha >= 1.0 else "BLEND"

    # ノードツリーをクリア
    mat.node_tree.nodes.clear()

    # Principled BSDFノードを追加
    principled = mat.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    principled.location = (0, 0)

    # Material Outputノードを追加
    output = mat.node_tree.nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (400, 0)

    # ノードを接続
    mat.node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    # プロパティを設定
    principled.inputs["Base Color"].default_value = base_color
    principled.inputs["Alpha"].default_value = alpha
    principled.inputs["Roughness"].default_value = roughness

    # Blender 4.x対応: Specular設定
    if "Specular IOR Level" in principled.inputs:
        # Blender 4.0以降
        principled.inputs["Specular IOR Level"].default_value = specular
    elif "Specular" in principled.inputs:
        # 従来のバージョン
        principled.inputs["Specular"].default_value = specular

    return mat


def apply_wear_material(garment_obj, wear_type):
    """生成された衣装メッシュにマテリアルを適用する"""
    if garment_obj is None or garment_obj.type != "MESH":
        log_error("マテリアル適用対象として有効な衣装オブジェクトが指定されていません")
        return False

    log_info(
        f"マテリアル適用処理を開始します (衣装: {garment_obj.name}, タイプ: {wear_type})"
    )

    try:
        # 既存のマテリアルスロットをクリア
        garment_obj.data.materials.clear()

        # デフォルト色マップ
        color_map = {
            "PANTS": (0.2, 0.3, 0.8, 1.0),
            "T_SHIRT": (0.8, 0.8, 0.8, 1.0),
            "BRA": (0.9, 0.7, 0.8, 1.0),
            "SOCKS": (0.1, 0.1, 0.1, 1.0),
            "GLOVES": (0.3, 0.2, 0.1, 1.0),
        }

        color = color_map.get(wear_type, (0.5, 0.5, 0.5, 1.0))
        material_name = f"{wear_type}_StableMaterial"

        material = create_principled_material(
            name=material_name, base_color=color, alpha=1.0, specular=0.5, roughness=0.5
        )

        if material:
            # マテリアルを衣装オブジェクトに適用
            garment_obj.data.materials.append(material)
            log_info(f"マテリアル '{material.name}' を適用しました")
            return True
        else:
            log_error("マテリアルの作成に失敗しました")
            return False

    except Exception as e:
        log_error(f"マテリアル適用中にエラーが発生しました: {str(e)}")
        return False


# =============================================================================
# 統合衣装生成エンジン
# =============================================================================
class StableWearGenerator:
    """安定動作していたプログラムを統合した最高品質衣装生成エンジン"""

    def __init__(self, props):
        self.props = props
        self.base_obj = props.base_body
        self.wear_type = props.wear_type
        self.quality = getattr(props, "quality_level", "MEDIUM")
        self.fit_settings = self._create_fit_settings()

    def _create_fit_settings(self):
        """fit_settings互換オブジェクト作成"""

        class FitSettings:
            def __init__(self, props):
                self.thickness = getattr(props, "thickness", 0.008)
                self.sock_length = getattr(props, "sock_length", 1.0)
                self.glove_fingers = getattr(props, "glove_fingers", True)
                self.tight_fit = getattr(props, "tight_fit", False)

        return FitSettings(self.props)

    def generate(self):
        """最高品質生成プロセス（安定版）"""
        try:
            log_info(f"安定版衣装生成開始: {self.wear_type}")

            # 1. メッシュ生成（mesh_generator.py準拠）
            garment = generate_wear_mesh(
                self.base_obj, self.wear_type, self.fit_settings
            )
            if not garment:
                return None

            # 2. フィッティング（fit_engine.py準拠）
            apply_fitting(garment, self.base_obj, self.fit_settings)

            # 3. リギング（bone_brendshape_weight_transfer.py準拠）
            armature = self._find_armature()
            if armature:
                apply_rigging(garment, self.base_obj, armature)

            # 4. マテリアル（material_generator.py準拠）
            apply_wear_material(garment, self.wear_type)

            log_info(f"安定版衣装生成完了: {garment.name}")
            return garment

        except Exception as e:
            log_error(f"生成エラー: {str(e)}")
            import traceback

            traceback.print_exc()
            return None

    def _find_armature(self):
        """アーマチュア検索"""
        for modifier in self.base_obj.modifiers:
            if modifier.type == "ARMATURE" and modifier.object:
                return modifier.object
        return None


# =============================================================================
# プロパティグループ（properties.py準拠）
# =============================================================================
def poll_mesh_objects(self, obj):
    """メッシュオブジェクトのみを選択可能にする"""
    return obj.type == "MESH"


class AWGProPropertyGroup(PropertyGroup):
    """AdaptiveWear Generator Pro のプロパティグループ（安定版統合）"""

    base_body: PointerProperty(
        name="素体メッシュ",
        description="衣装を適用するベースとなるメッシュオブジェクト",
        type=bpy.types.Object,
        poll=poll_mesh_objects,
    )

    wear_type: EnumProperty(
        name="衣装タイプ",
        description="生成する衣装のタイプを選択します",
        items=[
            ("NONE", "未選択", "衣装タイプが選択されていません"),
            ("T_SHIRT", "Tシャツ", "Tシャツを生成"),
            ("PANTS", "パンツ", "パンツを生成"),
            ("BRA", "ブラ", "ブラジャーを生成"),
            ("SOCKS", "靴下", "靴下を生成"),
            ("GLOVES", "手袋", "手袋を生成"),
        ],
        default="T_SHIRT",
    )

    quality_level: EnumProperty(
        name="品質レベル",
        description="生成する衣装の品質レベル",
        items=[
            ("STABLE", "安定モード", "実績のある安定版（推奨）"),
            ("MEDIUM", "中品質", "標準品質"),
            ("HIGH", "高品質", "高品質、処理時間長め"),
            ("ULTRA", "最高品質", "クロスシミュレーション含む最高品質"),
        ],
        default="STABLE",
    )

    tight_fit: BoolProperty(
        name="密着フィット",
        description="衣装のフィット感を素体に密着させる",
        default=False,
    )

    thickness: FloatProperty(
        name="厚み",
        description="衣装の厚みを設定します",
        default=0.01,
        min=0.001,
        max=0.1,
        step=0.1,
        precision=3,
    )

    # 衣装別設定
    sock_length: FloatProperty(
        name="靴下の長さ",
        description="靴下の長さを設定します (0.0で足首、1.0で膝上)",
        default=0.5,
        min=0.0,
        max=1.0,
    )

    glove_fingers: BoolProperty(
        name="指あり手袋",
        description="手袋に指の部分を生成するかどうか",
        default=False,
    )

    # 高品質設定
    enable_cloth_sim: BoolProperty(
        name="クロスシミュレーション",
        description="物理シミュレーションを適用して自然な形状を生成",
        default=True,
    )

    enable_edge_smoothing: BoolProperty(
        name="エッジスムージング",
        description="Bevelによるエッジの滑らか化",
        default=True,
    )

    progressive_fitting: BoolProperty(
        name="多段階フィット",
        description="粗いフィット→精密フィットの2段階処理",
        default=True,
    )

    # UI参照プロパティ（互換性）
    preserve_shapekeys: BoolProperty(
        name="シェイプキー保持",
        default=True,
    )

    use_vertex_groups: BoolProperty(
        name="頂点グループ使用",
        default=True,
    )

    min_weight: FloatProperty(
        name="最小ウェイト",
        default=0.1,
        min=0.0,
        max=1.0,
    )


# =============================================================================
# オペレーター（operators.py準拠）
# =============================================================================
class AWGP_OT_GenerateWear(Operator):
    """最高品質衣装生成オペレーター（安定版）"""

    bl_idname = "awgp.generate_wear"
    bl_label = "Generate Wear (Stable)"
    bl_description = "安定動作実績のある方式で衣装を生成"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.adaptive_wear_generator_pro

        # 入力検証
        if not self._validate_inputs(props):
            return {"CANCELLED"}

        try:
            generator = StableWearGenerator(props)
            garment = generator.generate()

            if garment:
                # 生成物を選択してアクティブに
                bpy.ops.object.select_all(action="DESELECT")
                garment.select_set(True)
                context.view_layer.objects.active = garment

                self.report({"INFO"}, f"{props.wear_type} 安定版生成完了")
                log_info(f"衣装生成成功: {garment.name}")
                return {"FINISHED"}
            else:
                self.report({"ERROR"}, "衣装生成に失敗")
                return {"CANCELLED"}

        except Exception as e:
            error_msg = f"生成エラー: {str(e)}"
            self.report({"ERROR"}, error_msg)
            log_error(error_msg)
            return {"CANCELLED"}

    def _validate_inputs(self, props):
        """入力検証（operators.py準拠）"""
        if not props.base_body:
            self.report({"ERROR"}, "素体メッシュを選択してください")
            return False

        if props.base_body.type != "MESH":
            self.report({"ERROR"}, "メッシュオブジェクトを選択してください")
            return False

        if len(props.base_body.data.vertices) == 0:
            self.report({"ERROR"}, "素体メッシュに頂点がありません")
            return False

        if props.wear_type == "NONE":
            self.report({"ERROR"}, "衣装タイプを選択してください")
            return False

        return True


# 診断オペレーター（diagnostic_operators.py準拠）
class AWGP_OT_DiagnoseBones(Operator):
    """ボーンと頂点グループの診断オペレーター（diagnostic_operators.py準拠）"""

    bl_idname = "awgp.diagnose_bones"
    bl_label = "Diagnose Bones & Vertex Groups"
    bl_description = "ボーンと頂点グループの対応関係を診断します"
    bl_options = {"REGISTER"}

    def execute(self, context):
        props = context.scene.adaptive_wear_generator_pro

        if not props.base_body:
            self.report({"ERROR"}, "素体メッシュを選択してください")
            return {"CANCELLED"}

        # アーマチュアを検索
        armature = None
        for modifier in props.base_body.modifiers:
            if modifier.type == "ARMATURE" and modifier.object:
                armature = modifier.object
                break

        if not armature:
            self.report(
                {"WARNING"},
                "アーマチュアが見つかりませんが、頂点グループのみ診断します",
            )

        # 診断実行
        self._diagnose_bone_vertex_group_mapping(props.base_body, armature)

        # 手関連の特別診断
        left_hand, right_hand = find_hand_vertex_groups(props.base_body)

        result_msg = "診断完了。詳細はシステムコンソールを確認してください。"
        if left_hand and right_hand:
            result_msg += f" 手の頂点グループ: {left_hand.name}, {right_hand.name}"
        elif left_hand or right_hand:
            found = left_hand or right_hand
            result_msg += f" 片手の頂点グループのみ発見: {found.name}"
        else:
            result_msg += " 手の頂点グループが見つかりませんでした。"

        self.report({"INFO"}, result_msg)
        return {"FINISHED"}

    def _diagnose_bone_vertex_group_mapping(self, mesh_obj, armature_obj=None):
        """メッシュオブジェクトのボーンと頂点グループの対応関係を診断"""
        if not mesh_obj or not mesh_obj.vertex_groups:
            log_error("メッシュオブジェクトまたは頂点グループが見つかりません")
            return

        log_info(f"=== {mesh_obj.name} の頂点グループ診断 ===")
        log_info(f"頂点グループ数: {len(mesh_obj.vertex_groups)}")

        # 頂点グループ一覧を表示
        vertex_groups = [vg.name for vg in mesh_obj.vertex_groups]
        log_info(f"頂点グループ一覧: {vertex_groups}")

        # アーマチュア情報も取得
        if armature_obj and armature_obj.type == "ARMATURE":
            log_info(f"=== {armature_obj.name} のボーン診断 ===")
            bones = [bone.name for bone in armature_obj.data.bones]
            log_info(f"ボーン数: {len(bones)}")
            log_info(f"ボーン一覧: {bones}")

            # ボーンと頂点グループの対応チェック
            log_info("=== 対応関係チェック ===")
            for bone_name in bones:
                if bone_name in vertex_groups:
                    log_info(f"✓ {bone_name}: 対応する頂点グループあり")
                else:
                    log_warning(f"✗ {bone_name}: 対応する頂点グループなし")

            # 逆チェック：頂点グループにあってボーンにないもの
            for vg_name in vertex_groups:
                if vg_name not in bones:
                    log_warning(f"! {vg_name}: 頂点グループのみ（対応ボーンなし）")

        # タイプ別チェック
        for group_type in ["hand", "chest", "hip", "foot", "leg", "arm"]:
            groups = find_vertex_groups_by_type(mesh_obj, group_type)
            if groups:
                group_names = [g.name for g in groups]
                log_info(f"{group_type}関連の頂点グループ: {group_names}")
            else:
                log_warning(f"{group_type}関連の頂点グループが見つかりません")


# =============================================================================
# エクスポート定義
# =============================================================================
__all__ = [
    "AWGProPropertyGroup",
    "AWGP_OT_GenerateWear",
    "AWGP_OT_DiagnoseBones",
]
