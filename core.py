from bpy.types import PropertyGroup, Operator
from bpy.props import (
    PointerProperty,
    EnumProperty,
    BoolProperty,
    FloatProperty,
    IntProperty,
    StringProperty,
)
import bpy
import bmesh
from mathutils import Vector  # Vectorを使用するため追加

from .core_base import *
from .core_advanced import *


def poll_mesh_objects(self, obj):
    return obj.type == "MESH"


class AWGProPropertyGroup(PropertyGroup):
    base_body: PointerProperty(
        name="素体メッシュ", type=bpy.types.Object, poll=poll_mesh_objects
    )
    wear_type: EnumProperty(
        name="衣装タイプ",
        items=[
            ("NONE", "未選択", ""),
            ("T_SHIRT", "Tシャツ", ""),
            ("PANTS", "パンツ", ""),
            ("BRA", "ブラ", ""),
            ("SOCKS", "靴下", ""),
            ("GLOVES", "手袋", ""),
            ("SKIRT", "プリーツスカート", "プリーツスカートを生成"),
        ],
        default="T_SHIRT",
    )
    quality_level: EnumProperty(
        name="品質レベル",
        items=[
            ("ULTIMATE", "AI最高品質", ""),
            ("STABLE", "安定モード", ""),
            ("MEDIUM", "中品質", ""),
            ("HIGH", "高品質", ""),
        ],
        default="ULTIMATE",
    )
    tight_fit: BoolProperty(name="密着フィット", default=False)
    thickness: FloatProperty(
        name="厚み", default=0.01, min=0.001, max=0.1, step=0.1, precision=3
    )
    material_prompt: StringProperty(
        name="マテリアル指示",
        description="テキストでマテリアルの特徴を指定（例：シルク素材の光沢のあるエレガントな）",
        default="",
        maxlen=200,
    )

    use_text_material: BoolProperty(
        name="テキストマテリアル使用",
        description="テキストプロンプトからマテリアルを自動生成",
        default=False,
    )
    ai_quality_mode: BoolProperty(name="AI品質モード", default=True)
    ai_threshold: FloatProperty(name="AI閾値", default=0.3, min=0.0, max=1.0)
    ai_subdivision: BoolProperty(name="AIサブディビジョン", default=False)
    ai_thickness_multiplier: FloatProperty(
        name="AI厚み倍率", default=1.0, min=0.1, max=3.0
    )
    sock_length: FloatProperty(name="靴下の長さ", default=0.5, min=0.0, max=1.0)
    glove_fingers: BoolProperty(
        name="指あり手袋", default=False
    )  # Trueで指あり, Falseで指なし(ミトン)
    enable_cloth_sim: BoolProperty(name="クロスシミュレーション", default=True)
    enable_edge_smoothing: BoolProperty(name="エッジスムージング", default=True)
    progressive_fitting: BoolProperty(
        name="多段階フィット", default=True
    )  # UIのみ、実装はUltimateAIWearGenerator内
    preserve_shapekeys: BoolProperty(
        name="シェイプキー保持", default=True
    )  # UIのみ、実装はUltimateAIWearGenerator内
    use_vertex_groups: BoolProperty(name="頂点グループ使用", default=True)  # UIのみ
    min_weight: FloatProperty(
        name="最小ウェイト", default=0.1, min=0.0, max=1.0
    )  # UIのみ
    # AI拡張設定 (core_advancedのAIFitSettingsで利用されるもの)
    ai_hand_threshold: FloatProperty(name="AI 手閾値", default=0.1, min=0.0, max=1.0)
    ai_bra_threshold: FloatProperty(name="AI ブラ閾値", default=0.1, min=0.0, max=1.0)
    ai_tshirt_threshold: FloatProperty(
        name="AI Tシャツ閾値", default=0.1, min=0.0, max=1.0
    )
    ai_sock_multiplier: FloatProperty(name="AI 靴下倍率", default=1.0, min=0.1, max=3.0)
    ai_tight_offset: FloatProperty(
        name="AI 密着オフセット", default=0.001, min=0.0, max=0.1, precision=4
    )
    ai_offset_multiplier: FloatProperty(
        name="AI オフセット倍率", default=0.5, min=0.0, max=2.0
    )

    skirt_length: FloatProperty(
        name="スカート丈",
        description="スカートの丈の長さ (0.0で膝上、1.0で足首)",
        default=0.6,
        min=0.0,
        max=1.0,
    )

    pleat_count: IntProperty(
        name="プリーツ数",
        description="プリーツの数を設定（6-24推奨）",
        default=12,
        min=6,
        max=24,
    )

    pleat_depth: FloatProperty(
        name="プリーツ深さ",
        description="プリーツの折り込み深さ",
        default=0.05,
        min=0.01,
        max=0.2,
    )


