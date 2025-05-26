import bpy
import bmesh
import mathutils
import time
from bpy.types import PropertyGroup, Operator
from bpy.props import (
    PointerProperty,
    EnumProperty,
    BoolProperty,
    FloatProperty,
    StringProperty,
    IntProperty,
    FloatVectorProperty,
)

from .core_base import (
    AWGLogger,
    performance_monitor,
    find_vertex_group_by_patterns,
    find_hand_vertex_groups,
    find_vertex_groups_by_type,
    ADVANCED_VERTEX_PATTERNS,
    SafeBlenderContext,
    log_info,
    log_warning,
    log_error,
    log_debug,
    transfer_weights,
    apply_rigging,
    apply_fitting,
    create_ai_principled_material,
    apply_wear_material,
)


class AIWearMeshGenerator:
    @staticmethod
    @performance_monitor
    def generate_wear_mesh(base_obj, wear_type, fit_settings):
        if not (base_obj and base_obj.type == "MESH"):
            log_error("有効な素体オブジェクトが指定されていません")
            return None
        log_info(f"{wear_type} メッシュ生成開始: 素体={base_obj.name}")
        gen_funcs = {
            "PANTS": AIWearMeshGenerator.create_ai_pants_mesh,
            "BRA": AIWearMeshGenerator.create_ai_bra_mesh,
            "T_SHIRT": AIWearMeshGenerator.create_ai_tshirt_mesh,
            "SOCKS": AIWearMeshGenerator.create_ai_socks_mesh,
            "GLOVES": AIWearMeshGenerator.create_ai_gloves_mesh,
        }
        gen_func = gen_funcs.get(wear_type)
        if not gen_func:
            log_error(f"未対応の衣装タイプ '{wear_type}'")
            return None
        try:
            gen_obj = gen_func(base_obj, fit_settings)
            if gen_obj:
                log_info(f"{wear_type} メッシュ生成完了: {gen_obj.name}")
            return gen_obj
        except Exception as e:
            log_error(f"{wear_type} メッシュ生成エラー: {str(e)}")
            import traceback

            traceback.print_exc()
            return None

    @staticmethod
    def _fix_duplicate_vertices(obj):
        log_debug(f"_fix_duplicate_vertices 開始: {obj.name}")
        try:
            original_mode = obj.mode
            if bpy.context.view_layer.objects.active != obj:
                bpy.context.view_layer.objects.active = obj
            if original_mode != "EDIT":
                bpy.ops.object.mode_set(mode="EDIT")
            mesh = obj.data
            bm = bmesh.from_edit_mesh(mesh)
            verts_before = len(bm.verts)
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
            verts_after = len(bm.verts)
            bmesh.update_edit_mesh(mesh)
            if original_mode != "EDIT":
                bpy.ops.object.mode_set(mode=original_mode)
            removed_count = verts_before - verts_after
            log_info(
                f"重複頂点修正: {removed_count} 個削除 ({obj.name})"
                if removed_count > 0
                else f"重複頂点修正: 削除なし ({obj.name})"
            )
            return True
        except Exception as e:
            log_error(f"重複頂点修正エラー: {str(e)} ({obj.name})")
            try:
                if bpy.context.object and bpy.context.object.mode == "EDIT":
                    bpy.ops.object.mode_set(mode="OBJECT")
            except RuntimeError:
                pass
            return False

    @staticmethod
    def _apply_smooth_operation(bm, factor=0.5, iterations=1):
        """bmesh.ops.smooth_vertの正しい使用方法"""
        try:
            for i in range(iterations):
                bmesh.ops.smooth_vert(
                    bm,
                    verts=bm.verts,
                    factor=factor,
                    use_axis_x=True,
                    use_axis_y=True,
                    use_axis_z=True,
                )
            log_debug(f"スムージング完了: factor={factor}, iterations={iterations}")
        except Exception as e:
            log_error(f"スムージングエラー: {str(e)}")

    @staticmethod
    @performance_monitor
    def create_ai_pants_mesh(base_obj, fit_settings):
        hip_vg = find_vertex_group_by_patterns(
            base_obj,
            ["hip", "hips", "pelvis", "waist", "腰", "hip_main", "pelvis_center"],
        )
        if not hip_vg:
            log_error("腰部の頂点グループが見つかりません")
            return None
        mesh = base_obj.data.copy()
        pants_obj = bpy.data.objects.new(f"{base_obj.name}_AI_pants", mesh)
        bpy.context.collection.objects.link(pants_obj)
        try:
            AIWearMeshGenerator._fix_duplicate_vertices(pants_obj)
            bm = bmesh.new()
            bm.from_mesh(mesh)
            bm.verts.ensure_lookup_table()
            bm.faces.ensure_lookup_table()
            deform_layer = bm.verts.layers.deform.verify()
            selected_verts = [
                v
                for v in bm.verts
                if hip_vg.index in v[deform_layer]
                and v[deform_layer][hip_vg.index]
                > getattr(fit_settings, "ai_threshold", 0.3)
            ]
            bmesh.ops.delete(
                bm,
                geom=[v for v in bm.verts if v not in selected_verts],
                context="VERTS",
            )
            thickness = getattr(fit_settings, "thickness", 0.008) * getattr(
                fit_settings, "ai_thickness_multiplier", 1.0
            )
            for v in bm.verts:
                v.co += v.normal * thickness
            if getattr(fit_settings, "ai_quality_mode", False):
                # 修正: repeatパラメータを削除し、反復回数を指定
                AIWearMeshGenerator._apply_smooth_operation(
                    bm, factor=0.2, iterations=2
                )
                bmesh.ops.triangulate(bm, faces=bm.faces)
            bm.to_mesh(mesh)
            bm.free()
            AIWearMeshGenerator._apply_smooth_shading(pants_obj)
            return pants_obj
        except Exception as e:
            log_error(f"パンツメッシュ生成エラー: {str(e)}")
            if pants_obj and pants_obj.name in bpy.data.objects:
                bpy.data.objects.remove(pants_obj, do_unlink=True)
            return None

    @staticmethod
    @performance_monitor
    def create_ai_gloves_mesh(base_obj, fit_settings):
        left_hand, right_hand = find_hand_vertex_groups(base_obj)
        if not (left_hand or right_hand):
            log_error("手の頂点グループが見つかりません")
            return None
        target_groups = (
            ([left_hand] if left_hand else [])
            + ([right_hand] if right_hand else [])
            + find_vertex_groups_by_type(base_obj, "hand")
        )
        mesh = base_obj.data.copy()
        gloves_obj = bpy.data.objects.new(f"{base_obj.name}_AI_gloves", mesh)
        bpy.context.collection.objects.link(gloves_obj)
        try:
            AIWearMeshGenerator._fix_duplicate_vertices(gloves_obj)
            bm = bmesh.new()
            bm.from_mesh(mesh)
            bm.verts.ensure_lookup_table()
            deform_layer = bm.verts.layers.deform.verify()
            selected_verts = [
                v
                for v in bm.verts
                for vg in target_groups
                if vg.index in v[deform_layer]
                and v[deform_layer][vg.index]
                > getattr(fit_settings, "ai_hand_threshold", 0.1)
            ]
            selected_verts = list(set(selected_verts))
            if not selected_verts:
                log_error("手袋生成用の頂点が選択されませんでした")
                bm.free()
                bpy.data.objects.remove(gloves_obj, do_unlink=True)
                return None
            bmesh.ops.delete(
                bm,
                geom=[v for v in bm.verts if v not in selected_verts],
                context="VERTS",
            )
            if (
                hasattr(fit_settings, "glove_fingers")
                and not fit_settings.glove_fingers
            ):
                log_info("指なし手袋モード")
            thickness = getattr(fit_settings, "thickness", 0.008)
            for v in bm.verts:
                v.co += v.normal * thickness
            if getattr(fit_settings, "ai_quality_mode", False):
                # 修正: repeatパラメータを削除
                AIWearMeshGenerator._apply_smooth_operation(
                    bm, factor=0.15, iterations=1
                )
            bm.to_mesh(mesh)
            bm.free()
            AIWearMeshGenerator._apply_smooth_shading(gloves_obj)
            return gloves_obj
        except Exception as e:
            log_error(f"手袋メッシュ生成エラー: {str(e)}")
            if gloves_obj and gloves_obj.name in bpy.data.objects:
                bpy.data.objects.remove(gloves_obj, do_unlink=True)
            return None

    @staticmethod
    @performance_monitor
    def create_ai_bra_mesh(base_obj, fit_settings):
        chest_groups = find_vertex_groups_by_type(base_obj, "chest")
        if not chest_groups:
            log_warning("胸部の頂点グループが見つかりません。デフォルト処理を使用")
        mesh = base_obj.data.copy()
        bra_obj = bpy.data.objects.new(f"{base_obj.name}_AI_bra", mesh)
        bpy.context.collection.objects.link(bra_obj)
        try:
            AIWearMeshGenerator._fix_duplicate_vertices(bra_obj)
            bm = bmesh.new()
            bm.from_mesh(mesh)
            if chest_groups:
                deform_layer = bm.verts.layers.deform.verify()
                selected_verts = [
                    v
                    for v in bm.verts
                    for vg in chest_groups
                    if vg.index in v[deform_layer]
                    and v[deform_layer][vg.index]
                    > getattr(fit_settings, "ai_bra_threshold", 0.1)
                ]
                selected_verts = list(set(selected_verts))
                bmesh.ops.delete(
                    bm,
                    geom=[v for v in bm.verts if v not in selected_verts],
                    context="VERTS",
                )
            else:
                avg_z = sum(v.co.z for v in bm.verts) / len(bm.verts) if bm.verts else 0
                std_z = (
                    (sum((v.co.z - avg_z) ** 2 for v in bm.verts) / len(bm.verts))
                    ** 0.5
                    if bm.verts
                    else 0
                )
                threshold_z = avg_z + (std_z * 0.3)
                bmesh.ops.delete(
                    bm,
                    geom=[v for v in bm.verts if v.co.z < threshold_z],
                    context="VERTS",
                )
            thickness = getattr(fit_settings, "thickness", 0.008)
            for v in bm.verts:
                v.co += v.normal * thickness
            if getattr(fit_settings, "ai_quality_mode", False):
                # 修正: repeatパラメータを削除
                AIWearMeshGenerator._apply_smooth_operation(
                    bm, factor=0.25, iterations=2
                )
            bm.to_mesh(mesh)
            bm.free()
            AIWearMeshGenerator._apply_smooth_shading(bra_obj)
            return bra_obj
        except Exception as e:
            log_error(f"ブラメッシュ生成エラー: {str(e)}")
            if bra_obj and bra_obj.name in bpy.data.objects:
                bpy.data.objects.remove(bra_obj, do_unlink=True)
            return None

    @staticmethod
    @performance_monitor
    def create_ai_tshirt_mesh(base_obj, fit_settings):
        all_groups = find_vertex_groups_by_type(
            base_obj, "chest"
        ) + find_vertex_groups_by_type(base_obj, "arm")
        if not all_groups:
            log_warning("Tシャツ用の頂点グループが見つかりません。デフォルト処理を使用")
        mesh = base_obj.data.copy()
        tshirt_obj = bpy.data.objects.new(f"{base_obj.name}_AI_tshirt", mesh)
        bpy.context.collection.objects.link(tshirt_obj)
        try:
            AIWearMeshGenerator._fix_duplicate_vertices(tshirt_obj)
            bm = bmesh.new()
            bm.from_mesh(mesh)
            if all_groups:
                deform_layer = bm.verts.layers.deform.verify()
                selected_verts = [
                    v
                    for v in bm.verts
                    for vg in all_groups
                    if vg.index in v[deform_layer]
                    and v[deform_layer][vg.index]
                    > getattr(fit_settings, "ai_tshirt_threshold", 0.1)
                ]
                selected_verts = list(set(selected_verts))
                bmesh.ops.delete(
                    bm,
                    geom=[v for v in bm.verts if v not in selected_verts],
                    context="VERTS",
                )
            else:
                avg_z = sum(v.co.z for v in bm.verts) / len(bm.verts) if bm.verts else 0
                threshold_z = avg_z * 0.4
                bmesh.ops.delete(
                    bm,
                    geom=[v for v in bm.verts if v.co.z < threshold_z],
                    context="VERTS",
                )
            thickness = getattr(fit_settings, "thickness", 0.008)
            for v in bm.verts:
                v.co += v.normal * thickness
            if getattr(fit_settings, "ai_quality_mode", False):
                # 修正: repeatパラメータを削除
                AIWearMeshGenerator._apply_smooth_operation(
                    bm, factor=0.2, iterations=2
                )
            bm.to_mesh(mesh)
            bm.free()
            AIWearMeshGenerator._apply_smooth_shading(tshirt_obj)
            return tshirt_obj
        except Exception as e:
            log_error(f"Tシャツメッシュ生成エラー: {str(e)}")
            if tshirt_obj and tshirt_obj.name in bpy.data.objects:
                bpy.data.objects.remove(tshirt_obj, do_unlink=True)
            return None

    @staticmethod
    @performance_monitor
    def create_ai_socks_mesh(base_obj, fit_settings):
        all_groups = find_vertex_groups_by_type(
            base_obj, "foot"
        ) + find_vertex_groups_by_type(base_obj, "leg")
        if not all_groups:
            log_error("靴下用の頂点グループが見つかりません")
            return None
        mesh = base_obj.data.copy()
        socks_obj = bpy.data.objects.new(f"{base_obj.name}_AI_socks", mesh)
        bpy.context.collection.objects.link(socks_obj)
        try:
            AIWearMeshGenerator._fix_duplicate_vertices(socks_obj)
            bm = bmesh.new()
            bm.from_mesh(mesh)
            deform_layer = bm.verts.layers.deform.verify()
            min_weight = (
                0.1
                * getattr(fit_settings, "sock_length", 1.0)
                * getattr(fit_settings, "ai_sock_multiplier", 1.0)
            )
            selected_verts = [
                v
                for v in bm.verts
                for vg in all_groups
                if vg.index in v[deform_layer]
                and v[deform_layer][vg.index] > min_weight
            ]
            selected_verts = list(set(selected_verts))
            if not selected_verts:
                log_error("靴下生成用の頂点が選択されませんでした")
                bm.free()
                bpy.data.objects.remove(socks_obj, do_unlink=True)
                return None
            bmesh.ops.delete(
                bm,
                geom=[v for v in bm.verts if v not in selected_verts],
                context="VERTS",
            )
            thickness = getattr(fit_settings, "thickness", 0.008)
            for v in bm.verts:
                v.co += v.normal * thickness
            if getattr(fit_settings, "ai_quality_mode", False):
                # 修正: repeatパラメータを削除
                AIWearMeshGenerator._apply_smooth_operation(
                    bm, factor=0.18, iterations=1
                )
            bm.to_mesh(mesh)
            bm.free()
            AIWearMeshGenerator._apply_smooth_shading(socks_obj)
            return socks_obj
        except Exception as e:
            log_error(f"靴下メッシュ生成エラー: {str(e)}")
            if socks_obj and socks_obj.name in bpy.data.objects:
                bpy.data.objects.remove(socks_obj, do_unlink=True)
            return None

    @staticmethod
    def _apply_smooth_shading(obj):
        try:
            with SafeBlenderContext(obj):
                bpy.ops.object.shade_smooth()
        except Exception as e:
            log_error(f"スムーズシェード適用エラー: {str(e)}")


