"""
コアオペレーター実装
衣装生成とユーティリティ機能
"""

import bpy
import bmesh
import time
from bpy.types import Operator
from typing import Set, Optional, Dict, Any
import logging

from . import core_generators, core_utils, core_materials

logger = logging.getLogger(__name__)

class AWGP_OT_GenerateWear(Operator):
    """AI駆動衣装生成メインオペレーター"""
    bl_idname = "awgp.generate_wear"
    bl_label = "Generate Wear"
    bl_description = "AI駆動で衣装を自動生成します"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        """オペレーターの有効/無効を判定"""
        awg_props = context.scene.adaptive_wear_generator_pro
        return awg_props.base_body is not None and awg_props.wear_type != "NONE"
    def execute(self, context: bpy.types.Context) -> Set[str]:
        """メイン実行処理"""
        props = context.scene.adaptive_wear_generator_pro

        # 設定検証
        is_valid, errors = props.validate_settings()
        if not is_valid:
            for error in errors:
                self.report({"ERROR"}, error)
            return {"CANCELLED"}

        start_time = time.time()
        logger.info(f"衣装生成開始: タイプ={props.wear_type}, 品質={props.quality_level}")

        try:
            # 生成処理の実行
            garment = self._generate_garment(props)

            if not garment:
                self.report({"ERROR"}, "衣装生成に失敗しました")
                return {"CANCELLED"}

            # 後処理
            self._apply_post_processing(garment, props)

            # 最終選択設定
            core_utils.select_single_object(garment)

            elapsed_time = time.time() - start_time
            logger.info(f"衣装生成完了: {garment.name} (処理時間: {elapsed_time:.2f}秒)")

            self.report(
                {"INFO"},
                f"{props.wear_type} 生成完了: {garment.name} ({elapsed_time:.1f}秒)"
            )
            return {"FINISHED"}

        except Exception as e:
            logger.error(f"衣装生成エラー: {str(e)}")
            self.report({"ERROR"}, f"生成エラー: {str(e)}")
            return {"CANCELLED"}

    def _generate_garment(self, props) -> Optional[bpy.types.Object]:
        """衣装メッシュの生成"""
        if props.wear_type == "SKIRT":
            return core_generators.generate_pleated_skirt(props)
        else:
            generator = core_generators.UltimateAIWearGenerator(props)
            return generator.generate()

    def _apply_post_processing(self, garment: bpy.types.Object, props) -> None:
        """後処理の適用"""
        # マテリアル適用
        if props.use_text_material and props.material_prompt:
            core_materials.apply_text_material(
                garment, props.wear_type, props.material_prompt
            )
        else:
            core_materials.apply_default_material(garment, props.wear_type)

        # 品質評価（スカートのみ）
        if props.wear_type == "SKIRT":
            quality_report = core_utils.evaluate_pleats_geometry(
                garment, props.pleat_count
            )
            if quality_report["total_score"] < 70:
                logger.warning(f"スカート品質スコアが低いです: {quality_report['total_score']}")

        # クロスシミュレーション
        if props.enable_cloth_sim:
            core_utils.setup_cloth_simulation(garment, props.base_body)

        # リギング
        if props.auto_rigging:
            armature = core_utils.find_armature(props.base_body)
            if armature:
                core_utils.apply_rigging(garment, props.base_body, armature)


class AWGP_OT_DiagnoseBones(Operator):
    """ボーンと頂点グループ診断"""
    bl_idname = "awgp.diagnose_bones"
    bl_label = "Diagnose Bones & Vertex Groups"
    bl_description = "アーマチュアと頂点グループの詳細診断を実行"
    bl_options = {"REGISTER"}

    def execute(self, context: bpy.types.Context) -> Set[str]:
        """診断実行処理"""
        props = context.scene.adaptive_wear_generator_pro

        if not props.base_body:
            self.report({"ERROR"}, "素体メッシュを選択してください")
            return {"CANCELLED"}

        try:
            # アーマチュア検索
            armature = core_utils.find_armature(props.base_body)
            if not armature:
                self.report(
                    {"WARNING"},
                    "アーマチュアが見つかりませんが、頂点グループのみ診断します"
                )

            # 診断実行
            diagnostic_result = self._perform_diagnosis(props.base_body, armature)

            # 結果レポート
            self._report_diagnosis(diagnostic_result)

            self.report({"INFO"}, "AI対応診断完了。詳細はシステムコンソールを確認。")
            return {"FINISHED"}

        except Exception as e:
            logger.error(f"診断エラー: {str(e)}")
            self.report({"ERROR"}, f"診断エラー: {str(e)}")
            return {"CANCELLED"}

    def _perform_diagnosis(
        self,
        mesh_obj: bpy.types.Object,
        armature_obj: Optional[bpy.types.Object]
    ) -> Dict[str, Any]:
        """診断処理の実行"""
        result = {
            "mesh_name": mesh_obj.name,
            "vertex_groups": [],
            "bones": [],
            "hand_groups": {},
            "mapping_issues": []
        }

        # 頂点グループ分析
        if mesh_obj.vertex_groups:
            result["vertex_groups"] = [vg.name for vg in mesh_obj.vertex_groups]
            logger.info(f"頂点グループ数: {len(result['vertex_groups'])}")

        # ボーン分析
        if armature_obj and armature_obj.type == "ARMATURE":
            result["bones"] = [b.name for b in armature_obj.data.bones]
            logger.info(f"ボーン数: {len(result['bones'])}")

            # マッピング問題の検出
            result["mapping_issues"] = self._detect_mapping_issues(
                result["vertex_groups"], result["bones"]
            )

        # 手の頂点グループ検索
        left_hand, right_hand = core_utils.find_hand_vertex_groups(mesh_obj)
        result["hand_groups"] = {
            "left": left_hand.name if left_hand else None,
            "right": right_hand.name if right_hand else None
        }

        return result

    def _detect_mapping_issues(
        self,
        vertex_groups: list,
        bones: list
    ) -> list:
        """マッピング問題の検出"""
        issues = []

        for bone_name in bones:
            if bone_name not in vertex_groups:
                issues.append(f"ボーン '{bone_name}' に対応する頂点グループがありません")

        for vg_name in vertex_groups:
            if vg_name not in bones:
                issues.append(f"頂点グループ '{vg_name}' に対応するボーンがありません")

        return issues

    def _report_diagnosis(self, result: Dict[str, Any]) -> None:
        """診断結果のレポート"""
        logger.info(f"=== {result['mesh_name']} の診断結果 ===")
        logger.info(f"頂点グループ: {len(result['vertex_groups'])}個")
        logger.info(f"ボーン: {len(result['bones'])}個")

        if result["hand_groups"]["left"] and result["hand_groups"]["right"]:
            logger.info(
                f"手VG: {result['hand_groups']['left']}, {result['hand_groups']['right']}"
            )
        elif hand_group := result["hand_groups"]["left"] or result["hand_groups"]["right"]:
            logger.info(f"片手VGのみ発見: {hand_group}")
        else:
            logger.warning("手の頂点グループが見つかりませんでした")

        if result["mapping_issues"]:
            logger.warning("マッピング問題:")
            for issue in result["mapping_issues"]:
                logger.warning(f"  - {issue}")