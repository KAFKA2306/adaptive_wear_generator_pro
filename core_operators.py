import bpy
import bmesh
import time
from bpy.types import Operator
from typing import Set, Optional, Dict, Any
import logging
from . import core_generators, core_utils, core_materials

logger = logging.getLogger(__name__)


class AWGP_OT_GenerateWear(Operator):
    bl_idname = "awgp.generate_wear"
    bl_label = "Generate Wear"
    bl_description = "AI駆動で衣装を自動生成します"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        awg_props = context.scene.adaptive_wear_generator_pro
        return awg_props.base_body is not None and awg_props.wear_type != "NONE"

    def execute(self, context: bpy.types.Context) -> Set[str]:
        props = context.scene.adaptive_wear_generator_pro

        is_valid, errors = props.validate_settings()
        if not is_valid:
            for error in errors:
                self.report({"ERROR"}, error)
            return {"CANCELLED"}

        start_time = time.time()
        logger.info(
            f"衣装生成開始: タイプ={props.wear_type}, 品質={props.quality_level}"
        )

        try:
            garment = self._generate_garment(props)
            if not garment:
                self.report({"ERROR"}, "衣装生成に失敗しました")
                return {"CANCELLED"}

            self._apply_post_processing(garment, props)
            core_utils.select_single_object(garment)

            elapsed_time = time.time() - start_time
            logger.info(
                f"衣装生成完了: {garment.name} (処理時間: {elapsed_time:.2f}秒)"
            )
            self.report(
                {"INFO"},
                f"{props.wear_type} 生成完了: {garment.name} ({elapsed_time:.1f}秒)",
            )
            return {"FINISHED"}

        except core_generators.AWGProException as e:
            logger.error(f"衣装生成エラー: {str(e)}")
            self.report({"ERROR"}, f"生成エラー: {str(e)}")
            return {"CANCELLED"}
        except Exception as e:
            logger.error(f"予期しない衣装生成エラー: {str(e)}")
            self.report({"ERROR"}, f"予期しないエラー: {str(e)}")
            return {"CANCELLED"}

    def _generate_garment(self, props) -> Optional[bpy.types.Object]:
        if props.wear_type == "SKIRT":
            return core_generators.generate_pleated_skirt(props)
        else:
            generator = core_generators.OptimizedAIWearGenerator(props)
            return generator.generate()

    def _apply_post_processing(self, garment: bpy.types.Object, props) -> None:
        try:
            if props.use_text_material and props.material_prompt:
                core_materials.apply_text_material(
                    garment, props.wear_type, props.material_prompt
                )
            else:
                core_materials.apply_default_material(garment, props.wear_type)

            if props.wear_type == "SKIRT":
                quality_report = core_utils.evaluate_pleats_geometry(
                    garment, props.pleat_count
                )
                if quality_report["total_score"] < 70:
                    logger.warning(
                        f"スカート品質スコアが低いです: {quality_report['total_score']}"
                    )

            if props.enable_cloth_sim:
                core_utils.setup_cloth_simulation(garment, props.base_body)

            if props.auto_rigging:
                armature = core_utils.find_armature(props.base_body)
                if armature:
                    core_utils.apply_rigging(garment, props.base_body, armature)
        except Exception as e:
            logger.error(f"ポストプロセシングエラー: {str(e)}")