class AWGP_OT_GenerateWear(Operator):
    bl_idname = "awgp.generate_wear"
    bl_label = "Generate Wear (AI Ultimate)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.adaptive_wear_generator_pro
        if not self._validate_inputs(props):
            return {"CANCELLED"}

        if props.wear_type == "SKIRT":
            log_info("プリーツスカート生成処理を開始します。")
            garment = create_skirt_mesh(props.base_body, props)
        else:
            try:
                generator = UltimateAIWearGenerator(props)
                garment = generator.generate()
            except Exception as e:
                self.report({"ERROR"}, f"生成エラー: {str(e)}")
                log_error(f"生成オペレーターエラー: {str(e)}")
                return {"CANCELLED"}
        # 4. マテリアル適用
        if garment:  # Only apply material if mesh generation was successful
            if props.use_text_material and props.material_prompt:
                apply_wear_material(garment, props.wear_type, props.material_prompt)
            else:
                apply_wear_material(garment, props.wear_type)

        # 5. 品質評価（Phase 2で追加済み）
        if (
            garment and props.wear_type == "SKIRT"
        ):  # Only evaluate if mesh generated and is SKIRT
            # プロパティからプリーツ数を安全に取得
            pleat_count = getattr(props, "pleat_count", 12)

            # 生成されたgarmentオブジェクトに対して評価を実行
            quality_report = evaluate_pleats_geometry(garment, pleat_count)

            if quality_report["total_score"] < 70:
                log_warning(f"品質スコア低下: {quality_report['total_score']}/100")
                for issue in quality_report["issues"]:
                    log_warning(f"改善要: {issue}")
            else:
                log_info(f"品質評価: {quality_report['total_score']}/100 (良好)")

        # Final selection and reporting
        if garment:
            log_info(f"安定版衣装生成完了: {garment.name}")  # Adapted log message
            bpy.ops.object.select_all(action="DESELECT")
            garment.select_set(True)
            context.view_layer.objects.active = garment
            self.report(
                {"INFO"}, f"{props.wear_type} 生成完了: {garment.name}"
            )  # Operator report
            return {"FINISHED"}
        else:
            log_error("衣装生成に失敗しました。")  # Added error log
            self.report({"ERROR"}, "衣装生成に失敗")  # Operator report
            return {"CANCELLED"}

    def _validate_inputs(self, props):
        if not props.base_body:
            self.report({"ERROR"}, "素体メッシュを選択してください")
            return False
        if props.base_body.type != "MESH":
            self.report({"ERROR"}, "メッシュオブジェクトを選択してください")
            return False
        if not props.base_body.data.vertices:
            self.report({"ERROR"}, "素体メッシュに頂点がありません")
            return False
        if len(props.base_body.data.vertices) > 100000:
            self.report(
                {"WARNING"}, "頂点数が多いため処理に時間がかかる可能性があります"
            )
        if props.wear_type == "NONE":
            self.report({"ERROR"}, "衣装タイプを選択してください")
            return False
        return True


