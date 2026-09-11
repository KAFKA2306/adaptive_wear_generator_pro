import logging
import time
from typing import Optional, Set

import bmesh
import bpy
from bpy.types import Operator

from . import core_generators, core_materials, core_utils

logger = logging.getLogger(__name__)


class _GenerationSceneSnapshot:
    """Track Blender state owned by one generation attempt and roll it back on failure."""

    def __init__(self, context: bpy.types.Context) -> None:
        self._object_ids = {obj.as_pointer() for obj in bpy.data.objects}
        self._mesh_ids = {mesh.as_pointer() for mesh in bpy.data.meshes}
        self._material_ids = {material.as_pointer() for material in bpy.data.materials}
        self._active_object = context.view_layer.objects.active
        self._selected_objects = tuple(context.selected_objects)

    def rollback(self, context: bpy.types.Context) -> list[str]:
        errors: list[str] = []

        for obj in list(bpy.data.objects):
            if obj.as_pointer() not in self._object_ids:
                try:
                    bpy.data.objects.remove(obj, do_unlink=True)
                except Exception as exc:
                    errors.append(f"object {obj.name}: {exc}")

        for mesh in list(bpy.data.meshes):
            if mesh.as_pointer() not in self._mesh_ids and mesh.users == 0:
                try:
                    bpy.data.meshes.remove(mesh)
                except Exception as exc:
                    errors.append(f"mesh {mesh.name}: {exc}")

        for material in list(bpy.data.materials):
            if material.as_pointer() not in self._material_ids and material.users == 0:
                try:
                    bpy.data.materials.remove(material)
                except Exception as exc:
                    errors.append(f"material {material.name}: {exc}")

        try:
            for obj in context.view_layer.objects:
                obj.select_set(False)
            for obj in self._selected_objects:
                if obj.name in context.view_layer.objects:
                    obj.select_set(True)
            if self._active_object is not None and self._active_object.name in context.view_layer.objects:
                context.view_layer.objects.active = self._active_object
            else:
                context.view_layer.objects.active = None
        except Exception as exc:
            errors.append(f"selection restore: {exc}")

        return errors


class AWGP_OT_GenerateWear(Operator):
    bl_idname = "awgp.generate_wear"
    bl_label = "Generate Wear"
    bl_description = "ルールベースで衣装候補を生成します。要求された工程が成功した場合のみ完了します"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        props = context.scene.adaptive_wear_generator_pro
        return props.base_body is not None and props.wear_type != "NONE"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        props = context.scene.adaptive_wear_generator_pro
        is_valid, errors = props.validate_settings()
        if not is_valid:
            for error in errors:
                self.report({"ERROR"}, error)
            return {"CANCELLED"}

        started_at = time.time()
        snapshot = _GenerationSceneSnapshot(context)
        try:
            garment = self._generate_garment(props)
            if garment is None or getattr(garment, "type", None) != "MESH":
                raise RuntimeError("衣装生成結果が有効なメッシュではありません")

            self._apply_post_processing(garment, props)
            core_utils.select_single_object(garment)

            elapsed = time.time() - started_at
            logger.info("衣装生成完了: %s (%.2f秒)", garment.name, elapsed)
            self.report({"INFO"}, f"{props.wear_type} 生成完了: {garment.name} ({elapsed:.1f}秒)")
            return {"FINISHED"}
        except Exception as exc:
            cleanup_errors = snapshot.rollback(context)
            logger.exception("衣装生成失敗")
            if cleanup_errors:
                cleanup_detail = "; ".join(cleanup_errors)
                logger.error("衣装生成rollback失敗: %s", cleanup_detail)
                self.report({"ERROR"}, f"生成エラー: {exc}; rollbackエラー: {cleanup_detail}")
            else:
                self.report({"ERROR"}, f"生成エラー: {exc}")
            return {"CANCELLED"}

    def _generate_garment(self, props) -> Optional[bpy.types.Object]:
        if props.wear_type == "SKIRT":
            return core_generators.generate_pleated_skirt(props)
        return core_generators.UltimateAIWearGenerator(props).generate()

    def _apply_post_processing(self, garment: bpy.types.Object, props) -> None:
        if props.use_text_material and props.material_prompt:
            core_materials.apply_text_material(garment, props.wear_type, props.material_prompt)
            expected_material_prefix = "AWGP_AI_"
        else:
            core_materials.apply_default_material(garment, props.wear_type)
            expected_material_prefix = "AWGP_Default_"

        material = garment.data.materials[0] if garment.data.materials else None
        if material is None or not material.name.startswith(expected_material_prefix):
            raise RuntimeError("要求されたマテリアル適用を確認できません")

        if props.enable_cloth_sim:
            core_utils.setup_cloth_simulation(garment, props.base_body)
            if not any(mod.type == "CLOTH" for mod in garment.modifiers):
                raise RuntimeError("要求されたCloth modifierを確認できません")

        if props.auto_rigging:
            armature = core_utils.find_armature(props.base_body)
            if armature is None:
                raise RuntimeError("自動リギングが有効ですが素体のArmatureが見つかりません")
            core_utils.apply_rigging(garment, props.base_body, armature)
            if not any(
                mod.type == "ARMATURE" and mod.object == armature
                for mod in garment.modifiers
            ):
                raise RuntimeError("要求されたArmature modifierを確認できません")


class AWGP_OT_DiagnoseBones(Operator):
    bl_idname = "awgp.diagnose_bones"
    bl_label = "Diagnose Bones & Vertex Groups"
    bl_description = "アーマチュア、頂点グループ、メッシュ状態を診断します"
    bl_options = {"REGISTER"}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        body = context.scene.adaptive_wear_generator_pro.base_body
        if body is None or body.type != "MESH":
            self.report({"ERROR"}, "素体メッシュを選択してください")
            return {"CANCELLED"}

        try:
            armature = core_utils.find_armature(body)
            vertex_groups = {group.name for group in body.vertex_groups}
            bones = {bone.name for bone in armature.data.bones} if armature else set()

            bm = bmesh.new()
            try:
                bm.from_mesh(body.data)
                non_manifold_edges = sum(1 for edge in bm.edges if not edge.is_manifold)
                loose_vertices = sum(1 for vertex in bm.verts if not vertex.link_edges)
                ngons = sum(1 for face in bm.faces if len(face.verts) > 4)
            finally:
                bm.free()

            missing_vertex_groups = sorted(bones - vertex_groups)
            unmatched_vertex_groups = sorted(vertex_groups - bones) if bones else []
            logger.info(
                "診断 %s: vertices=%d faces=%d groups=%d bones=%d non_manifold_edges=%d loose_vertices=%d ngons=%d",
                body.name,
                len(body.data.vertices),
                len(body.data.polygons),
                len(vertex_groups),
                len(bones),
                non_manifold_edges,
                loose_vertices,
                ngons,
            )
            if missing_vertex_groups:
                logger.warning("ボーンに対応する頂点グループなし: %s", ", ".join(missing_vertex_groups))
            if unmatched_vertex_groups:
                logger.warning("ボーンに対応しない頂点グループ: %s", ", ".join(unmatched_vertex_groups))

            self.report(
                {"INFO"},
                f"診断完了: non-manifold edges={non_manifold_edges}, loose vertices={loose_vertices}",
            )
            return {"FINISHED"}
        except Exception as exc:
            logger.exception("診断失敗")
            self.report({"ERROR"}, f"診断エラー: {exc}")
            return {"CANCELLED"}
