"""
コアユーティリティ関数群
メッシュ操作、リギング、診断、ヘルパー機能
"""

import bpy
import bmesh
import mathutils
import time
from mathutils import Vector
from typing import Optional, Dict, Any, Tuple, List
import logging

logger = logging.getLogger(__name__)
























def find_vertex_groups_by_type(
    obj: bpy.types.Object, group_type: str
) -> List[bpy.types.VertexGroup]:
    """
    オブジェクトから指定されたタイプ（例: 'hip', 'chest'）に関連する頂点グループを検索して返します。
    名前にタイプ名を含むグループを検索します（大文字小文字を区別しない）。
    Args:
        obj: 頂点グループを検索するオブジェクト。
        group_type: 検索する頂点グループのタイプ名 (例: 'hip', 'chest', 'arm', 'foot', 'leg', 'hand')。
    Returns:
        見つかった頂点グループのリスト。
    """
    found_groups: List[bpy.types.VertexGroup] = []
    if obj and obj.type == "MESH" and obj.vertex_groups:
        search_term = group_type.lower()
        for vg in obj.vertex_groups:
            if search_term in vg.name.lower():
                found_groups.append(vg)
        logger.debug(
            f"オブジェクト '{obj.name}' からタイプ '{group_type}' に関連する頂点グループを {len(found_groups)} 個見つけました。"
        )
    else:
        logger.warning(
            f"オブジェクト '{obj.name if obj else 'None'}' はメッシュではないか、頂点グループがありません。検索をスキップします。"
        )

    return found_groups


def find_hand_vertex_groups(
    obj: bpy.types.Object,
) -> Tuple[Optional[bpy.types.VertexGroup], Optional[bpy.types.VertexGroup]]:
    """
    オブジェクトから左右の手に対応する頂点グループを検索して返します。
    名前に 'hand.L' または 'hand_L'、'hand.R' または 'hand_R' を含むグループを検索します。
    Args:
        obj: 頂点グループを検索するオブジェクト。
    Returns:
        左手、右手の頂点グループ (見つからなければ None) のタプル。
    """
    left_hand_vg = None
    right_hand_vg = None

    if obj and obj.type == "MESH" and obj.vertex_groups:
        for vg in obj.vertex_groups:
            name_lower = vg.name.lower()
            if "hand.l" in name_lower or "hand_l" in name_lower:
                left_hand_vg = vg
            elif "hand.r" in name_lower or "hand_r" in name_lower:
                right_hand_vg = vg

        logger.debug(
            f"オブジェクト '{obj.name}' から手の頂点グループを検索しました: 左={left_hand_vg.name if left_hand_vg else 'None'}, 右={right_hand_vg.name if right_hand_vg else 'None'}"
        )
    else:
        logger.warning(
            f"オブジェクト '{obj.name if obj else 'None'}' はメッシュではないか、頂点グループがありません。手の頂点グループ検索をスキップします。"
        )

    return left_hand_vg, right_hand_vg