class AWGP_OT_DiagnoseBones(Operator):
    bl_idname = "awgp.diagnose_bones"
    bl_label = "AI Diagnose Bones & Vertex Groups"
    bl_options = {"REGISTER"}

    def execute(self, context):
        props = context.scene.adaptive_wear_generator_pro
        if not props.base_body:
            self.report({"ERROR"}, "素体メッシュを選択してください")
            return {"CANCELLED"}
        armature = next(
            (
                mod.object
                for mod in props.base_body.modifiers
                if mod.type == "ARMATURE" and mod.object
            ),
            None,
        )
        if not armature:
            self.report(
                {"WARNING"},
                "アーマチュアが見つかりませんが、頂点グループのみ診断します",
            )
        self._ai_diagnose_bone_vertex_group_mapping(props.base_body, armature)
        left_hand, right_hand = find_hand_vertex_groups(props.base_body)
        msg = "AI対応診断完了。詳細はシステムコンソールを確認。"
        if left_hand and right_hand:
            msg += f" 手VG: {left_hand.name}, {right_hand.name}"
        elif found_hand := left_hand or right_hand:
            msg += f" 片手VGのみ発見: {found_hand.name}"
        else:
            msg += " 手の頂点グループが見つかりませんでした。"
        self.report({"INFO"}, msg)
        return {"FINISHED"}

    def _ai_diagnose_bone_vertex_group_mapping(self, mesh_obj, armature_obj=None):
        if not (mesh_obj and mesh_obj.vertex_groups):
            log_error("メッシュ/頂点グループが見つかりません")
            return
        log_info(f"=== {mesh_obj.name} の頂点グループ診断 ===")
        log_info(f"頂点グループ数: {len(mesh_obj.vertex_groups)}")
        vgs = [vg.name for vg in mesh_obj.vertex_groups]
        log_info(f"頂点グループ一覧: {vgs}")
        if armature_obj and armature_obj.type == "ARMATURE":
            log_info(f"=== {armature_obj.name} のボーン診断 ===")
            bones = [b.name for b in armature_obj.data.bones]
            log_info(f"ボーン数: {len(bones)}")
            log_info(f"ボーン一覧: {bones}")
            log_info("=== 対応関係チェック ===")
            for bone_name in bones:
                log_info(
                    f"✓ {bone_name}: 対応VGあり"
                    if bone_name in vgs
                    else f"✗ {bone_name}: 対応VGなし"
                )
            for vg_name in vgs:
                if vg_name not in bones:
                    log_warning(f"! {vg_name}: VGのみ（対応ボーンなし）")
        for group_type, patterns in ADVANCED_VERTEX_PATTERNS.items():
            found = find_vertex_groups_by_type(mesh_obj, group_type)
            log_info(
                f"{group_type}関連VG: {[g.name for g in found]}"
                if found
                else f"{group_type}関連VGは見つかりません"
            )


__all__ = ["AWGProPropertyGroup", "AWGP_OT_GenerateWear", "AWGP_OT_DiagnoseBones"]