class AWGP_OT_DiagnoseBones(Operator):
    bl_idname = "awgp.diagnose_bones"
    bl_label = "Diagnose Bones & Vertex Groups"
    bl_description = "アーマチュアと頂点グループの詳細診断を実行"
    bl_options = {"REGISTER"}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        props = context.scene.adaptive_wear_generator_pro
        if not props.base_body:
            self.report({"ERROR"}, "素体メッシュを選択してください")
            return {"CANCELLED"}

        try:
            armature = core_utils.find_armature(props.base_body)
            if not armature:
                self.report(
                    {"WARNING"},
                    "アーマチュアが見つかりませんが、頂点グループのみ診断します",
                )

            diagnostic_result = self._perform_diagnosis(props.base_body, armature)
            self._report_diagnosis(diagnostic_result)

            self.report({"INFO"}, "AI対応診断完了。詳細はシステムコンソールを確認。")
            return {"FINISHED"}

        except Exception as e:
            logger.error(f"診断エラー: {str(e)}")
            self.report({"ERROR"}, f"診断エラー: {str(e)}")
            return {"CANCELLED"}

    def _perform_diagnosis(
        self, mesh_obj: bpy.types.Object, armature_obj: Optional[bpy.types.Object]
    ) -> Dict[str, Any]:
        result = {
            "mesh_name": mesh_obj.name,
            "vertex_groups": [],
            "bones": [],
            "hand_groups": {},
            "mapping_issues": [],
            "mesh_quality": {},
            "compatibility_issues": [],
        }

        if mesh_obj.vertex_groups:
            result["vertex_groups"] = [vg.name for vg in mesh_obj.vertex_groups]
            logger.info(f"頂点グループ数: {len(result['vertex_groups'])}")

        if armature_obj and armature_obj.type == "ARMATURE":
            result["bones"] = [b.name for b in armature_obj.data.bones]
            logger.info(f"ボーン数: {len(result['bones'])}")

        result["mapping_issues"] = self._detect_mapping_issues(
            result["vertex_groups"], result["bones"]
        )
        result["mesh_quality"] = self._analyze_mesh_quality(mesh_obj)
        result["compatibility_issues"] = self._check_compatibility(mesh_obj)

        left_hand, right_hand = core_utils.find_hand_vertex_groups(mesh_obj)
        result["hand_groups"] = {
            "left": left_hand.name if left_hand else None,
            "right": right_hand.name if right_hand else None,
        }

        return result

    def _detect_mapping_issues(self, vertex_groups: list, bones: list) -> list:
        issues = []
        for bone_name in bones:
            if bone_name not in vertex_groups:
                issues.append(
                    f"ボーン '{bone_name}' に対応する頂点グループがありません"
                )

        for vg_name in vertex_groups:
            if vg_name not in bones:
                issues.append(f"頂点グループ '{vg_name}' に対応するボーンがありません")

        return issues

    def _analyze_mesh_quality(self, obj: bpy.types.Object) -> Dict[str, Any]:
        quality_info = {
            "vertex_count": len(obj.data.vertices),
            "face_count": len(obj.data.polygons),
            "edge_count": len(obj.data.edges),
            "has_ngons": False,
            "has_loose_vertices": False,
            "manifold_status": "unknown",
        }

        try:
            bm = bmesh.new()
            bm.from_mesh(obj.data)

            quality_info["has_ngons"] = any(len(face.verts) > 4 for face in bm.faces)
            quality_info["has_loose_vertices"] = any(
                len(vert.link_edges) == 0 for vert in bm.verts
            )

            if hasattr(bm, "is_valid"):
                quality_info["manifold_status"] = "valid" if bm.is_valid else "invalid"

            bm.free()
        except Exception as e:
            logger.error(f"メッシュ品質分析エラー: {e}")
            quality_info["manifold_status"] = "error"

        return quality_info

    def _check_compatibility(self, obj: bpy.types.Object) -> list:
        issues = []

        if len(obj.data.vertices) > 50000:
            issues.append(
                "頂点数が非常に多いです（50,000以上）。パフォーマンスに影響する可能性があります。"
            )

        if not obj.vertex_groups:
            issues.append("頂点グループが存在しません。高精度な衣装生成が困難です。")

        modifiers = [
            mod for mod in obj.modifiers if mod.type in ["MIRROR", "ARRAY", "SOLIDIFY"]
        ]
        if modifiers:
            issues.append(
                f"モディファイア（{', '.join(mod.type for mod in modifiers)}）が適用されています。"
            )

        return issues

    def _report_diagnosis(self, result: Dict[str, Any]) -> None:
        logger.info(f"=== {result['mesh_name']} の包括診断結果 ===")
        logger.info(f"頂点グループ: {len(result['vertex_groups'])}個")
        logger.info(f"ボーン: {len(result['bones'])}個")

        quality = result["mesh_quality"]
        logger.info(
            f"メッシュ品質: 頂点={quality['vertex_count']}, 面={quality['face_count']}"
        )
        logger.info(f"多角形面: {'あり' if quality['has_ngons'] else 'なし'}")
        logger.info(f"孤立頂点: {'あり' if quality['has_loose_vertices'] else 'なし'}")
        logger.info(f"多様体状態: {quality['manifold_status']}")

        if result["hand_groups"]["left"] and result["hand_groups"]["right"]:
            logger.info(
                f"手VG: {result['hand_groups']['left']}, {result['hand_groups']['right']}"
            )
        elif (
            hand_group := result["hand_groups"]["left"]
            or result["hand_groups"]["right"]
        ):
            logger.info(f"片手VGのみ発見: {hand_group}")
        else:
            logger.warning("手の頂点グループが見つかりませんでした")

        if result["mapping_issues"]:
            logger.warning("マッピング問題:")
            for issue in result["mapping_issues"]:
                logger.warning(f" - {issue}")

        if result["compatibility_issues"]:
            logger.warning("互換性問題:")
            for issue in result["compatibility_issues"]:
                logger.warning(f" - {issue}")


