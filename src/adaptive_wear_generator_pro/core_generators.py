import bpy
import bmesh
import mathutils
import math
import numpy as np
import time
from mathutils import Vector, Matrix
from typing import Optional, Dict, Any, List, Tuple
import logging
from . import core_utils

logger = logging.getLogger(__name__)


class AWGProException(Exception):
    pass


class MeshValidationError(AWGProException):
    pass


class VertexGroupError(AWGProException):
    pass


class GeometryQualityValidator:
    """組み込み幾何学品質検証システム"""

    def __init__(self):
        self.tolerance = 1e-6
        self.quality_thresholds = {
            "minimum_face_area": 1e-8,
            "maximum_aspect_ratio": 15.0,
            "minimum_edge_length": 1e-6,
            "maximum_edge_length": 10.0,
            "manifold_score_threshold": 80.0,
            "degenerate_face_ratio_threshold": 0.05,
        }

    def validate_mesh_comprehensive(
        self, obj: bpy.types.Object, context: str = ""
    ) -> Dict[str, Any]:
        """包括的メッシュ検証"""
        if not obj or obj.type != "MESH":
            return {"valid": False, "error": "Invalid mesh object", "score": 0.0}

        start_time = time.time()
        mesh = obj.data

        logger.info(
            f"🔍 Starting comprehensive mesh validation for {obj.name} {context}"
        )

        # 基本統計の収集
        basic_stats = self._collect_basic_statistics(mesh)
        logger.info(
            f"📊 Basic stats: {basic_stats['vertex_count']}v, {basic_stats['face_count']}f, {basic_stats['edge_count']}e"
        )

        # トポロジー検証
        topology_result = self._validate_topology(mesh)
        logger.info(
            f"🔗 Topology: Euler={topology_result['euler_characteristic']}, Manifold={topology_result['is_manifold']}"
        )

        # 幾何学的品質検証
        geometry_result = self._validate_geometry_quality(mesh)
        logger.info(
            f"📐 Geometry: Score={geometry_result['quality_score']:.1f}, Degenerate={len(geometry_result['degenerate_faces'])}"
        )

        # 面積・体積検証
        volume_result = self._validate_volume_properties(mesh)
        logger.info(
            f"📏 Volume: Surface={volume_result['surface_area']:.4f}, Volume={volume_result['volume']:.4f}"
        )

        # 総合評価
        overall_score = self._calculate_overall_quality_score(
            topology_result, geometry_result, volume_result
        )

        validation_time = time.time() - start_time

        result = {
            "valid": overall_score
            >= self.quality_thresholds["manifold_score_threshold"],
            "overall_score": overall_score,
            "basic_stats": basic_stats,
            "topology": topology_result,
            "geometry": geometry_result,
            "volume": volume_result,
            "validation_time": validation_time,
            "issues": self._compile_issues(topology_result, geometry_result),
            "recommendations": [],
        }

        result["recommendations"] = self._generate_quality_recommendations(result)

        # 結果サマリーログ
        status = "✅ PASSED" if result["valid"] else "❌ FAILED"
        logger.info(
            f"🎯 Validation {status}: Score={overall_score:.1f}/100 in {validation_time:.3f}s"
        )

        if not result["valid"]:
            logger.warning(f"⚠️  Quality issues detected for {obj.name}:")
            for issue in result["issues"]:
                logger.warning(f"   - {issue}")

        return result

    def _collect_basic_statistics(self, mesh: bpy.types.Mesh) -> Dict[str, int]:
        """基本統計の収集"""
        return {
            "vertex_count": len(mesh.vertices),
            "face_count": len(mesh.polygons),
            "edge_count": len(mesh.edges),
            "material_count": len(mesh.materials),
        }

    def _validate_topology(self, mesh: bpy.types.Mesh) -> Dict[str, Any]:
        """トポロジー検証"""
        V = len(mesh.vertices)
        E = len(mesh.edges)
        F = len(mesh.polygons)

        euler_characteristic = V - E + F

        # エッジ-面の関係性チェック
        edge_face_count = {}
        for poly in mesh.polygons:
            for i in range(len(poly.vertices)):
                j = (i + 1) % len(poly.vertices)
                edge = tuple(sorted([poly.vertices[i], poly.vertices[j]]))
                edge_face_count[edge] = edge_face_count.get(edge, 0) + 1

        # 多様体性チェック
        is_manifold = all(count <= 2 for count in edge_face_count.values())
        boundary_edges = [edge for edge, count in edge_face_count.items() if count == 1]
        non_manifold_edges = [
            edge for edge, count in edge_face_count.items() if count > 2
        ]

        return {
            "euler_characteristic": euler_characteristic,
            "is_manifold": is_manifold,
            "is_closed": len(boundary_edges) == 0,
            "boundary_edge_count": len(boundary_edges),
            "non_manifold_edge_count": len(non_manifold_edges),
            "genus": max(0, (2 - euler_characteristic) // 2)
            if len(boundary_edges) == 0
            else None,
        }

    def _validate_geometry_quality(self, mesh: bpy.types.Mesh) -> Dict[str, Any]:
        """幾何学的品質検証"""
        degenerate_faces = []
        high_aspect_faces = []
        face_areas = []
        edge_lengths = []
        aspect_ratios = []

        # 面の品質チェック
        for i, poly in enumerate(mesh.polygons):
            area = poly.area
            face_areas.append(area)

            if area < self.quality_thresholds["minimum_face_area"]:
                degenerate_faces.append(i)

            # アスペクト比計算
            aspect_ratio = self._calculate_face_aspect_ratio(poly, mesh.vertices)
            aspect_ratios.append(aspect_ratio)

            if aspect_ratio > self.quality_thresholds["maximum_aspect_ratio"]:
                high_aspect_faces.append(i)

        # エッジの品質チェック
        for edge in mesh.edges:
            length = self._calculate_edge_length(edge, mesh.vertices)
            edge_lengths.append(length)

        # 品質スコア計算
        quality_score = 100.0

        degenerate_ratio = len(degenerate_faces) / max(len(mesh.polygons), 1)
        if (
            degenerate_ratio
            > self.quality_thresholds["degenerate_face_ratio_threshold"]
        ):
            quality_score -= 40.0 * (
                degenerate_ratio
                / self.quality_thresholds["degenerate_face_ratio_threshold"]
            )

        if high_aspect_faces:
            quality_score -= min(len(high_aspect_faces) * 2, 30.0)

        return {
            "quality_score": max(0.0, quality_score),
            "degenerate_faces": degenerate_faces,
            "high_aspect_faces": high_aspect_faces,
            "face_area_stats": self._calculate_array_stats(face_areas),
            "edge_length_stats": self._calculate_array_stats(edge_lengths),
            "aspect_ratio_stats": self._calculate_array_stats(aspect_ratios),
        }

    def _validate_volume_properties(self, mesh: bpy.types.Mesh) -> Dict[str, float]:
        """体積・表面積の検証"""
        try:
            # bmeshを使用した正確な計算
            bm = bmesh.new()
            bm.from_mesh(mesh)

            # 法線の確認と修正
            bm.normal_update()
            bm.faces.ensure_lookup_table()

            # 体積計算
            volume = 0.0
            if len(bm.faces) > 0:
                try:
                    volume = bm.calc_volume()
                except:
                    volume = 0.0

            # 表面積計算
            surface_area = sum(face.calc_area() for face in bm.faces)

            bm.free()

            return {
                "volume": abs(volume),  # 絶対値を取る
                "surface_area": surface_area,
                "volume_valid": volume != 0.0,
            }
        except Exception as e:
            logger.warning(f"Volume calculation failed: {e}")
            return {"volume": 0.0, "surface_area": 0.0, "volume_valid": False}

    def _calculate_face_aspect_ratio(
        self, poly: bpy.types.MeshPolygon, vertices: bpy.types.MeshVertices
    ) -> float:
        """面のアスペクト比計算"""
        if len(poly.vertices) < 3:
            return float("inf")

        edge_lengths = []
        for i in range(len(poly.vertices)):
            j = (i + 1) % len(poly.vertices)
            v1 = vertices[poly.vertices[i]].co
            v2 = vertices[poly.vertices[j]].co
            edge_lengths.append((v1 - v2).length)

        if min(edge_lengths) == 0:
            return float("inf")

        return max(edge_lengths) / min(edge_lengths)

    def _calculate_edge_length(
        self, edge: bpy.types.MeshEdge, vertices: bpy.types.MeshVertices
    ) -> float:
        """エッジ長計算"""
        v1 = vertices[edge.vertices[0]].co
        v2 = vertices[edge.vertices[1]].co
        return (v1 - v2).length

    def _calculate_array_stats(self, array: List[float]) -> Dict[str, float]:
        """配列統計計算"""
        if not array:
            return {"mean": 0, "std": 0, "min": 0, "max": 0, "median": 0}

        arr = np.array(array)
        return {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "min": float(np.min(arr)),
            "max": float(np.max(arr)),
            "median": float(np.median(arr)),
        }

    def _calculate_overall_quality_score(
        self, topology: Dict, geometry: Dict, volume: Dict
    ) -> float:
        """総合品質スコア計算"""
        score = 100.0

        # トポロジースコア（40%の重み）
        if not topology["is_manifold"]:
            score -= 30.0

        if topology["non_manifold_edge_count"] > 0:
            score -= min(topology["non_manifold_edge_count"] * 5, 20.0)

        # 幾何学スコア（40%の重み）
        geometry_penalty = 100.0 - geometry["quality_score"]
        score -= geometry_penalty * 0.4

        # 体積スコア（20%の重み）
        if not volume["volume_valid"]:
            score -= 15.0

        return max(0.0, score)

    def _compile_issues(self, topology: Dict, geometry: Dict) -> List[str]:
        """問題点のコンパイル"""
        issues = []

        if not topology["is_manifold"]:
            issues.append("Non-manifold geometry detected")

        if topology["non_manifold_edge_count"] > 0:
            issues.append(
                f"{topology['non_manifold_edge_count']} non-manifold edges found"
            )

        if geometry["degenerate_faces"]:
            issues.append(
                f"{len(geometry['degenerate_faces'])} degenerate faces detected"
            )

        if geometry["high_aspect_faces"]:
            issues.append(
                f"{len(geometry['high_aspect_faces'])} faces with high aspect ratio"
            )

        return issues

    def _generate_quality_recommendations(self, result: Dict) -> List[str]:
        """品質改善提案"""
        recommendations = []

        if result["overall_score"] < 70:
            recommendations.append("Consider using higher quality generation settings")

        if not result["topology"]["is_manifold"]:
            recommendations.append("Run mesh cleanup to fix manifold issues")

        if result["geometry"]["degenerate_faces"]:
            recommendations.append("Remove degenerate faces using mesh cleanup tools")

        if result["volume"]["volume"] == 0:
            recommendations.append("Check mesh closure and face orientations")

        return recommendations


class VisualValidationLogger:
    """見た目検証とログ出力システム"""

    def __init__(self):
        self.validation_history = []

    def validate_visual_appearance(
        self,
        original_obj: bpy.types.Object,
        generated_obj: bpy.types.Object,
        wear_type: str,
        generation_params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """見た目の妥当性検証"""
        logger.info(f"👁️  Starting visual validation for {wear_type} generation")

        # 基本的な視覚検証
        size_validation = self._validate_size_relationship(
            original_obj, generated_obj, generation_params
        )
        coverage_validation = self._validate_coverage_area(
            original_obj, generated_obj, wear_type
        )
        shape_validation = self._validate_shape_integrity(generated_obj, wear_type)

        # 衣装タイプ別の特別検証
        type_specific_validation = self._validate_wear_type_specific(
            generated_obj, wear_type, generation_params
        )

        # 総合判定
        overall_valid = (
            size_validation["valid"]
            and coverage_validation["valid"]
            and shape_validation["valid"]
            and type_specific_validation["valid"]
        )

        result = {
            "overall_valid": overall_valid,
            "wear_type": wear_type,
            "size_validation": size_validation,
            "coverage_validation": coverage_validation,
            "shape_validation": shape_validation,
            "type_specific_validation": type_specific_validation,
            "visual_score": self._calculate_visual_score(
                size_validation,
                coverage_validation,
                shape_validation,
                type_specific_validation,
            ),
        }

        # 詳細ログ出力
        self._log_visual_validation_results(result)

        self.validation_history.append(result)
        return result

    def _validate_size_relationship(
        self,
        original: bpy.types.Object,
        generated: bpy.types.Object,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """サイズ関係の検証"""
        orig_bounds = self._get_object_bounds(original)
        gen_bounds = self._get_object_bounds(generated)

        expected_thickness = params.get("thickness", 0.01)

        # サイズ変化の測定
        size_change = {
            "x": gen_bounds["size"][0] - orig_bounds["size"][0],
            "y": gen_bounds["size"][1] - orig_bounds["size"][1],
            "z": gen_bounds["size"][2] - orig_bounds["size"][2],
        }

        # 期待値との比較
        avg_size_change = (
            abs(size_change["x"]) + abs(size_change["y"]) + abs(size_change["z"])
        ) / 3
        size_accuracy = 1.0 - abs(avg_size_change - expected_thickness) / max(
            expected_thickness, 0.001
        )
        size_accuracy = max(0.0, min(1.0, size_accuracy))

        is_valid = size_accuracy > 0.7  # 70%以上の精度を要求

        return {
            "valid": is_valid,
            "size_accuracy": size_accuracy,
            "size_change": size_change,
            "expected_thickness": expected_thickness,
            "actual_avg_change": avg_size_change,
        }

    def _validate_coverage_area(
        self, original: bpy.types.Object, generated: bpy.types.Object, wear_type: str
    ) -> Dict[str, Any]:
        """カバレッジ領域の検証"""
        # 期待されるカバレッジ比率（衣装タイプ別）
        expected_coverage = {
            "T_SHIRT": 0.4,  # 上半身の40%
            "PANTS": 0.3,  # 下半身の30%
            "BRA": 0.1,  # 胸部の10%
            "SOCKS": 0.05,  # 足の5%
            "GLOVES": 0.02,  # 手の2%
            "SKIRT": 0.2,  # 腰回りの20%
        }

        orig_surface_area = self._calculate_surface_area(original)
        gen_surface_area = self._calculate_surface_area(generated)

        coverage_ratio = gen_surface_area / max(orig_surface_area, 0.001)
        expected_ratio = expected_coverage.get(wear_type, 0.2)

        # カバレッジの妥当性チェック
        coverage_valid = 0.5 * expected_ratio <= coverage_ratio <= 2.0 * expected_ratio

        return {
            "valid": coverage_valid,
            "coverage_ratio": coverage_ratio,
            "expected_ratio": expected_ratio,
            "original_surface_area": orig_surface_area,
            "generated_surface_area": gen_surface_area,
        }

    def _validate_shape_integrity(
        self, obj: bpy.types.Object, wear_type: str
    ) -> Dict[str, Any]:
        """形状の整合性検証"""
        mesh = obj.data

        # 基本的な形状チェック
        has_holes = self._detect_holes(mesh)
        has_strange_protrusions = self._detect_protrusions(mesh)
        shape_smoothness = self._calculate_shape_smoothness(mesh)

        # 衣装らしい形状かどうか
        is_clothing_like = self._assess_clothing_likeness(mesh, wear_type)

        shape_valid = (
            not has_holes
            and not has_strange_protrusions
            and shape_smoothness > 0.6
            and is_clothing_like
        )

        return {
            "valid": shape_valid,
            "has_holes": has_holes,
            "has_protrusions": has_strange_protrusions,
            "smoothness": shape_smoothness,
            "clothing_like": is_clothing_like,
        }

    def _validate_wear_type_specific(
        self, obj: bpy.types.Object, wear_type: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """衣装タイプ固有の検証"""
        if wear_type == "SKIRT":
            return self._validate_skirt_specific(obj, params)
        elif wear_type == "GLOVES":
            return self._validate_gloves_specific(obj, params)
        elif wear_type == "SOCKS":
            return self._validate_socks_specific(obj, params)
        else:
            return {"valid": True, "message": "No specific validation for this type"}

    def _validate_skirt_specific(
        self, obj: bpy.types.Object, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """スカート固有の検証"""
        expected_pleats = params.get("pleat_count", 12)

        # プリーツ形状の検証
        pleat_analysis = self._analyze_pleat_geometry(obj, expected_pleats)

        return {
            "valid": pleat_analysis["pleat_detected"]
            and pleat_analysis["pleat_regularity"] > 0.6,
            "pleat_analysis": pleat_analysis,
        }

    def _validate_gloves_specific(
        self, obj: bpy.types.Object, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """手袋固有の検証"""
        finger_mode = params.get("glove_fingers", False)

        # 指の形状検証
        finger_analysis = self._analyze_finger_geometry(obj, finger_mode)

        return {
            "valid": finger_analysis["finger_count_valid"],
            "finger_analysis": finger_analysis,
        }

    def _validate_socks_specific(
        self, obj: bpy.types.Object, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """靴下固有の検証"""
        expected_length = params.get("sock_length", 0.5)

        # 長さと形状の検証
        length_analysis = self._analyze_sock_geometry(obj, expected_length)

        return {
            "valid": length_analysis["length_appropriate"],
            "length_analysis": length_analysis,
        }

    def _get_object_bounds(self, obj: bpy.types.Object) -> Dict[str, Tuple[float, ...]]:
        """オブジェクトの境界計算"""
        if not obj.data.vertices:
            return {"min": (0, 0, 0), "max": (0, 0, 0), "size": (0, 0, 0)}

        coords = [obj.matrix_world @ v.co for v in obj.data.vertices]

        min_x = min(co.x for co in coords)
        min_y = min(co.y for co in coords)
        min_z = min(co.z for co in coords)
        max_x = max(co.x for co in coords)
        max_y = max(co.y for co in coords)
        max_z = max(co.z for co in coords)

        return {
            "min": (min_x, min_y, min_z),
            "max": (max_x, max_y, max_z),
            "size": (max_x - min_x, max_y - min_y, max_z - min_z),
        }

    def _calculate_surface_area(self, obj: bpy.types.Object) -> float:
        """表面積計算"""
        return sum(poly.area for poly in obj.data.polygons)

    def _detect_holes(self, mesh: bpy.types.Mesh) -> bool:
        """穴の検出"""
        # 境界エッジの検出による穴の判定
        edge_face_count = {}
        for poly in mesh.polygons:
            for i in range(len(poly.vertices)):
                j = (i + 1) % len(poly.vertices)
                edge = tuple(sorted([poly.vertices[i], poly.vertices[j]]))
                edge_face_count[edge] = edge_face_count.get(edge, 0) + 1

        boundary_edges = [edge for edge, count in edge_face_count.items() if count == 1]
        return len(boundary_edges) > 0

    def _detect_protrusions(self, mesh: bpy.types.Mesh) -> bool:
        """異常な突起の検出"""
        if len(mesh.vertices) < 4:
            return False

        # 頂点の局所的な曲率変化を検査
        coords = np.array([v.co for v in mesh.vertices])
        center = np.mean(coords, axis=0)
        distances = np.linalg.norm(coords - center, axis=1)

        # 異常に離れた頂点の検出
        mean_dist = np.mean(distances)
        std_dist = np.std(distances)
        outlier_threshold = mean_dist + 3 * std_dist

        outliers = np.sum(distances > outlier_threshold)
        return outliers > len(mesh.vertices) * 0.05  # 5%以上が外れ値

    def _calculate_shape_smoothness(self, mesh: bpy.types.Mesh) -> float:
        """形状の滑らかさ計算"""
        if len(mesh.polygons) < 2:
            return 1.0

        try:
            # 隣接面の法線ベクトル間の角度を計算
            angles = []
            for edge in mesh.edges:
                if len(edge.link_faces) == 2:
                    face1, face2 = edge.link_faces
                    angle = face1.normal.angle(face2.normal)
                    angles.append(angle)

            if not angles:
                return 1.0

            # 平均角度から滑らかさを計算
            mean_angle = np.mean(angles)
            smoothness = 1.0 - min(mean_angle / math.pi, 1.0)
            return smoothness
        except:
            return 0.5  # デフォルト値

    def _assess_clothing_likeness(self, mesh: bpy.types.Mesh, wear_type: str) -> bool:
        """衣装らしさの評価"""
        # 基本的な形状特徴による判定
        vertex_count = len(mesh.vertices)
        face_count = len(mesh.polygons)

        # 適切な解像度かチェック
        appropriate_resolution = 50 <= vertex_count <= 10000

        # 面密度チェック
        if vertex_count > 0:
            face_density = face_count / vertex_count
            appropriate_density = 1.5 <= face_density <= 3.0
        else:
            appropriate_density = False

        return appropriate_resolution and appropriate_density

    def _analyze_pleat_geometry(
        self, obj: bpy.types.Object, expected_pleats: int
    ) -> Dict[str, Any]:
        """プリーツ形状の解析"""
        mesh = obj.data

        # シャープエッジによるプリーツ検出
        sharp_edges = [e for e in mesh.edges if e.use_edge_sharp]
        estimated_pleats = max(1, len(sharp_edges) // 2)

        pleat_regularity = 1.0 - abs(estimated_pleats - expected_pleats) / max(
            expected_pleats, 1
        )

        return {
            "pleat_detected": len(sharp_edges) > 0,
            "estimated_pleat_count": estimated_pleats,
            "expected_pleat_count": expected_pleats,
            "pleat_regularity": max(0.0, pleat_regularity),
            "sharp_edge_count": len(sharp_edges),
        }

    def _analyze_finger_geometry(
        self, obj: bpy.types.Object, finger_mode: bool
    ) -> Dict[str, Any]:
        """指形状の解析"""
        mesh = obj.data

        # 簡易的な指の検出（突起の数による推定）
        coords = np.array([v.co for v in mesh.vertices])

        if len(coords) == 0:
            return {"finger_count_valid": False, "detected_fingers": 0}

        # Z軸方向の突起検出
        z_coords = coords[:, 2]
        z_mean = np.mean(z_coords)
        z_std = np.std(z_coords)

        high_points = np.sum(z_coords > z_mean + z_std)
        estimated_fingers = min(high_points // 3, 5)  # 最大5本指

        if finger_mode:
            finger_valid = 3 <= estimated_fingers <= 5
        else:
            finger_valid = estimated_fingers <= 2  # ミトンタイプ

        return {
            "finger_count_valid": finger_valid,
            "detected_fingers": estimated_fingers,
            "finger_mode": finger_mode,
        }

    def _analyze_sock_geometry(
        self, obj: bpy.types.Object, expected_length: float
    ) -> Dict[str, Any]:
        """靴下形状の解析"""
        mesh = obj.data

        if not mesh.vertices:
            return {"length_appropriate": False}

        # Z軸方向の長さ測定
        z_coords = [v.co.z for v in mesh.vertices]
        actual_length = max(z_coords) - min(z_coords)

        # 期待される長さとの比較
        length_ratio = actual_length / max(expected_length, 0.1)
        length_appropriate = 0.7 <= length_ratio <= 1.5

        return {
            "length_appropriate": length_appropriate,
            "actual_length": actual_length,
            "expected_length": expected_length,
            "length_ratio": length_ratio,
        }

    def _calculate_visual_score(
        self, size_val: Dict, coverage_val: Dict, shape_val: Dict, type_val: Dict
    ) -> float:
        """視覚的品質スコア計算"""
        score = 0.0

        # サイズ検証（30%）
        if size_val["valid"]:
            score += 30.0 * size_val["size_accuracy"]

        # カバレッジ検証（25%）
        if coverage_val["valid"]:
            score += 25.0

        # 形状検証（25%）
        if shape_val["valid"]:
            score += 25.0 * shape_val["smoothness"]

        # タイプ固有検証（20%）
        if type_val["valid"]:
            score += 20.0

        return min(100.0, score)

    def _log_visual_validation_results(self, result: Dict[str, Any]):
        """視覚検証結果の詳細ログ"""
        wear_type = result["wear_type"]
        overall_valid = result["overall_valid"]
        visual_score = result["visual_score"]

        status_emoji = "✅" if overall_valid else "❌"
        logger.info(
            f"{status_emoji} Visual validation for {wear_type}: Score={visual_score:.1f}/100"
        )

        # サイズ検証ログ
        size_val = result["size_validation"]
        size_emoji = "✅" if size_val["valid"] else "❌"
        logger.info(
            f"  {size_emoji} Size: Accuracy={size_val['size_accuracy']:.2f}, Expected thickness={size_val['expected_thickness']:.4f}"
        )

        # カバレッジ検証ログ
        coverage_val = result["coverage_validation"]
        coverage_emoji = "✅" if coverage_val["valid"] else "❌"
        logger.info(
            f"  {coverage_emoji} Coverage: Ratio={coverage_val['coverage_ratio']:.3f} (expected: {coverage_val['expected_ratio']:.3f})"
        )

        # 形状検証ログ
        shape_val = result["shape_validation"]
        shape_emoji = "✅" if shape_val["valid"] else "❌"
        logger.info(
            f"  {shape_emoji} Shape: Smoothness={shape_val['smoothness']:.2f}, Holes={shape_val['has_holes']}, Protrusions={shape_val['has_protrusions']}"
        )

        # タイプ固有検証ログ
        type_val = result["type_specific_validation"]
        type_emoji = "✅" if type_val["valid"] else "❌"
        logger.info(
            f"  {type_emoji} Type-specific: {type_val.get('message', 'Validation completed')}"
        )


class UltimateAIWearGenerator:
    """最高品質AI衣装生成システム"""

    def __init__(self, props):
        self.props = props
        self.base_obj = props.base_body
        self.wear_type = props.wear_type
        self.quality = props.quality_level
        self.ai_settings = props.get_ai_settings()
        self.generation_start_time = time.time()

        # 品質検証システム
        self.geometry_validator = GeometryQualityValidator()
        self.visual_validator = VisualValidationLogger()

        # 生成状態追跡
        self.generation_stages = []
        self.quality_checkpoints = []

        logger.info(
            f"🚀 Ultimate AI Wear Generator initialized for {self.wear_type} (Quality: {self.quality})"
        )

    def generate(self) -> Optional[bpy.types.Object]:
        """最高品質メッシュ生成"""
        try:
            self._log_generation_start()

            # Stage 1: 前処理と検証
            self._add_stage("preprocessing", "Preprocessing and validation")
            if not self._validate_prerequisites():
                return None

            # Stage 2: ベースメッシュ生成
            self._add_stage("base_mesh", "Base mesh generation")
            garment = self._generate_base_mesh_with_validation()
            if not garment:
                return None

            # Stage 3: 形状調整とフィッティング
            self._add_stage("fitting", "Shape adjustment and fitting")
            if not self._apply_intelligent_fitting(garment):
                return None

            # Stage 4: 品質向上処理
            self._add_stage("enhancement", "Quality enhancement")
            if not self._apply_quality_enhancements(garment):
                return None

            # Stage 5: 最終検証と調整
            self._add_stage("finalization", "Final validation and adjustment")
            if not self._finalize_with_validation(garment):
                return None

            # 視覚的検証
            visual_result = self.visual_validator.validate_visual_appearance(
                self.base_obj, garment, self.wear_type, self.ai_settings
            )

            self._log_generation_completion(garment, visual_result)

            return garment

        except Exception as e:
            logger.error(f"❌ Ultimate generation failed: {str(e)}")
            return None

    def _log_generation_start(self):
        """生成開始ログ"""
        logger.info(f"🎯 Starting {self.wear_type} generation with Ultimate AI system")
        logger.info(
            f"📋 Base object: {self.base_obj.name} ({len(self.base_obj.data.vertices)} vertices)"
        )
        logger.info(f"⚙️  Quality level: {self.quality}")
        logger.info(f"🎛️  AI Settings: {self.ai_settings}")

    def _add_stage(self, stage_id: str, description: str):
        """生成ステージの追加"""
        stage_info = {
            "id": stage_id,
            "description": description,
            "start_time": time.time(),
            "status": "in_progress",
        }
        self.generation_stages.append(stage_info)
        logger.info(f"📍 Stage {len(self.generation_stages)}: {description}")

    def _complete_stage(self, success: bool, details: str = ""):
        """ステージ完了"""
        if self.generation_stages:
            stage = self.generation_stages[-1]
            stage["status"] = "completed" if success else "failed"
            stage["end_time"] = time.time()
            stage["duration"] = stage["end_time"] - stage["start_time"]
            stage["details"] = details

            status_emoji = "✅" if success else "❌"
            logger.info(
                f"{status_emoji} Stage completed in {stage['duration']:.3f}s: {details}"
            )

    def _validate_prerequisites(self) -> bool:
        """前提条件の検証"""
        try:
            if not self.base_obj or self.base_obj.type != "MESH":
                logger.error("❌ Invalid base object: not a mesh")
                self._complete_stage(False, "Invalid base object")
                return False

            if not self.base_obj.data.vertices:
                logger.error("❌ Base mesh has no vertices")
                self._complete_stage(False, "Empty base mesh")
                return False

            # ベースオブジェクトの品質検証
            base_validation = self.geometry_validator.validate_mesh_comprehensive(
                self.base_obj, "(base object)"
            )

            if not base_validation["valid"]:
                logger.warning("⚠️  Base object has quality issues but continuing...")

            self._complete_stage(
                True,
                f"Base object validated (score: {base_validation['overall_score']:.1f})",
            )
            return True

        except Exception as e:
            logger.error(f"❌ Prerequisite validation failed: {e}")
            self._complete_stage(False, str(e))
            return False

    def _generate_base_mesh_with_validation(self) -> Optional[bpy.types.Object]:
        """検証付きベースメッシュ生成"""
        try:
            # 従来の生成方法を使用
            generator_map = {
                "PANTS": self._generate_pants_ultimate,
                "T_SHIRT": self._generate_tshirt_ultimate,
                "BRA": self._generate_bra_ultimate,
                "SOCKS": self._generate_socks_ultimate,
                "GLOVES": self._generate_gloves_ultimate,
            }

            generator = generator_map.get(self.wear_type)
            if not generator:
                logger.error(f"❌ Unsupported wear type: {self.wear_type}")
                self._complete_stage(False, f"Unsupported wear type: {self.wear_type}")
                return None

            garment = generator()

            if garment:
                # 即座に品質検証
                validation_result = self.geometry_validator.validate_mesh_comprehensive(
                    garment, "(after base generation)"
                )

                self.quality_checkpoints.append(
                    {"stage": "base_mesh", "result": validation_result}
                )

                if validation_result["valid"]:
                    self._complete_stage(
                        True,
                        f"Base mesh generated (score: {validation_result['overall_score']:.1f})",
                    )
                else:
                    logger.warning("⚠️  Base mesh has quality issues but continuing...")
                    self._complete_stage(
                        True,
                        f"Base mesh generated with issues (score: {validation_result['overall_score']:.1f})",
                    )

                return garment
            else:
                logger.error("❌ Base mesh generation failed")
                self._complete_stage(False, "Base mesh generation failed")
                return None

        except Exception as e:
            logger.error(f"❌ Base mesh generation error: {e}")
            self._complete_stage(False, str(e))
            return None

    def _generate_pants_ultimate(self) -> Optional[bpy.types.Object]:
        """究極品質パンツ生成"""
        logger.info("👖 Generating ultimate quality pants")

        # 頂点グループの検索と検証
        hip_groups = core_utils.find_vertex_groups_by_type(self.base_obj, "hip")
        leg_groups = core_utils.find_vertex_groups_by_type(self.base_obj, "leg")
        target_groups = hip_groups + leg_groups

        if not target_groups:
            logger.error("❌ No suitable vertex groups found for pants")
            return None

        logger.info(f"📍 Found {len(target_groups)} vertex groups for pants generation")

        # メッシュ作成
        mesh = self.base_obj.data.copy()
        pants_obj = bpy.data.objects.new(f"{self.base_obj.name}_Ultimate_Pants", mesh)
        bpy.context.collection.objects.link(pants_obj)

        try:
            # bmesh操作
            bm = bmesh.new()
            bm.from_mesh(mesh)

            logger.info(f"🔧 Processing {len(bm.verts)} vertices for pants generation")

            # AI駆動頂点選択
            selected_verts = self._ai_select_vertices_enhanced(
                bm, target_groups, "pants"
            )
            logger.info(f"🎯 Selected {len(selected_verts)} vertices for pants")

            if not selected_verts:
                logger.error("❌ No vertices selected for pants generation")
                raise Exception("No vertices selected")

            # 不要頂点の除去
            self._remove_unwanted_vertices_safe(bm, selected_verts)

            # 厚み適用
            self._apply_intelligent_thickness(bm, "pants")

            # メッシュ最適化
            self._optimize_mesh_quality(bm)

            # 品質向上処理
            if self.ai_settings["quality_mode"]:
                self._apply_ai_smoothing_enhanced(bm, iterations=2)

            # メッシュ更新
            bm.to_mesh(mesh)
            bm.free()

            # エッジスムージング
            core_utils.apply_edge_smoothing(pants_obj)

            logger.info("✅ Ultimate pants generation completed successfully")
            return pants_obj

        except Exception as e:
            logger.error(f"❌ Pants generation failed: {e}")
            if pants_obj.name in bpy.data.objects:
                bpy.data.objects.remove(pants_obj, do_unlink=True)
            return None

    def _generate_tshirt_ultimate(self) -> Optional[bpy.types.Object]:
        """究極品質Tシャツ生成"""
        logger.info("👕 Generating ultimate quality T-shirt")

        chest_groups = core_utils.find_vertex_groups_by_type(self.base_obj, "chest")
        arm_groups = core_utils.find_vertex_groups_by_type(self.base_obj, "arm")
        torso_groups = core_utils.find_vertex_groups_by_type(self.base_obj, "torso")
        target_groups = chest_groups + arm_groups + torso_groups

        mesh = self.base_obj.data.copy()
        tshirt_obj = bpy.data.objects.new(f"{self.base_obj.name}_Ultimate_Tshirt", mesh)
        bpy.context.collection.objects.link(tshirt_obj)

        try:
            bm = bmesh.new()
            bm.from_mesh(mesh)

            logger.info(
                f"🔧 Processing {len(bm.verts)} vertices for T-shirt generation"
            )

            if target_groups:
                selected_verts = self._ai_select_vertices_enhanced(
                    bm, target_groups, "tshirt"
                )
                logger.info(
                    f"🎯 Selected {len(selected_verts)} vertices using vertex groups"
                )
            else:
                selected_verts = self._height_based_selection_enhanced(bm, 0.4)
                logger.info(
                    f"🎯 Selected {len(selected_verts)} vertices using height-based selection"
                )

            if not selected_verts:
                logger.error("❌ No vertices selected for T-shirt generation")
                raise Exception("No vertices selected")

            self._remove_unwanted_vertices_safe(bm, selected_verts)
            self._apply_intelligent_thickness(bm, "tshirt")
            self._optimize_mesh_quality(bm)

            if self.ai_settings["quality_mode"]:
                self._apply_ai_smoothing_enhanced(bm, iterations=2)

            bm.to_mesh(mesh)
            bm.free()

            core_utils.apply_edge_smoothing(tshirt_obj)

            logger.info("✅ Ultimate T-shirt generation completed successfully")
            return tshirt_obj

        except Exception as e:
            logger.error(f"❌ T-shirt generation failed: {e}")
            if tshirt_obj.name in bpy.data.objects:
                bpy.data.objects.remove(tshirt_obj, do_unlink=True)
            return None

    def _generate_bra_ultimate(self) -> Optional[bpy.types.Object]:
        """究極品質ブラ生成"""
        logger.info("👙 Generating ultimate quality bra")

        chest_groups = core_utils.find_vertex_groups_by_type(self.base_obj, "chest")
        breast_groups = core_utils.find_vertex_groups_by_type(self.base_obj, "breast")
        target_groups = chest_groups + breast_groups

        mesh = self.base_obj.data.copy()
        bra_obj = bpy.data.objects.new(f"{self.base_obj.name}_Ultimate_Bra", mesh)
        bpy.context.collection.objects.link(bra_obj)

        try:
            bm = bmesh.new()
            bm.from_mesh(mesh)

            logger.info(f"🔧 Processing {len(bm.verts)} vertices for bra generation")

            if target_groups:
                selected_verts = self._ai_select_vertices_enhanced(
                    bm, target_groups, "bra"
                )
                logger.info(
                    f"🎯 Selected {len(selected_verts)} vertices using vertex groups"
                )
            else:
                selected_verts = self._statistical_selection_enhanced(bm, "chest")
                logger.info(
                    f"🎯 Selected {len(selected_verts)} vertices using statistical selection"
                )

            if not selected_verts:
                logger.error("❌ No vertices selected for bra generation")
                raise Exception("No vertices selected")

            self._remove_unwanted_vertices_safe(bm, selected_verts)
            self._apply_intelligent_thickness(bm, "bra")
            self._optimize_mesh_quality(bm)

            if self.ai_settings["quality_mode"]:
                self._apply_ai_smoothing_enhanced(bm, iterations=3)

            bm.to_mesh(mesh)
            bm.free()

            core_utils.apply_edge_smoothing(bra_obj)

            logger.info("✅ Ultimate bra generation completed successfully")
            return bra_obj

        except Exception as e:
            logger.error(f"❌ Bra generation failed: {e}")
            if bra_obj.name in bpy.data.objects:
                bpy.data.objects.remove(bra_obj, do_unlink=True)
            return None

    def _generate_socks_ultimate(self) -> Optional[bpy.types.Object]:
        """究極品質靴下生成"""
        logger.info("🧦 Generating ultimate quality socks")

        foot_groups = core_utils.find_vertex_groups_by_type(self.base_obj, "foot")
        leg_groups = core_utils.find_vertex_groups_by_type(self.base_obj, "leg")
        target_groups = foot_groups + leg_groups

        if not target_groups:
            logger.error("❌ No suitable vertex groups found for socks")
            return None

        mesh = self.base_obj.data.copy()
        socks_obj = bpy.data.objects.new(f"{self.base_obj.name}_Ultimate_Socks", mesh)
        bpy.context.collection.objects.link(socks_obj)

        try:
            bm = bmesh.new()
            bm.from_mesh(mesh)

            logger.info(f"🔧 Processing {len(bm.verts)} vertices for socks generation")

            selected_verts = self._length_based_selection_enhanced(
                bm, target_groups, "socks"
            )
            logger.info(
                f"🎯 Selected {len(selected_verts)} vertices for socks (length: {self.props.sock_length})"
            )

            if not selected_verts:
                logger.error("❌ No vertices selected for socks generation")
                raise Exception("No vertices selected")

            self._remove_unwanted_vertices_safe(bm, selected_verts)
            self._apply_intelligent_thickness(bm, "socks")
            self._optimize_mesh_quality(bm)

            if self.ai_settings["quality_mode"]:
                self._apply_ai_smoothing_enhanced(bm, iterations=1)

            bm.to_mesh(mesh)
            bm.free()

            core_utils.apply_edge_smoothing(socks_obj)

            logger.info("✅ Ultimate socks generation completed successfully")
            return socks_obj

        except Exception as e:
            logger.error(f"❌ Socks generation failed: {e}")
            if socks_obj.name in bpy.data.objects:
                bpy.data.objects.remove(socks_obj, do_unlink=True)
            return None

    def _generate_gloves_ultimate(self) -> Optional[bpy.types.Object]:
        """究極品質手袋生成"""
        logger.info("🧤 Generating ultimate quality gloves")

        left_hand, right_hand = core_utils.find_hand_vertex_groups(self.base_obj)
        hand_groups = core_utils.find_vertex_groups_by_type(self.base_obj, "hand")

        if not (left_hand or right_hand):
            logger.error("❌ No hand vertex groups found for gloves")
            return None

        target_groups = (
            ([left_hand] if left_hand else [])
            + ([right_hand] if right_hand else [])
            + hand_groups
        )

        mesh = self.base_obj.data.copy()
        gloves_obj = bpy.data.objects.new(f"{self.base_obj.name}_Ultimate_Gloves", mesh)
        bpy.context.collection.objects.link(gloves_obj)

        try:
            bm = bmesh.new()
            bm.from_mesh(mesh)

            logger.info(f"🔧 Processing {len(bm.verts)} vertices for gloves generation")

            selected_verts = self._ai_select_vertices_enhanced(
                bm, target_groups, "gloves"
            )
            logger.info(f"🎯 Selected {len(selected_verts)} vertices for gloves")

            if not selected_verts:
                logger.error("❌ No vertices selected for gloves generation")
                raise Exception("No vertices selected")

            self._remove_unwanted_vertices_safe(bm, selected_verts)

            # 指タイプの処理
            if not self.props.glove_fingers:
                logger.info("🤏 Converting to mitten type")
                self._simplify_to_mitten_enhanced(bm)

            self._apply_intelligent_thickness(bm, "gloves")
            self._optimize_mesh_quality(bm)

            if self.ai_settings["quality_mode"]:
                self._apply_ai_smoothing_enhanced(bm, iterations=1)

            bm.to_mesh(mesh)
            bm.free()

            core_utils.apply_edge_smoothing(gloves_obj)

            logger.info("✅ Ultimate gloves generation completed successfully")
            return gloves_obj

        except Exception as e:
            logger.error(f"❌ Gloves generation failed: {e}")
            if gloves_obj.name in bpy.data.objects:
                bpy.data.objects.remove(gloves_obj, do_unlink=True)
            return None

    def _ai_select_vertices_enhanced(
        self, bm: bmesh.types.BMesh, groups: list, wear_type: str
    ) -> list:
        """強化AI頂点選択"""
        deform_layer = bm.verts.layers.deform.verify()
        selected_verts = []

        threshold_map = {
            "pants": self.ai_settings.get("threshold", 0.3),
            "tshirt": self.ai_settings.get("tshirt_threshold", 0.1),
            "bra": self.ai_settings.get("bra_threshold", 0.1),
            "gloves": self.ai_settings.get("hand_threshold", 0.1),
            "socks": 0.1
            * self.props.sock_length
            * self.ai_settings.get("sock_multiplier", 1.0),
        }

        threshold = threshold_map.get(wear_type, 0.2)
        logger.debug(
            f"🎯 Using threshold {threshold:.3f} for {wear_type} vertex selection"
        )

        # 頂点選択とウェイト分析
        total_weight = 0.0
        weight_distribution = []

        for vert in bm.verts:
            max_weight = 0.0
            for group in groups:
                if group.index in vert[deform_layer]:
                    weight = vert[deform_layer][group.index]
                    max_weight = max(max_weight, weight)

            weight_distribution.append(max_weight)
            total_weight += max_weight

            if max_weight > threshold:
                selected_verts.append(vert)

        # 選択品質の分析
        if weight_distribution:
            avg_weight = total_weight / len(weight_distribution)
            selected_ratio = len(selected_verts) / len(bm.verts)

            logger.debug(
                f"📊 Selection analysis: avg_weight={avg_weight:.3f}, selected_ratio={selected_ratio:.3f}"
            )

        return list(set(selected_verts))

    def _height_based_selection_enhanced(
        self, bm: bmesh.types.BMesh, factor: float
    ) -> list:
        """強化高さベース選択"""
        if not bm.verts:
            return []

        z_coords = [v.co.z for v in bm.verts]
        z_mean = sum(z_coords) / len(z_coords)
        z_std = (sum((z - z_mean) ** 2 for z in z_coords) / len(z_coords)) ** 0.5

        threshold_z = z_mean + (z_std * factor)
        selected_verts = [v for v in bm.verts if v.co.z > threshold_z]

        logger.debug(
            f"📏 Height selection: mean_z={z_mean:.3f}, std_z={z_std:.3f}, threshold={threshold_z:.3f}"
        )

        return selected_verts

    def _statistical_selection_enhanced(
        self, bm: bmesh.types.BMesh, body_part: str
    ) -> list:
        """強化統計的選択"""
        if not bm.verts:
            return []

        z_coords = [v.co.z for v in bm.verts]
        z_mean = sum(z_coords) / len(z_coords)
        z_std = (sum((z - z_mean) ** 2 for z in z_coords) / len(z_coords)) ** 0.5

        if body_part == "chest":
            threshold_z = z_mean + (z_std * 0.5)  # より緩い閾値
        else:
            threshold_z = z_mean

        selected_verts = [v for v in bm.verts if v.co.z >= threshold_z]

        logger.debug(
            f"📈 Statistical selection for {body_part}: threshold={threshold_z:.3f}, selected={len(selected_verts)}"
        )

        return selected_verts

    def _length_based_selection_enhanced(
        self, bm: bmesh.types.BMesh, groups: list, wear_type: str
    ) -> list:
        """強化長さベース選択"""
        deform_layer = bm.verts.layers.deform.verify()
        min_weight = (
            0.1 * self.props.sock_length * self.ai_settings.get("sock_multiplier", 1.0)
        )

        selected_verts = []
        weight_stats = []

        for vert in bm.verts:
            max_weight = 0.0
            for group in groups:
                if group.index in vert[deform_layer]:
                    weight = vert[deform_layer][group.index]
                    max_weight = max(max_weight, weight)

            weight_stats.append(max_weight)
            if max_weight > min_weight:
                selected_verts.append(vert)

        if weight_stats:
            avg_weight = sum(weight_stats) / len(weight_stats)
            logger.debug(
                f"📐 Length selection: min_weight={min_weight:.3f}, avg_weight={avg_weight:.3f}"
            )

        return list(set(selected_verts))

    def _remove_unwanted_vertices_safe(
        self, bm: bmesh.types.BMesh, keep_verts: list
    ) -> None:
        """安全な不要頂点除去"""
        try:
            verts_to_remove = [v for v in bm.verts if v not in keep_verts]

            if verts_to_remove:
                logger.debug(f"🗑️  Removing {len(verts_to_remove)} unwanted vertices")
                bmesh.ops.delete(bm, geom=verts_to_remove, context="VERTS")

                # インデックス更新
                bm.verts.ensure_lookup_table()
                bm.edges.ensure_lookup_table()
                bm.faces.ensure_lookup_table()

        except Exception as e:
            logger.warning(f"⚠️  Vertex removal warning: {e}")

    def _apply_intelligent_thickness(
        self, bm: bmesh.types.BMesh, wear_type: str
    ) -> None:
        """インテリジェント厚み適用"""
        base_thickness = self.props.thickness * self.ai_settings.get(
            "thickness_multiplier", 1.0
        )

        # 衣装タイプ別の厚み調整
        thickness_modifiers = {
            "pants": 1.0,
            "tshirt": 0.8,
            "bra": 0.6,
            "socks": 1.2,
            "gloves": 0.9,
        }

        adjusted_thickness = base_thickness * thickness_modifiers.get(wear_type, 1.0)

        logger.debug(
            f"📏 Applying thickness: base={base_thickness:.4f}, adjusted={adjusted_thickness:.4f}"
        )

        # 法線の計算と更新
        bm.normal_update()
        bm.verts.ensure_lookup_table()

        # 厚み適用
        for vert in bm.verts:
            vert.co += vert.normal * adjusted_thickness

    def _optimize_mesh_quality(self, bm: bmesh.types.BMesh) -> None:
        """メッシュ品質最適化"""
        try:
            # 重複頂点の除去
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)

            # 法線の再計算
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

            # 退化面の除去
            degenerate_faces = [f for f in bm.faces if f.calc_area() < 1e-8]
            if degenerate_faces:
                logger.debug(f"🧹 Removing {len(degenerate_faces)} degenerate faces")
                bmesh.ops.delete(bm, geom=degenerate_faces, context="FACES")

            # インデックス更新
            bm.verts.ensure_lookup_table()
            bm.edges.ensure_lookup_table()
            bm.faces.ensure_lookup_table()

            logger.debug("✨ Mesh optimization completed")

        except Exception as e:
            logger.warning(f"⚠️  Mesh optimization warning: {e}")

    def _apply_ai_smoothing_enhanced(
        self, bm: bmesh.types.BMesh, iterations: int = 1
    ) -> None:
        """強化AIスムージング"""
        try:
            original_vert_count = len(bm.verts)

            for i in range(iterations):
                bmesh.ops.smooth_vert(
                    bm,
                    verts=bm.verts,
                    factor=0.3,  # やや強めのスムージング
                    use_axis_x=True,
                    use_axis_y=True,
                    use_axis_z=True,
                )

                logger.debug(
                    f"🌊 AI smoothing iteration {i + 1}/{iterations} completed"
                )

            # スムージング後の品質チェック
            final_vert_count = len(bm.verts)
            if final_vert_count != original_vert_count:
                logger.warning(
                    f"⚠️  Vertex count changed during smoothing: {original_vert_count} -> {final_vert_count}"
                )

        except Exception as e:
            logger.error(f"❌ AI smoothing failed: {e}")

    def _simplify_to_mitten_enhanced(self, bm: bmesh.types.BMesh) -> None:
        """強化ミトン変換"""
        try:
            # 指の検出と統合
            finger_verts = []

            for vert in bm.verts:
                # 簡易的な指検出（高いZ座標と外側のX座標）
                if vert.co.z > 0 and abs(vert.co.x) > 0.2:
                    finger_verts.append(vert)

            if finger_verts:
                logger.debug(
                    f"🤏 Converting {len(finger_verts)} finger vertices to mitten"
                )

                # 指部分の統合
                bmesh.ops.remove_doubles(bm, verts=finger_verts, dist=0.08)

                # インデックス更新
                bm.verts.ensure_lookup_table()
                bm.faces.ensure_lookup_table()

        except Exception as e:
            logger.warning(f"⚠️  Mitten conversion warning: {e}")

    def _apply_intelligent_fitting(self, garment: bpy.types.Object) -> bool:
        """インテリジェントフィッティング"""
        try:
            logger.info("🎯 Applying intelligent fitting")

            # 既存のフィッティング機能を使用
            core_utils.apply_fitting(garment, self.base_obj, self.props)

            # フィッティング後の品質チェック
            fitting_validation = self.geometry_validator.validate_mesh_comprehensive(
                garment, "(after fitting)"
            )

            self.quality_checkpoints.append(
                {"stage": "fitting", "result": fitting_validation}
            )

            if fitting_validation["valid"]:
                self._complete_stage(
                    True,
                    f"Fitting completed (score: {fitting_validation['overall_score']:.1f})",
                )
                return True
            else:
                logger.warning(
                    "⚠️  Fitting resulted in quality issues but continuing..."
                )
                self._complete_stage(
                    True,
                    f"Fitting completed with issues (score: {fitting_validation['overall_score']:.1f})",
                )
                return True

        except Exception as e:
            logger.error(f"❌ Intelligent fitting failed: {e}")
            self._complete_stage(False, str(e))
            return False

    def _apply_quality_enhancements(self, garment: bpy.types.Object) -> bool:
        """品質向上処理"""
        try:
            logger.info("✨ Applying quality enhancements")

            if self.quality == "ULTIMATE":
                return self._apply_ultimate_quality_enhancements(garment)
            elif self.quality in ["HIGH", "STABLE"]:
                return self._apply_standard_quality_enhancements(garment)
            else:
                self._complete_stage(True, "Basic quality processing")
                return True

        except Exception as e:
            logger.error(f"❌ Quality enhancement failed: {e}")
            self._complete_stage(False, str(e))
            return False

    def _apply_ultimate_quality_enhancements(self, garment: bpy.types.Object) -> bool:
        """究極品質向上処理"""
        try:
            # エッジスムージング
            if self.props.enable_edge_smoothing:
                core_utils.apply_edge_smoothing(garment)
                logger.debug("✨ Edge smoothing applied")

            # サブディビジョンサーフェス
            if self.ai_settings["subdivision"]:
                core_utils.apply_subdivision_surface(garment, levels=1)
                logger.debug("🔲 Subdivision surface applied")

            # クロスシミュレーション
            if self.props.enable_cloth_sim:
                core_utils.setup_cloth_simulation(garment, self.base_obj)
                logger.debug("🧵 Cloth simulation setup")

            # 最終品質検証
            final_validation = self.geometry_validator.validate_mesh_comprehensive(
                garment, "(after ultimate enhancement)"
            )

            self.quality_checkpoints.append(
                {"stage": "ultimate_enhancement", "result": final_validation}
            )

            self._complete_stage(
                True,
                f"Ultimate enhancements applied (score: {final_validation['overall_score']:.1f})",
            )
            return True

        except Exception as e:
            logger.error(f"❌ Ultimate quality enhancement failed: {e}")
            self._complete_stage(False, str(e))
            return False

    def _apply_standard_quality_enhancements(self, garment: bpy.types.Object) -> bool:
        """標準品質向上処理"""
        try:
            if self.props.enable_edge_smoothing:
                core_utils.apply_edge_smoothing(garment)
                logger.debug("✨ Standard edge smoothing applied")

            standard_validation = self.geometry_validator.validate_mesh_comprehensive(
                garment, "(after standard enhancement)"
            )

            self.quality_checkpoints.append(
                {"stage": "standard_enhancement", "result": standard_validation}
            )

            self._complete_stage(
                True,
                f"Standard enhancements applied (score: {standard_validation['overall_score']:.1f})",
            )
            return True

        except Exception as e:
            logger.error(f"❌ Standard quality enhancement failed: {e}")
            self._complete_stage(False, str(e))
            return False

    def _finalize_with_validation(self, garment: bpy.types.Object) -> bool:
        """検証付き最終化"""
        try:
            logger.info("🏁 Finalizing garment with validation")

            # メッシュクリーンアップ
            core_utils.fix_duplicate_vertices(garment)

            # 名前設定
            garment.name = f"{self.base_obj.name}_{self.wear_type}_Ultimate"

            # 最終品質検証
            final_validation = self.geometry_validator.validate_mesh_comprehensive(
                garment, "(final)"
            )

            self.quality_checkpoints.append(
                {"stage": "finalization", "result": final_validation}
            )

            if final_validation["valid"]:
                self._complete_stage(
                    True,
                    f"Finalization completed (score: {final_validation['overall_score']:.1f})",
                )
                return True
            else:
                logger.warning("⚠️  Final validation shows quality issues")
                self._complete_stage(
                    True,
                    f"Finalization completed with issues (score: {final_validation['overall_score']:.1f})",
                )
                return True

        except Exception as e:
            logger.error(f"❌ Finalization failed: {e}")
            self._complete_stage(False, str(e))
            return False

    def _log_generation_completion(
        self, garment: bpy.types.Object, visual_result: Dict[str, Any]
    ):
        """生成完了ログ"""
        total_time = time.time() - self.generation_start_time

        logger.info(f"🎉 {self.wear_type} generation completed successfully!")
        logger.info(f"⏱️  Total generation time: {total_time:.3f} seconds")
        logger.info(f"🎭 Final object: {garment.name}")
        logger.info(
            f"👁️  Visual validation score: {visual_result['visual_score']:.1f}/100"
        )

        # ステージ別時間ログ
        logger.info("📊 Stage breakdown:")
        for stage in self.generation_stages:
            if "duration" in stage:
                logger.info(
                    f"   {stage['description']}: {stage['duration']:.3f}s ({stage['status']})"
                )

        # 品質チェックポイントのサマリー
        logger.info("🏆 Quality checkpoints:")
        for checkpoint in self.quality_checkpoints:
            score = checkpoint["result"]["overall_score"]
            stage = checkpoint["stage"]
            logger.info(f"   {stage}: {score:.1f}/100")

        # 最終推奨事項
        if visual_result["overall_valid"]:
            logger.info("✅ Generation meets all quality standards")
        else:
            logger.warning("⚠️  Generation has some quality issues but is usable")
            for issue in visual_result.get("recommendations", []):
                logger.info(f"   💡 {issue}")


def generate_pleated_skirt(props) -> Optional[bpy.types.Object]:
    """究極品質プリーツスカート生成"""
    logger.info("👗 Starting ultimate pleated skirt generation")

    try:
        # 頂点グループの検索
        hip_groups = core_utils.find_vertex_groups_by_type(props.base_body, "hip")
        leg_groups = core_utils.find_vertex_groups_by_type(props.base_body, "leg")

        if not hip_groups:
            logger.error("❌ No hip vertex groups found for skirt generation")
            return None

        logger.info(
            f"📍 Found vertex groups: {len(hip_groups)} hip, {len(leg_groups)} leg"
        )

        # ベースメッシュ作成
        skirt_obj = _create_skirt_base_mesh_ultimate(props, hip_groups + leg_groups)
        if not skirt_obj:
            return None

        # プリーツ生成
        _create_pleats_geometry_ultimate(skirt_obj, props)

        # 品質検証
        validator = GeometryQualityValidator()
        quality_result = validator.validate_mesh_comprehensive(
            skirt_obj, "(pleated skirt)"
        )

        # 視覚検証
        visual_validator = VisualValidationLogger()
        visual_result = visual_validator.validate_visual_appearance(
            props.base_body,
            skirt_obj,
            "SKIRT",
            {"pleat_count": props.pleat_count, "pleat_depth": props.pleat_depth},
        )

        # ログ出力
        logger.info(f"🎯 Skirt generation completed:")
        logger.info(f"   Quality score: {quality_result['overall_score']:.1f}/100")
        logger.info(f"   Visual score: {visual_result['visual_score']:.1f}/100")

        if quality_result["overall_score"] < 70:
            logger.warning(
                f"⚠️  Skirt quality score is low: {quality_result['overall_score']:.1f}"
            )
            for issue in quality_result.get("issues", []):
                logger.warning(f"     - {issue}")

        return skirt_obj

    except Exception as e:
        logger.error(f"❌ Pleated skirt generation failed: {e}")
        return None


def _create_skirt_base_mesh_ultimate(
    props, target_groups: list
) -> Optional[bpy.types.Object]:
    """究極品質スカートベースメッシュ作成"""
    logger.info("🔧 Creating ultimate quality skirt base mesh")

    mesh = props.base_body.data.copy()
    skirt_obj = bpy.data.objects.new(f"{props.base_body.name}_Ultimate_Skirt", mesh)
    bpy.context.collection.objects.link(skirt_obj)

    try:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        deform_layer = bm.verts.layers.deform.verify()

        logger.debug(f"🔧 Processing {len(bm.verts)} vertices for skirt base")

        # 長さファクターに基づく選択
        selected_verts = []
        length_factor = props.skirt_length
        min_weight = 0.15 * length_factor  # やや高い閾値

        weight_stats = []
        for vert in bm.verts:
            max_weight = 0.0
            for group in target_groups:
                if group.index in vert[deform_layer]:
                    weight = vert[deform_layer][group.index]
                    max_weight = max(max_weight, weight)

            weight_stats.append(max_weight)
            if max_weight > min_weight:
                selected_verts.append(vert)

        if not selected_verts:
            logger.error("❌ No vertices selected for skirt base mesh")
            raise Exception("No vertices selected for skirt")

        logger.info(
            f"🎯 Selected {len(selected_verts)} vertices for skirt (min_weight: {min_weight:.3f})"
        )

        # 不要頂点の除去
        verts_to_remove = [v for v in bm.verts if v not in selected_verts]
        if verts_to_remove:
            bmesh.ops.delete(bm, geom=verts_to_remove, context="VERTS")

        # 厚み適用
        thickness = props.thickness
        bm.normal_update()
        for vert in bm.verts:
            vert.co += vert.normal * thickness

        # メッシュ最適化
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

        bm.to_mesh(mesh)
        bm.free()

        core_utils.apply_edge_smoothing(skirt_obj)

        logger.info("✅ Skirt base mesh created successfully")
        return skirt_obj

    except Exception as e:
        logger.error(f"❌ Skirt base mesh creation failed: {e}")
        if skirt_obj.name in bpy.data.objects:
            bpy.data.objects.remove(skirt_obj, do_unlink=True)
        return None


def _create_pleats_geometry_ultimate(skirt_obj: bpy.types.Object, props) -> None:
    """究極品質プリーツ生成"""
    logger.info(
        f"📐 Creating ultimate pleats: count={props.pleat_count}, depth={props.pleat_depth}"
    )

    try:
        bpy.context.view_layer.objects.active = skirt_obj
        bpy.ops.object.mode_set(mode="EDIT")

        bm = bmesh.from_edit_mesh(skirt_obj.data)

        # ウエストと裾の頂点検出
        waist_verts = _detect_waist_vertices_enhanced(bm)
        hem_verts = _detect_hem_vertices_enhanced(bm)

        logger.debug(
            f"🔍 Detected {len(waist_verts)} waist vertices, {len(hem_verts)} hem vertices"
        )

        if not waist_verts or not hem_verts:
            logger.warning("⚠️  Could not detect waist or hem vertices properly")
            bpy.ops.object.mode_set(mode="OBJECT")
            return

        # プリーツ生成
        angle_step = 2 * math.pi / props.pleat_count
        successful_pleats = 0

        for i in range(props.pleat_count):
            try:
                _create_single_pleat_ultimate(
                    bm, waist_verts, hem_verts, i, angle_step, props.pleat_depth
                )
                successful_pleats += 1
            except Exception as e:
                logger.warning(f"⚠️  Pleat {i} creation failed: {e}")

        logger.info(
            f"✅ Created {successful_pleats}/{props.pleat_count} pleats successfully"
        )

        # シャープエッジ適用
        _apply_pleat_sharp_edges_ultimate(bm)

        bmesh.update_edit_mesh(skirt_obj.data)
        bpy.ops.object.mode_set(mode="OBJECT")

        logger.info("✅ Ultimate pleats geometry creation completed")

    except Exception as e:
        logger.error(f"❌ Pleats geometry creation failed: {e}")
        try:
            bpy.ops.object.mode_set(mode="OBJECT")
        except:
            pass


def _detect_waist_vertices_enhanced(bm: bmesh.types.BMesh) -> List[bmesh.types.BMVert]:
    """強化ウエスト頂点検出"""
    if not bm.verts:
        return []

    z_coords = [v.co.z for v in bm.verts]
    max_z = max(z_coords)
    waist_threshold = max_z - 0.05  # より精密な閾値

    waist_verts = [v for v in bm.verts if v.co.z >= waist_threshold]

    # 角度でソート
    def angle_from_center(v):
        return math.atan2(v.co.y, v.co.x)

    waist_verts.sort(key=angle_from_center)

    logger.debug(
        f"🔍 Waist detection: max_z={max_z:.3f}, threshold={waist_threshold:.3f}"
    )

    return waist_verts


def _detect_hem_vertices_enhanced(bm: bmesh.types.BMesh) -> List[bmesh.types.BMVert]:
    """強化裾頂点検出"""
    if not bm.verts:
        return []

    z_coords = [v.co.z for v in bm.verts]
    min_z = min(z_coords)
    hem_threshold = min_z + 0.05  # より精密な閾値

    hem_verts = [v for v in bm.verts if v.co.z <= hem_threshold]

    # 角度でソート
    def angle_from_center(v):
        return math.atan2(v.co.y, v.co.x)

    hem_verts.sort(key=angle_from_center)

    logger.debug(f"🔍 Hem detection: min_z={min_z:.3f}, threshold={hem_threshold:.3f}")

    return hem_verts


def _create_single_pleat_ultimate(
    bm, waist_verts, hem_verts, pleat_index, angle_step, depth
):
    """究極品質単一プリーツ作成"""
    if not waist_verts or not hem_verts:
        return

    waist_count = len(waist_verts)
    hem_count = len(hem_verts)

    if waist_count == 0 or hem_count == 0:
        return

    # より精密なインデックス計算
    waist_ratio = pleat_index / max(1, pleat_index + 1)
    hem_ratio = pleat_index / max(1, pleat_index + 1)

    waist_idx = int(waist_ratio * waist_count) % waist_count
    hem_idx = int(hem_ratio * hem_count) % hem_count

    if waist_idx < len(waist_verts) and hem_idx < len(hem_verts):
        waist_vert = waist_verts[waist_idx]
        hem_vert = hem_verts[hem_idx]

        # プリーツオフセットの計算
        fold_direction = (
            Vector(
                (
                    math.cos(angle_step * pleat_index),
                    math.sin(angle_step * pleat_index),
                    0,
                )
            )
            * depth
        )

        # より自然なプリーツ変形
        waist_vert.co += fold_direction * 0.3
        hem_vert.co += fold_direction * 0.7

        logger.debug(f"📐 Created pleat {pleat_index} with depth {depth:.4f}")


def _apply_pleat_sharp_edges_ultimate(bm: bmesh.types.BMesh):
    """究極品質プリーツシャープエッジ適用"""
    try:
        sharp_angle_threshold = math.radians(45)  # 45度
        sharp_edge_count = 0

        for edge in bm.edges:
            if len(edge.link_faces) == 2:
                face1, face2 = edge.link_faces
                try:
                    angle = face1.normal.angle(face2.normal)
                    if angle > sharp_angle_threshold:
                        edge.smooth = False
                        sharp_edge_count += 1
                except:
                    continue

        logger.debug(f"✨ Applied sharp edges to {sharp_edge_count} edges")

    except Exception as e:
        logger.warning(f"⚠️  Sharp edge application warning: {e}")
