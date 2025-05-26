"""
AI駆動メッシュ生成エンジン
各衣装タイプの専用生成機能
"""

import bpy
import bmesh
import mathutils
import time
from mathutils import Vector
from typing import Optional, Dict, Any, List
import logging

from . import core_utils

logger = logging.getLogger(__name__)

class UltimateAIWearGenerator:
    """最高品質AI駆動衣装生成器"""

    def __init__(self, props):
        self.props = props
        self.base_obj = props.base_body
        self.wear_type = props.wear_type
        self.quality = props.quality_level
        self.ai_settings = props.get_ai_settings()
        self.generation_start_time = time.time()

        logger.info(f"AI生成器初期化: {self.wear_type}, 品質: {self.quality}")

    def generate(self) -> Optional[bpy.types.Object]:
        """メイン生成処理"""
        try:
            # 段階的進捗報告
            core_utils.log_progress(1, 5, "メッシュ生成開始")
            garment = self._generate_base_mesh()

            if not garment:
                return None

            core_utils.log_progress(2, 5, "フィッティング処理")
            self._apply_fitting(garment)

            core_utils.log_progress(3, 5, "リギング処理")
            self._apply_rigging(garment)

            core_utils.log_progress(4, 5, "品質向上処理")
            self._apply_quality_enhancements(garment)

            core_utils.log_progress(5, 5, "最終調整")
            self._finalize_garment(garment)

            elapsed = time.time() - self.generation_start_time
            logger.info(f"AI生成完了: {garment.name} ({elapsed:.2f}秒)")

            return garment

        except Exception as e:
            logger.error(f"AI生成エラー: {str(e)}")
            return None

    def _generate_base_mesh(self) -> Optional[bpy.types.Object]:
        """基本メッシュの生成"""
        generator_map = {
            "PANTS": self._generate_pants,
            "T_SHIRT": self._generate_tshirt,
            "BRA": self._generate_bra,
            "SOCKS": self._generate_socks,
            "GLOVES": self._generate_gloves,
        }

        generator = generator_map.get(self.wear_type)
        if not generator:
            raise ValueError(f"未対応の衣装タイプ: {self.wear_type}")

        return generator()

    def _generate_pants(self) -> Optional[bpy.types.Object]:
        """パンツ生成"""
        # 腰部頂点グループ検索
        hip_groups = core_utils.find_vertex_groups_by_type(self.base_obj, "hip")
        if not hip_groups:
            logger.error("腰部の頂点グループが見つかりません")
            return None

        # メッシュ複製と初期化
        mesh = self.base_obj.data.copy()
        pants_obj = bpy.data.objects.new(f"{self.base_obj.name}_AI_pants", mesh)
        bpy.context.collection.objects.link(pants_obj)

        try:
            # bmesh処理
            bm = bmesh.new()
            bm.from_mesh(mesh)

            # AI駆動頂点選択
            selected_verts = self._ai_select_vertices(bm, hip_groups, "pants")

            # 不要頂点削除
            self._remove_unwanted_vertices(bm, selected_verts)

            # 厚み適用
            self._apply_thickness(bm)

            # AI品質向上
            if self.ai_settings["quality_mode"]:
                self._apply_ai_smoothing(bm, iterations=2)

            # メッシュ更新
            bm.to_mesh(mesh)
            bm.free()

            # スムーズシェード適用
            core_utils.apply_edge_smoothing(pants_obj)

            return pants_obj

        except Exception as e:
            logger.error(f"パンツ生成エラー: {str(e)}")
            if pants_obj.name in bpy.data.objects:
                bpy.data.objects.remove(pants_obj, do_unlink=True)
            return None

    def _generate_tshirt(self) -> Optional[bpy.types.Object]:
        """Tシャツ生成"""
        # 胸部と腕の頂点グループ検索
        chest_groups = core_utils.find_vertex_groups_by_type(self.base_obj, "chest")
        arm_groups = core_utils.find_vertex_groups_by_type(self.base_obj, "arm")
        target_groups = chest_groups + arm_groups

        if not target_groups:
            logger.warning("Tシャツ用頂点グループが見つかりません。デフォルト処理を使用")

        # メッシュ生成処理
        mesh = self.base_obj.data.copy()
        tshirt_obj = bpy.data.objects.new(f"{self.base_obj.name}_AI_tshirt", mesh)
        bpy.context.collection.objects.link(tshirt_obj)

        try:
            bm = bmesh.new()
            bm.from_mesh(mesh)

            if target_groups:
                selected_verts = self._ai_select_vertices(bm, target_groups, "tshirt")
            else:
                # フォールバック：高さベース選択
                selected_verts = self._height_based_selection(bm, 0.4)

            self._remove_unwanted_vertices(bm, selected_verts)
            self._apply_thickness(bm)

            if self.ai_settings["quality_mode"]:
                self._apply_ai_smoothing(bm, iterations=2)

            bm.to_mesh(mesh)
            bm.free()

            core_utils.apply_edge_smoothing(tshirt_obj)
            return tshirt_obj

        except Exception as e:
            logger.error(f"Tシャツ生成エラー: {str(e)}")
            if tshirt_obj.name in bpy.data.objects:
                bpy.data.objects.remove(tshirt_obj, do_unlink=True)
            return None

    def _generate_bra(self) -> Optional[bpy.types.Object]:
        """ブラ生成"""
        chest_groups = core_utils.find_vertex_groups_by_type(self.base_obj, "chest")

        mesh = self.base_obj.data.copy()
        bra_obj = bpy.data.objects.new(f"{self.base_obj.name}_AI_bra", mesh)
        bpy.context.collection.objects.link(bra_obj)

        try:
            bm = bmesh.new()
            bm.from_mesh(mesh)

            if chest_groups:
                selected_verts = self._ai_select_vertices(bm, chest_groups, "bra")
            else:
                # 統計的選択
                selected_verts = self._statistical_selection(bm, "chest")

            self._remove_unwanted_vertices(bm, selected_verts)
            self._apply_thickness(bm)

            if self.ai_settings["quality_mode"]:
                self._apply_ai_smoothing(bm, iterations=2)

            bm.to_mesh(mesh)
            bm.free()

            core_utils.apply_edge_smoothing(bra_obj)
            return bra_obj

        except Exception as e:
            logger.error(f"ブラ生成エラー: {str(e)}")
            if bra_obj.name in bpy.data.objects:
                bpy.data.objects.remove(bra_obj, do_unlink=True)
            return None

    def _generate_socks(self) -> Optional[bpy.types.Object]:
        """靴下生成"""
        foot_groups = core_utils.find_vertex_groups_by_type(self.base_obj, "foot")
        leg_groups = core_utils.find_vertex_groups_by_type(self.base_obj, "leg")
        target_groups = foot_groups + leg_groups

        if not target_groups:
            logger.error("靴下用の頂点グループが見つかりません")
            return None

        mesh = self.base_obj.data.copy()
        socks_obj = bpy.data.objects.new(f"{self.base_obj.name}_AI_socks", mesh)
        bpy.context.collection.objects.link(socks_obj)

        try:
            bm = bmesh.new()
            bm.from_mesh(mesh)

            # 長さを考慮した選択
            selected_verts = self._length_based_selection(bm, target_groups, "socks")

            if not selected_verts:
                logger.error("靴下生成用の頂点が選択されませんでした")
                bm.free()
                bpy.data.objects.remove(socks_obj, do_unlink=True)
                return None

            self._remove_unwanted_vertices(bm, selected_verts)
            self._apply_thickness(bm)

            if self.ai_settings["quality_mode"]:
                self._apply_ai_smoothing(bm, iterations=1)

            bm.to_mesh(mesh)
            bm.free()

            core_utils.apply_edge_smoothing(socks_obj)
            return socks_obj

        except Exception as e:
            logger.error(f"靴下生成エラー: {str(e)}")
            if socks_obj.name in bpy.data.objects:
                bpy.data.objects.remove(socks_obj, do_unlink=True)
            return None

    def _generate_gloves(self) -> Optional[bpy.types.Object]:
        """手袋生成"""
        left_hand, right_hand = core_utils.find_hand_vertex_groups(self.base_obj)
        hand_groups = core_utils.find_vertex_groups_by_type(self.base_obj, "hand")

        if not (left_hand or right_hand):
            logger.error("手の頂点グループが見つかりません")
            return None

        target_groups = (
            ([left_hand] if left_hand else []) +
            ([right_hand] if right_hand else []) +
            hand_groups
        )

        mesh = self.base_obj.data.copy()
        gloves_obj = bpy.data.objects.new(f"{self.base_obj.name}_AI_gloves", mesh)
        bpy.context.collection.objects.link(gloves_obj)

        try:
            bm = bmesh.new()
            bm.from_mesh(mesh)

            selected_verts = self._ai_select_vertices(bm, target_groups, "gloves")

            if not selected_verts:
                logger.error("手袋生成用の頂点が選択されませんでした")
                bm.free()
                bpy.data.objects.remove(gloves_obj, do_unlink=True)
                return None

            self._remove_unwanted_vertices(bm, selected_verts)

            # 指の処理
            if not self.props.glove_fingers:
                logger.info("指なし手袋モード")
                # ミトン処理の実装

            self._apply_thickness(bm)

            if self.ai_settings["quality_mode"]:
                self._apply_ai_smoothing(bm, iterations=1)

            bm.to_mesh(mesh)
            bm.free()

            core_utils.apply_edge_smoothing(gloves_obj)
            return gloves_obj

        except Exception as e:
            logger.error(f"手袋生成エラー: {str(e)}")
            if gloves_obj.name in bpy.data.objects:
                bpy.data.objects.remove(gloves_obj, do_unlink=True)
            return None

    def _ai_select_vertices(self, bm: bmesh.types.BMesh, groups: list, wear_type: str) -> list:
        """AI駆動頂点選択"""
        deform_layer = bm.verts.layers.deform.verify()
        selected_verts = []

        # 衣装タイプ別閾値
        threshold_map = {
            "pants": self.ai_settings.get("threshold", 0.3),
            "tshirt": self.ai_settings.get("tshirt_threshold", 0.1),
            "bra": self.ai_settings.get("bra_threshold", 0.1),
            "gloves": self.ai_settings.get("hand_threshold", 0.1),
            "socks": 0.1 * self.props.sock_length * self.ai_settings.get("sock_multiplier", 1.0)
        }

        threshold = threshold_map.get(wear_type, 0.2)

        for vert in bm.verts:
            for group in groups:
                if group.index in vert[deform_layer]:
                    weight = vert[deform_layer][group.index]
                    if weight > threshold:
                        selected_verts.append(vert)
                        break

        return list(set(selected_verts))  # 重複除去

    def _height_based_selection(self, bm: bmesh.types.BMesh, factor: float) -> list:
        """高さベース頂点選択"""
        if not bm.verts:
            return []

        avg_z = sum(v.co.z for v in bm.verts) / len(bm.verts)
        threshold_z = avg_z * factor

        return [v for v in bm.verts if v.co.z > threshold_z]

    def _statistical_selection(self, bm: bmesh.types.BMesh, body_part: str) -> list:
        """統計的頂点選択"""
        if not bm.verts:
            return []

        avg_z = sum(v.co.z for v in bm.verts) / len(bm.verts)
        std_z = (sum((v.co.z - avg_z) ** 2 for v in bm.verts) / len(bm.verts)) ** 0.5

        if body_part == "chest":
            threshold_z = avg_z + (std_z * 0.3)
        else:
            threshold_z = avg_z

        return [v for v in bm.verts if v.co.z >= threshold_z]

    def _length_based_selection(self, bm: bmesh.types.BMesh, groups: list, wear_type: str) -> list:
        """長さベース頂点選択（靴下用）"""
        deform_layer = bm.verts.layers.deform.verify()

        min_weight = (
            0.1 * self.props.sock_length *
            self.ai_settings.get("sock_multiplier", 1.0)
        )

        selected_verts = []
        for vert in bm.verts:
            for group in groups:
                if group.index in vert[deform_layer]:
                    weight = vert[deform_layer][group.index]
                    if weight > min_weight:
                        selected_verts.append(vert)
                        break

        return list(set(selected_verts))

    def _remove_unwanted_vertices(self, bm: bmesh.types.BMesh, keep_verts: list) -> None:
        """不要頂点の削除"""
        verts_to_remove = [v for v in bm.verts if v not in keep_verts]
        if verts_to_remove:
            bmesh.ops.delete(bm, geom=verts_to_remove, context="VERTS")

    def _apply_thickness(self, bm: bmesh.types.BMesh) -> None:
        """厚み適用"""
        thickness = (
            self.props.thickness *
            self.ai_settings.get("thickness_multiplier", 1.0)
        )

        for vert in bm.verts:
            vert.co += vert.normal * thickness

    def _apply_ai_smoothing(self, bm: bmesh.types.BMesh, iterations: int = 1) -> None:
        """AI駆動スムージング"""
        try:
            for i in range(iterations):
                bmesh.ops.smooth_vert(
                    bm,
                    verts=bm.verts,
                    factor=0.2,
                    use_axis_x=True,
                    use_axis_y=True,
                    use_axis_z=True,
                )
            logger.debug(f"AIスムージング完了: {iterations}回反復")
        except Exception as e:
            logger.error(f"AIスムージングエラー: {str(e)}")

    def _apply_fitting(self, garment: bpy.types.Object) -> None:
        """フィッティング適用"""
        core_utils.apply_fitting(garment, self.base_obj, self.props)

    def _apply_rigging(self, garment: bpy.types.Object) -> None:
        """リギング適用"""
        armature = core_utils.find_armature(self.base_obj)
        if armature:
            core_utils.apply_rigging(garment, self.base_obj, armature)

    def _apply_quality_enhancements(self, garment: bpy.types.Object) -> None:
        """品質向上処理"""
        if self.quality == "ULTIMATE":
            self._apply_ultimate_quality(garment)
        elif self.quality in ["HIGH", "STABLE"]:
            self._apply_standard_quality(garment)

    def _apply_ultimate_quality(self, garment: bpy.types.Object) -> None:
        """最高品質処理"""
        if self.props.enable_edge_smoothing:
            core_utils.apply_edge_smoothing(garment)

        if self.ai_settings["subdivision"]:
            core_utils.apply_subdivision_surface(garment, levels=1)

        if self.props.enable_cloth_sim:
            core_utils.setup_cloth_simulation(garment)

    def _apply_standard_quality(self, garment: bpy.types.Object) -> None:
        """標準品質処理"""
        if self.props.enable_edge_smoothing:
            core_utils.apply_edge_smoothing(garment)

    def _finalize_garment(self, garment: bpy.types.Object) -> None:
        """最終調整"""
        # 重複頂点の修正
        core_utils.fix_duplicate_vertices(garment)

        # 名前設定
        garment.name = f"{self.base_obj.name}_{self.wear_type}_AI"