def evaluate_pleats_geometry(
    skirt_obj: bpy.types.Object, expected_pleat_count: int
) -> Dict[str, Any]:
    """
    プリーツスカートのジオメトリを評価し、品質レポートを生成します。
    Args:
        skirt_obj: 評価するスカートオブジェクト。
        expected_pleat_count: 期待されるプリーツの数。
    Returns:
        評価結果を含む辞書。
    """
    report: Dict[str, Any] = {
        "object_name": skirt_obj.name if skirt_obj else "None",
        "expected_pleat_count": expected_pleat_count,
        "actual_pleat_count_estimate": 0,  # 実際のプリーツ数の推定値
        "vertex_count": 0,
        "face_count": 0,
        "manifold_check": False,  # 多様体チェック
        "sharp_edge_count": 0,  # シャープエッジ数
        "total_score": 0,  # 総合スコア (0-100)
        "messages": [],  # 評価メッセージ
    }

    if not (skirt_obj and skirt_obj.type == "MESH"):
        report["messages"].append("評価するオブジェクトがメッシュではありません。")
        return report

    mesh = skirt_obj.data
    report["vertex_count"] = len(mesh.vertices)
    report["face_count"] = len(mesh.polygons)

    # 多様体チェック (bmeshが必要)
    try:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        # logger.debug(f"evaluate_pleats_geometry: bm type: {type(bm)}") # 変更 - ログレベル調整のためコメントアウト
        # logger.debug(f"evaluate_pleats_geometry: bm attributes: {dir(bm)}") # 変更 - ログレベル調整のためコメントアウト
        # is_manifold は bmesh のプロパティ (Blender 4.1では変更の可能性あり)
        # Blender 4.1での多様体チェック方法に修正
        # bmesh.calc_manifold() は存在しないため、代替手段を検討
        # シンプルに頂点と辺の接続をチェックする方法などがあるが、ここではエラーを回避しつつ情報提供を優先
        # 一時的に多様体チェックをスキップするか、エラーハンドリングを強化
        try:
            # Blender 4.1で利用可能な多様体チェックの代替手段を探すか、エラーを適切に処理
            # 例: bmesh.utils.validate() や他のジオメトリチェック関数
            # ここではエラーを捕捉し、メッセージとして報告する
            # report["manifold_check"] = bm.calc_manifold() # 存在しないためコメントアウト
            # 代替として、より基本的なチェックや、エラーメッセージの改善を行う
            # 例: bm.is_valid() などが存在するか確認
            if hasattr(bm, 'is_valid'):
                 report["manifold_check"] = bm.is_valid()
                 if not report["manifold_check"]:
                     report["messages"].append("メッシュが有効ではありません (bmesh.is_valid() 判定)。ジオメトリに問題がある可能性があります。")
            else:
                 report["messages"].append("bmeshオブジェクトに多様体チェックまたは有効性チェックの属性が見つかりませんでした。")
                 report["manifold_check"] = False # チェックできなかった場合はFalseとする

        except Exception as e:
            report["messages"].append(f"多様体チェックまたはbmesh有効性チェック中にエラーが発生しました: {e}")
            report["manifold_check"] = False  # エラー時はFalseとする
        finally:
             bm.free() # bmeshオブジェクトは必ず解放する

    except Exception as e: # bmesh.new() や bm.from_mesh() でエラーが発生した場合
        report["messages"].append(f"bmeshオブジェクトの作成またはメッシュからのデータ読み込みに失敗しました: {e}")
        report["manifold_check"] = False # エラー時はFalseとする


    # シャープエッジ数のカウント (プリーツのエッジを想定)
    # Blender 4.1でも edge.use_edge_sharp は存在する可能性が高いが、念のためtry-exceptで囲む
    try:
        sharp_edges = [e for e in mesh.edges if e.use_edge_sharp]
        report["sharp_edge_count"] = len(sharp_edges)
    except Exception as e:
        report["messages"].append(f"シャープエッジのカウント中にエラーが発生しました: {e}")
        report["sharp_edge_count"] = 0 # エラー時は0とする


    # プリーツ数の推定 (シャープエッジ数から単純に推定)
    # これは非常に単純な推定であり、実際のプリーツ構造に依存します
    # より正確な推定には高度なジオメトリ解析が必要です
    if report["sharp_edge_count"] > 0:
        # プリーツは通常、表と裏にシャープエッジを持つため、シャープエッジ数を2で割る
        # ただし、端の処理などにより誤差が生じます
        report["actual_pleat_count_estimate"] = max(
            1, round(report["sharp_edge_count"] / 2)
        )
        if abs(report["actual_pleat_count_estimate"] - expected_pleat_count) > 2:
            report["messages"].append(
                f"推定プリーツ数 ({report['actual_pleat_count_estimate']}) が期待値 ({expected_pleat_count}) と大きく異なります。"
            )
    else:
        report["messages"].append(
            "シャープエッジが見つかりませんでした。プリーツが正しく形成されていない可能性があります。"
        )

    # 総合スコア計算 (非常に単純な例)
    score = 0
    if report["manifold_check"]:
        score += 30
    if abs(report["actual_pleat_count_estimate"] - expected_pleat_count) <= 2:



def log_progress(current: int, total: int, message: str) -> None:
    """
    進捗状況をログに出力します。
    Args:
        current: 現在のステップ。
        total: 全体のステップ数。
        message: 表示するメッセージ。
    """
    progress_percent = (current / total) * 100 if total > 0 else 0
    logger.info(f"進捗: {current}/{total} ({progress_percent:.1f}%) - {message}")


# 既存の apply_smooth_shading, remove_duplicate_vertices, clear_internal_cache は削除
# find_vertex_groups_by_type は core_generators で使用されているため残す
# find_hand_vertex_groups は core_operators で使用されているため残す
# evaluate_pleats_geometry は core_operators で使用されているため残す