def create_skirt_mesh(base_obj, fit_settings):
    """プリーツスカートメッシュ生成（詳細実装版）"""

    log_info(f"プリーツスカートメッシュ生成開始: 素体={base_obj.name}")

    try:
        # 1. 腰部頂点グループ検索（既存パターン準拠）
        hip_groups = find_vertex_groups_by_type(base_obj, "hip")
        leg_groups = find_vertex_groups_by_type(base_obj, "leg")

        if not hip_groups:
            log_error("腰部の頂点グループが見つかりません")
            return None

        # 2. メッシュ複製（既存パターン準拠）
        mesh = base_obj.data.copy()
        skirt_obj = bpy.data.objects.new(base_obj.name + "_skirt", mesh)
        bpy.context.collection.objects.link(skirt_obj)

        # 3. bmesh処理開始
        bm = bmesh.new()
        bm.from_mesh(mesh)
        deform_layer = bm.verts.layers.deform.verify()

        # 4. 腰部から下方向への辺ループ選択・抽出
        selected_verts = []
        target_groups = hip_groups + leg_groups

        for vert in bm.verts:
            for vg in target_groups:
                if vg.index in vert[deform_layer]:
                    weight = vert[deform_layer][vg.index]
                    # スカート丈に応じた重み調整
                    length_factor = getattr(fit_settings, "skirt_length", 0.6)
                    min_weight = 0.1 * length_factor
                    if weight > min_weight:
                        selected_verts.append(vert)
                        break

        if not selected_verts:
            raise Exception("スカート生成用の頂点が見つかりません")

        # 5. 不要な頂点を削除（スカート部分のみ残す）
        verts_to_remove = [v for v in bm.verts if v not in selected_verts]
        if verts_to_remove:
            bmesh.ops.delete(bm, geom=verts_to_remove, context="VERTS")

        # 6. プリーツ生成メイン処理
        create_pleats_geometry(bm, fit_settings)

        # 7. 厚み追加（既存パターン準拠）
        thickness = getattr(fit_settings, "thickness", 0.005)
        for vert in bm.verts:
            vert.co += vert.normal * thickness

        # 8. メッシュ適用
        bm.to_mesh(mesh)
        bm.free()

        # 9. スムーズシェード適用
        skirt_obj.select_set(True)
        bpy.context.view_layer.objects.active = skirt_obj
        bpy.ops.object.shade_smooth()

        log_info("プリーツスカートメッシュ生成完了")
        return skirt_obj

    except Exception as e:
        log_error(f"プリーツスカートメッシュ生成エラー: {str(e)}")
        if "skirt_obj" in locals() and skirt_obj and skirt_obj.name in bpy.data.objects:
            bpy.data.objects.remove(skirt_obj, do_unlink=True)
        return None


def create_pleats_geometry(bm, fit_settings):
    """プリーツ形状の生成（詳細実装）"""

    pleat_count = getattr(fit_settings, "pleat_count", 12)
    pleat_depth = getattr(fit_settings, "pleat_depth", 0.05)

    log_info(f"プリーツ生成: 数={pleat_count}, 深さ={pleat_depth}")

    # 1. 頂点の高さ別分類
    vert_levels = classify_vertices_by_height(bm)

    # 2. 各レベルでプリーツ形成
    for level, verts in vert_levels.items():
        if len(verts) < pleat_count:
            continue

        # 3. 頂点を角度順にソート
        center = calculate_center_point(verts)
        sorted_verts = sort_vertices_by_angle(verts, center)

        # 4. プリーツ数に応じた頂点選択（交互選択）
        pleat_indices = select_pleat_vertices(sorted_verts, pleat_count)

        # 5. 選択頂点をプリーツ深さに応じて移動
        apply_pleat_deformation(sorted_verts, pleat_indices, pleat_depth, center)


def classify_vertices_by_height(bm):
    """頂点を高さ別に分類"""
    levels = {}

    for vert in bm.verts:
        # Z座標を0.1単位で丸める
        height_level = round(vert.co.z / 0.1) * 0.1
        if height_level not in levels:
            levels[height_level] = []
        levels[height_level].append(vert)

    return levels


def calculate_center_point(verts):
    """頂点群の中心点を計算"""
    if not verts:
        return Vector((0, 0, 0))

    center = Vector((0, 0, 0))
    for vert in verts:
        center += vert.co
    center /= len(verts)

    return center


def sort_vertices_by_angle(verts, center):
    """中心点からの角度順に頂点をソート"""
    import math

    def angle_from_center(vert):
        vec = vert.co - center
        return math.atan2(vec.y, vec.x)

    return sorted(verts, key=angle_from_center)


def select_pleat_vertices(sorted_verts, pleat_count):
    """プリーツ数に応じて交互に頂点を選択"""
    total_verts = len(sorted_verts)
    step = total_verts // pleat_count

    # 交互選択パターン：0, 2, 4, ... (内側), 1, 3, 5, ... (外側)
    inner_indices = []  # 内側に移動する頂点
    outer_indices = []  # 外側に移動する頂点

    for i in range(pleat_count):
        base_idx = i * step
        if base_idx < total_verts:
            if i % 2 == 0:
                inner_indices.append(base_idx)
            else:
                outer_indices.append(base_idx)

    return {"inner": inner_indices, "outer": outer_indices}