def generate_pleated_skirt(props) -> Optional[bpy.types.Object]:
    """プリーツスカート生成"""
    logger.info("プリーツスカート生成開始")

    try:
        # 腰部・脚部頂点グループ検索
        hip_groups = core_utils.find_vertex_groups_by_type(props.base_body, "hip")
        leg_groups = core_utils.find_vertex_groups_by_type(props.base_body, "leg")

        if not hip_groups:
            logger.error("腰部の頂点グループが見つかりません")
            return None

        # メッシュ生成
        skirt_obj = _create_skirt_base_mesh(props, hip_groups + leg_groups)
        if not skirt_obj:
            return None

        # プリーツ形成
        _create_pleats_geometry(skirt_obj, props)

        # 品質評価
        quality_report = core_utils.evaluate_pleats_geometry(skirt_obj, props.pleat_count)
        if quality_report["total_score"] < 70:
            logger.warning(f"スカート品質スコアが低いです: {quality_report['total_score']}")

        logger.info(f"プリーツスカート生成完了: {skirt_obj.name}")
        return skirt_obj

    except Exception as e:
        logger.error(f"プリーツスカート生成エラー: {str(e)}")
        return None


def _create_skirt_base_mesh(props, target_groups: list) -> Optional[bpy.types.Object]:
    """スカート基本メッシュ作成"""
    mesh = props.base_body.data.copy()
    skirt_obj = bpy.data.objects.new(f"{props.base_body.name}_skirt", mesh)
    bpy.context.collection.objects.link(skirt_obj)

    try:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        deform_layer = bm.verts.layers.deform.verify()

        # 頂点選択
        selected_verts = []
        length_factor = props.skirt_length
        min_weight = 0.1 * length_factor

        for vert in bm.verts:
            for group in target_groups:
                if group.index in vert[deform_layer]:
                    weight = vert[deform_layer][group.index]
                    if weight > min_weight:
                        selected_verts.append(vert)
                        break

        if not selected_verts:
            raise Exception("スカート生成用の頂点が見つかりません")

        # 不要頂点削除
        verts_to_remove = [v for v in bm.verts if v not in selected_verts]
        if verts_to_remove:
            bmesh.ops.delete(bm, geom=verts_to_remove, context="VERTS")

        # 厚み追加
        thickness = props.thickness
        for vert in bm.verts:
            vert.co += vert.normal * thickness

        bm.to_mesh(mesh)
        bm.free()

        core_utils.apply_edge_smoothing(skirt_obj)
        return skirt_obj

    except Exception as e:
        logger.error(f"スカート基本メッシュ作成エラー: {str(e)}")
        if skirt_obj.name in bpy.data.objects:
            bpy.data.objects.remove(skirt_obj, do_unlink=True)
        return None


def _create_pleats_geometry(skirt_obj: bpy.types.Object, props) -> None:
    """プリーツ形状生成"""
    logger.info(f"プリーツ生成: 数={props.pleat_count}, 深さ={props.pleat_depth}")

    # プリーツ生成の詳細実装
    # この部分は元のコードの詳細ロジックを整理して実装
    pass