class AWGP_OT_ComprehensiveDiagnosis(Operator):
    bl_idname = "awgp.comprehensive_diagnosis"
    bl_label = "Comprehensive Diagnosis"
    bl_description = "包括的なシステム診断を実行"
    bl_options = {"REGISTER"}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        props = context.scene.adaptive_wear_generator_pro

        try:
            logger.info("=== 包括的システム診断開始 ===")

            system_info = self._diagnose_system_compatibility()
            self._report_system_info(system_info)

            if props.base_body:
                mesh_quality = self._diagnose_mesh_quality(props.base_body)
                self._report_mesh_quality(mesh_quality)

            performance_info = self._diagnose_performance_potential()
            self._report_performance_info(performance_info)

            self.report(
                {"INFO"}, "包括的診断完了。詳細はシステムコンソールを確認してください。"
            )
            return {"FINISHED"}

        except Exception as e:
            logger.error(f"包括的診断エラー: {str(e)}")
            self.report({"ERROR"}, f"診断エラー: {str(e)}")
            return {"CANCELLED"}

    def _diagnose_system_compatibility(self) -> Dict[str, Any]:
        import sys
        import platform

        return {
            "blender_version": bpy.app.version_string,
            "python_version": sys.version,
            "platform": platform.platform(),
            "available_memory": "unknown",
            "gpu_info": "unknown",
        }

    def _report_system_info(self, info: Dict[str, Any]) -> None:
        logger.info("=== システム情報 ===")
        logger.info(f"Blender: {info['blender_version']}")
        logger.info(f"Python: {info['python_version']}")
        logger.info(f"プラットフォーム: {info['platform']}")

    def _diagnose_mesh_quality(self, obj: bpy.types.Object) -> Dict[str, Any]:
        return {
            "vertex_count": len(obj.data.vertices),
            "polygon_count": len(obj.data.polygons),
            "material_count": len(obj.data.materials),
            "modifier_count": len(obj.modifiers),
            "vertex_group_count": len(obj.vertex_groups),
            "estimated_processing_time": self._estimate_processing_time(obj),
        }

    def _estimate_processing_time(self, obj: bpy.types.Object) -> float:
        vertex_count = len(obj.data.vertices)
        base_time = vertex_count * 0.0001
        return max(0.5, min(30.0, base_time))

    def _report_mesh_quality(self, quality: Dict[str, Any]) -> None:
        logger.info("=== メッシュ品質情報 ===")
        logger.info(f"頂点数: {quality['vertex_count']}")
        logger.info(f"ポリゴン数: {quality['polygon_count']}")
        logger.info(f"マテリアル数: {quality['material_count']}")
        logger.info(f"モディファイア数: {quality['modifier_count']}")
        logger.info(f"頂点グループ数: {quality['vertex_group_count']}")
        logger.info(f"推定処理時間: {quality['estimated_processing_time']:.1f}秒")

    def _diagnose_performance_potential(self) -> Dict[str, Any]:
        scene_objects = len(bpy.context.scene.objects)

        return {
            "scene_object_count": scene_objects,
            "expected_performance": "良好"
            if scene_objects < 100
            else "注意"
            if scene_objects < 500
            else "低下",
            "optimization_suggestions": self._get_optimization_suggestions(
                scene_objects
            ),
        }

    def _get_optimization_suggestions(self, object_count: int) -> list:
        suggestions = []

        if object_count > 500:
            suggestions.append("シーン内のオブジェクト数を削減することを推奨します")

        if object_count > 100:
            suggestions.append(
                "不要なオブジェクトを別レイヤーに移動することを検討してください"
            )

        suggestions.append("定期的にBlenderファイルを保存してください")

        return suggestions

    def _report_performance_info(self, info: Dict[str, Any]) -> None:
        logger.info("=== パフォーマンス情報 ===")
        logger.info(f"シーンオブジェクト数: {info['scene_object_count']}")
        logger.info(f"予想パフォーマンス: {info['expected_performance']}")

        if info["optimization_suggestions"]:
            logger.info("最適化提案:")
            for suggestion in info["optimization_suggestions"]:
                logger.info(f" - {suggestion}")