def apply_pleat_deformation(sorted_verts, pleat_indices, pleat_depth, center):
    """プリーツ変形を適用"""

    # 内側頂点の処理（プリーツの谷）
    for idx in pleat_indices["inner"]:
        if idx < len(sorted_verts):
            vert = sorted_verts[idx]
            # 中心方向に移動
            direction = (center - vert.co).normalized()
            vert.co += direction * pleat_depth

    # 外側頂点の処理（プリーツの山）
    for idx in pleat_indices["outer"]:
        if idx < len(sorted_verts):
            vert = sorted_verts[idx]
            # 中心から離れる方向に移動
            direction = (vert.co - center).normalized()
            vert.co += direction * pleat_depth * 0.5  # 外側は内側の半分の移動量


def evaluate_pleats_geometry(skirt_obj, pleat_count):
    """プリーツの幾何学的精度評価（0-100点）"""

    log_info(
        f"プリーツ幾何評価開始: オブジェクト={skirt_obj.name}, プリーツ数={pleat_count}"
    )

    quality_score = 0
    issues = []

    # 1. プリーツ角度の均等性チェック
    expected_angle = 360.0 / pleat_count
    actual_angles = calculate_pleat_angles(skirt_obj)  # この関数は別途実装が必要です

    # 角度の分散を計算（例：標準偏差や最大偏差）
    if actual_angles:
        angle_variance = max(abs(angle - expected_angle) for angle in actual_angles)
        log_debug(f"プリーツ角度分散: {angle_variance:.2f}")

        # 評価基準（例：分散が小さいほど高得点）
        if angle_variance < 5.0:  # 許容範囲の例
            quality_score += 40
        elif angle_variance < 10.0:
            quality_score += 20
        else:
            issues.append(f"プリーツ角度の不均等: 分散 {angle_variance:.2f}")
    else:
        issues.append("プリーツ角度の計算に失敗しました")

    # 2. プリーツ深度の一貫性チェック
    depth_consistency = check_pleat_depth_consistency(
        skirt_obj
    )  # この関数は別途実装が必要です
    log_debug(f"プリーツ深度一貫性: {depth_consistency:.2f}")

    # 評価基準（例：一貫性が高いほど高得点、1.0が理想）
    if depth_consistency > 0.95:  # 高い一貫性の例
        quality_score += 35
    elif depth_consistency > 0.8:
        quality_score += 20
    else:
        issues.append(f"プリーツ深度の一貫性不足: {depth_consistency:.2f}")

    # 3. メッシュ品質チェック
    mesh_quality_score = evaluate_mesh_quality(
        skirt_obj
    )  # この関数は別途実装が必要です
    log_debug(f"メッシュ品質スコア: {mesh_quality_score:.2f}")

    # 評価基準（例：メッシュ品質スコアをそのまま加算、最大25点）
    quality_score += min(
        25, max(0, int(mesh_quality_score))
    )  # スコアを0-25に正規化または制限

    if mesh_quality_score < 15:  # 低いメッシュ品質の例
        issues.append(f"メッシュ品質の問題: スコア {mesh_quality_score:.2f}")

    # 合計スコアを100点満点に調整（必要に応じて）
    # 例: quality_score = min(100, quality_score)

    log_info(f"プリーツ幾何評価完了: スコア={quality_score}/100")

    # 4. 結果レポート生成
    report = {
        "total_score": quality_score,
        "angle_variance": angle_variance if actual_angles else None,
        "depth_consistency": depth_consistency,
        "mesh_quality_score": mesh_quality_score,
        "issues": issues,
        "recommendations": generate_improvement_suggestions(
            issues
        ),  # この関数は別途実装が必要です
    }