class UltimateAIWearGenerator:
    def __init__(self, props):
        self.props, self.base_obj, self.wear_type = (
            props,
            props.base_body,
            props.wear_type,
        )
        self.quality = getattr(props, "quality_level", "ULTIMATE")
        self.fit_settings = self._create_ai_fit_settings()
        self.generation_start_time = time.time()

    def _create_ai_fit_settings(self):
        class AIFitSettings:
            pass

        settings = AIFitSettings()
        for prop_name in [
            "thickness",
            "sock_length",
            "glove_fingers",
            "tight_fit",
            "ai_quality_mode",
            "ai_threshold",
            "ai_hand_threshold",
            "ai_bra_threshold",
            "ai_tshirt_threshold",
            "ai_thickness_multiplier",
            "ai_sock_multiplier",
            "ai_tight_offset",
            "ai_offset_multiplier",
        ]:
            setattr(settings, prop_name, getattr(self.props, prop_name, None))
        return settings

    @performance_monitor
    def generate(self):
        try:
            log_info(f"衣装生成開始: {self.wear_type}")
            AWGLogger.log_progress(1, 5, "メッシュ生成開始")
            garment = AIWearMeshGenerator.generate_wear_mesh(
                self.base_obj, self.wear_type, self.fit_settings
            )
            if not garment:
                return None
            AWGLogger.log_progress(2, 5, "フィッティング処理")
            apply_fitting(garment, self.base_obj, self.fit_settings)
            AWGLogger.log_progress(3, 5, "リギング処理")
            if armature := self._find_armature():
                apply_rigging(garment, self.base_obj, armature)
            AWGLogger.log_progress(4, 5, "マテリアル適用")
            apply_wear_material(garment, self.wear_type)
            AWGLogger.log_progress(5, 5, "品質向上処理")
            self._apply_ai_quality_enhancements_improved(garment)
            log_info(
                f"衣装生成完了: {garment.name}",
                time.time() - self.generation_start_time,
            )
            return garment
        except Exception as e:
            log_error(f"生成エラー: {str(e)}")
            import traceback

            traceback.print_exc()
            return None

    def _find_armature(self):
        for mod in self.base_obj.modifiers:
            if mod.type == "ARMATURE" and mod.object:
                return mod.object
        return None

    @performance_monitor
    def _apply_ai_quality_enhancements_improved(self, garment):
        try:
            log_info(f"品質向上処理開始: {garment.name}")
            with SafeBlenderContext(garment):
                if getattr(self.props, "enable_edge_smoothing", True):
                    self._apply_improved_edge_smoothing(garment)
                if self.quality == "ULTIMATE" and getattr(
                    self.props, "ai_subdivision", False
                ):
                    self._apply_subdivision_surface(garment)
                if getattr(self.props, "enable_cloth_sim", False):
                    self._setup_improved_cloth_simulation(garment)
            log_info(f"品質向上処理完了: {garment.name}")
        except Exception as e:
            log_error(f"品質向上処理エラー: {str(e)} ({garment.name})")
            import traceback

            traceback.print_exc()

    def _apply_improved_edge_smoothing(self, garment):
        log_info(f"エッジスムージング開始 (bmesh): {garment.name}")
        try:
            original_mode = garment.mode
            if bpy.context.view_layer.objects.active != garment:
                bpy.context.view_layer.objects.active = garment
            if original_mode != "EDIT":
                bpy.ops.object.mode_set(mode="EDIT")
            mesh = garment.data
            bm = bmesh.from_edit_mesh(mesh)
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            bm.faces.ensure_lookup_table()
            for edge in bm.edges:
                edge.smooth = True
            for face in bm.faces:
                face.smooth = True
            bmesh.update_edit_mesh(mesh)
            if original_mode != "EDIT":
                bpy.ops.object.mode_set(mode=original_mode)
            current_mode_for_autosmooth = garment.mode
            if current_mode_for_autosmooth != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")
            if hasattr(garment.data, "use_auto_smooth"):
                garment.data.use_auto_smooth = True
                garment.data.auto_smooth_angle = 1.0472
            if (
                current_mode_for_autosmooth != "OBJECT"
                and current_mode_for_autosmooth != garment.mode
            ):
                bpy.ops.object.mode_set(mode=current_mode_for_autosmooth)
            log_info(f"エッジスムージング完了 (bmesh): {garment.name}")
        except Exception as e:
            log_error(f"エッジスムージングエラー (bmesh): {str(e)} ({garment.name})")
            try:
                if bpy.context.object and bpy.context.object.mode == "EDIT":
                    bpy.ops.object.mode_set(mode="OBJECT")
            except RuntimeError:
                pass

    def _apply_subdivision_surface(self, garment):
        try:
            log_info(f"サブディビジョン適用開始: {garment.name}")
            for mod in [m for m in garment.modifiers if m.type == "SUBSURF"]:
                garment.modifiers.remove(mod)
            subsurf = garment.modifiers.new("AI_SubSurf", type="SUBSURF")
            subsurf.levels, subsurf.render_levels, subsurf.subdivision_type = (
                1,
                2,
                "CATMULL_CLARK",
            )
            log_info(f"サブディビジョン適用完了: {garment.name}")
        except Exception as e:
            log_error(f"サブディビジョン適用エラー: {str(e)} ({garment.name})")

    def _setup_improved_cloth_simulation(self, garment):
        try:
            log_info(f"クロスシミュレーション設定開始: {garment.name}")
            for mod in [m for m in garment.modifiers if m.type == "CLOTH"]:
                garment.modifiers.remove(mod)
            if not self._verify_mesh_for_cloth(garment):
                log_warning(
                    f"メッシュにクロスシミュレーション適用上の問題: {garment.name}"
                )
            cloth = garment.modifiers.new("AI_Cloth", type="CLOTH")
            s = cloth.settings
            cs = cloth.collision_settings
            s.quality, s.time_scale, s.mass, s.tension_stiffness = 15, 1.0, 0.15, 15
            s.compression_stiffness, s.shear_stiffness, s.bending_stiffness = 15, 5, 0.5
            cs.use_collision, cs.distance_min, cs.impulse_clamp = True, 0.015, 0.0
            s.air_damping, s.vertex_group_mass = 1.0, ""
            log_info(f"クロスシミュレーション設定完了: {garment.name}")
        except Exception as e:
            log_error(f"クロスシミュレーション設定エラー: {str(e)} ({garment.name})")

    def _verify_mesh_for_cloth(self, garment):
        try:
            if garment.hide_viewport or garment.hide_render:
                garment.hide_viewport, garment.hide_render = False, False
            mesh = garment.data
            if not (mesh.vertices and mesh.polygons):
                log_error("メッシュに頂点または面がありません")
                return False
            log_info(
                f"メッシュ検証完了: 頂点数={len(mesh.vertices)}, 面数={len(mesh.polygons)} ({garment.name})"
            )
            return True
        except Exception as e:
            log_error(f"メッシュ検証エラー: {str(e)} ({garment.name})")
            return False


__all__ = ["AIWearMeshGenerator", "UltimateAIWearGenerator"]