def apply_wear_material(garment_obj, wear_type, material_prompt=None):
    """生成された衣装メッシュにマテリアルを適用する（テキスト対応版）"""

    if garment_obj is None or garment_obj.type != "MESH":
        log_error("マテリアル適用対象として有効な衣装オブジェクトが指定されていません")
        return False

    try:
        garment_obj.data.materials.clear()

        # テキストプロンプトが指定されている場合
        if material_prompt and material_prompt.strip():
            log_info(f"テキストベースマテリアル生成: '{material_prompt}'")
            material = generate_material_from_text(material_prompt, wear_type)
        else:
            # 従来のデフォルトマテリアル
            color_map = {
                "PANTS": (0.2, 0.3, 0.8, 1.0),
                "T_SHIRT": (0.8, 0.8, 0.8, 1.0),
                "BRA": (0.9, 0.7, 0.8, 1.0),
                "SOCKS": (0.1, 0.1, 0.1, 1.0),
                "GLOVES": (0.3, 0.2, 0.1, 1.0),
                "SKIRT": (0.5, 0.2, 0.7, 1.0),  # 新規追加
            }

            color = color_map.get(wear_type, (0.5, 0.5, 0.5, 1.0))
            material_name = f"{wear_type}_Default_Material"
            # 既存のcreate_principled_material関数を使用
            try:
                material = create_principled_material(
                    name=material_name, base_color=color
                )
            except NameError:
                log_error(
                    "create_principled_material関数が見つかりません。core.py内に存在するか確認してください。"
                )
                return False

        if material:
            garment_obj.data.materials.append(material)
            log_info(f"マテリアル '{material.name}' を適用しました")
            return True
        else:
            log_error("マテリアルの作成に失敗しました")
            return False

    except Exception as e:
        log_error(f"マテリアル適用中にエラーが発生しました: {str(e)}")
        return False


def evaluate_mesh_quality(skirt_obj):
    """メッシュ品質の評価"""
    # TODO: 非多様体エッジ、面法線の一貫性、重複頂点などをチェックし、メッシュ品質を評価するロジックを実装
    # Blender APIのbmeshやbpy.ops.mesh.select_non_manifold等の活用を検討
    log_warning("evaluate_mesh_quality関数は未実装です")
    return 0.0  # 未実装のため0.0を返す


def generate_improvement_suggestions(issues):
    """課題に基づいた改善提案を生成"""
    # TODO: issuesリストの内容に応じて、具体的な改善提案を生成するロジックを実装
    log_debug("generate_improvement_suggestions関数は未実装です")
    return ["自動改善提案機能は未実装です。"]  # 未実装のため固定メッセージを返す


def generate_material_from_text(text_prompt, wear_type):
    """テキストプロンプトからマテリアル設定を生成（FashionCLIPライク）"""

    log_info(f"テキストマテリアル生成開始: '{text_prompt}'")

    # 日本語材質キーワードマップ
    material_keywords = {
        "シルク": {"roughness": 0.1, "metallic": 0.0, "specular": 0.8, "sheen": 0.5},
        "サテン": {"roughness": 0.2, "metallic": 0.0, "specular": 0.9, "sheen": 0.8},
        "レザー": {"roughness": 0.7, "metallic": 0.0, "specular": 0.3, "sheen": 0.0},
        "デニム": {"roughness": 0.8, "metallic": 0.0, "specular": 0.1, "sheen": 0.0},
        "コットン": {"roughness": 0.9, "metallic": 0.0, "specular": 0.1, "sheen": 0.0},
        "ベルベット": {
            "roughness": 1.0,
            "metallic": 0.0,
            "specular": 0.0,
            "sheen": 0.0,
        },
        "メタル": {"roughness": 0.1, "metallic": 1.0, "specular": 1.0, "sheen": 0.0},
        "ゴム": {"roughness": 0.0, "metallic": 0.0, "specular": 0.9, "sheen": 0.0},
    }

    # 色キーワードマップ
    color_keywords = {
        "赤": (0.8, 0.1, 0.1, 1.0),
        "青": (0.1, 0.3, 0.8, 1.0),
        "緑": (0.1, 0.6, 0.2, 1.0),
        "白": (0.9, 0.9, 0.9, 1.0),
        "黒": (0.05, 0.05, 0.05, 1.0),
        "金": (0.8, 0.7, 0.2, 1.0),
        "銀": (0.7, 0.7, 0.7, 1.0),
        "ピンク": (0.9, 0.6, 0.7, 1.0),
        "紫": (0.6, 0.2, 0.8, 1.0),
    }

    # 特殊効果キーワード
    effect_keywords = {
        "光沢": {"specular_boost": 0.3, "roughness_reduce": -0.2},
        "マット": {"specular_boost": -0.4, "roughness_boost": 0.3},
        "メタリック": {"metallic_boost": 0.5},
        "透明": {"alpha_reduce": -0.3, "transmission_boost": 0.5},
        "半透明": {"alpha_reduce": -0.1, "transmission_boost": 0.2},
    }

    # テキスト解析実行
    material_settings = analyze_material_text(
        text_prompt, material_keywords, color_keywords, effect_keywords
    )

    # マテリアル名生成
    material_name = f"{wear_type}_{text_prompt[:20]}_AI_Material"

    return create_principled_material_enhanced(name=material_name, **material_settings)


def analyze_material_text(prompt, materials, colors, effects):
    """テキスト解析実行"""

    # デフォルト設定
    settings = {
        "base_color": (0.8, 0.8, 0.8, 1.0),
        "roughness": 0.5,
        "metallic": 0.0,
        "specular": 0.5,
        "alpha": 1.0,
        "sheen": 0.0,
        "transmission": 0.0,
    }

    prompt_lower = prompt.lower()
    used_keywords = []

    # 材質キーワード検索
    for material, props in materials.items():
        if material in prompt_lower:
            settings.update(props)
            used_keywords.append(material)
            log_debug(f"材質キーワード適用: {material}")

    # 色キーワード検索
    for color, rgba in colors.items():
        if color in prompt_lower:
            settings["base_color"] = rgba
            used_keywords.append(color)
            log_debug(f"色キーワード適用: {color}")

    # 特殊効果適用
    for effect, modifiers in effects.items():
        if effect in prompt_lower:
            for mod_key, mod_value in modifiers.items():
                if mod_key == "specular_boost":
                    settings["specular"] = min(1.0, settings["specular"] + mod_value)
                elif mod_key == "roughness_reduce":
                    settings["roughness"] = max(0.0, settings["roughness"] + mod_value)
                # 他の修正子も同様に処理...
            used_keywords.append(effect)
            log_debug(f"特殊効果適用: {effect}")

    log_info(f"使用キーワード: {', '.join(used_keywords)}")
    return settings


def create_principled_material_enhanced(name, **kwargs):
    """拡張Principled BSDFマテリアル作成"""

    # 既存のcreate_principled_material()を拡張
    # create_principled_material関数がcore.py内に存在することを前提とします。
    # 存在しない場合は、別途実装またはインポートが必要です。
    try:
        material = create_principled_material(
            name=name,
            base_color=kwargs.get("base_color", (0.8, 0.8, 0.8, 1.0)),
            alpha=kwargs.get("alpha", 1.0),
            specular=kwargs.get("specular", 0.5),
            roughness=kwargs.get("roughness", 0.5),
        )
    except NameError:
        log_error(
            "create_principled_material関数が見つかりません。core.py内に存在するか確認してください。"
        )
        return None

    if material and material.use_nodes:
        principled = None
        for node in material.node_tree.nodes:
            if node.type == "BSDF_PRINCIPLED":
                principled = node
                break

        if principled:
            # Blender 4.x対応の追加設定
            if "Sheen Weight" in principled.inputs:
                principled.inputs["Sheen Weight"].default_value = kwargs.get(
                    "sheen", 0.0
                )
            if "Transmission Weight" in principled.inputs:
                principled.inputs["Transmission Weight"].default_value = kwargs.get(
                    "transmission", 0.0
                )
            # 他のPrincipled BSDFプロパティも必要に応じてここに追加

    return material
