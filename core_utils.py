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

def apply_edge_smoothing(obj: bpy.types.Object, angle: float = 0.785398) -> None:
    """
    メッシュのエッジを滑らかにする処理を適用します。
    メッシュデータのオートスムース角度を設定します。
    Args:
        obj: スムージングを適用するオブジェクト。
        angle: オートスムースの角度閾値 (ラジアン)。デフォルトは45度。
    """
    if obj and obj.type == 'MESH':
        try:
            mesh = obj.data
            mesh.use_auto_smooth = True
            mesh.auto_smooth_angle = angle
            logger.debug(f"{obj.name} にオートスムースを適用 (角度: {angle:.2f} rad)")
        except Exception as e:
            logger.error(f"{obj.name} のオートスムース適用に失敗: {e}")
    else:
        logger.warning(f"オブジェクト '{obj.name if obj else 'None'}' はメッシュではありません。オートスムースをスキップします。")

def find_armature(obj: bpy.types.Object) -> Optional[bpy.types.Object]:
    """
    指定されたオブジェクトに関連付けられたアーマチュアをシーンから検索して返します。
    まず親オブジェクトを確認し、見つからなければシーン全体から検索します。
    Args:
        obj: アーマチュアを検索する基準となるオブジェクト。
    Returns:
        見つかったアーマチュアオブジェクト、または None。
    """
    if not obj:
        return None

    # 1. 親オブジェクトがアーマチュアか確認
    if obj.parent and obj.parent.type == 'ARMATURE':
        logger.debug(f"親オブジェクト '{obj.parent.name}' がアーマチュアとして見つかりました。")
        return obj.parent

    # 2. シーン全体からアーマチュアを検索し、指定オブジェクトがその子であるか確認
    armatures_in_scene = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE']
    for armature in armatures_in_scene:
        if obj in armature.children:
            logger.debug(f"シーン内のアーマチュア '{armature.name}' の子として '{obj.name}' が見つかりました。")
            return armature

    logger.debug(f"オブジェクト '{obj.name}' に関連付けられたアーマチュアは見つかりませんでした。")
    return None

def apply_rigging(garment: bpy.types.Object, base_body: bpy.types.Object, armature: bpy.types.Object) -> None:
    """
    衣装メッシュに自動ウェイトでリギングを適用します。
    Args:
        garment: リギングを適用する衣装オブジェクト。
        base_body: 素体オブジェクト (アーマチュア検索に使用)。
        armature: 適用するアーマチュアオブジェクト。
    """
    if not (garment and armature and garment.type == 'MESH' and armature.type == 'ARMATURE'):
        logger.warning("リギング適用に必要なオブジェクトが不足しているか、タイプが不正です。")
        return

    logger.info(f"衣装 '{garment.name}' にアーマチュア '{armature.name}' でリギングを適用開始...")

    # オブジェクトを選択し、アーマチュアをアクティブにする
    bpy.ops.object.select_all(action='DESELECT')
    armature.select_set(True)
    garment.select_set(True)
    bpy.context.view_layer.objects.active = armature

    # 自動ウェイトでペアレント
    try:
        # Blender 4.x での自動ウェイトペアレント
        bpy.ops.object.parent_set(type='ARMATURE', xmirror=False, keep_transform=False)
        logger.info(f"'{garment.name}' に自動ウェイトでリギングを適用しました。")
    except RuntimeError as e:
        logger.error(f"自動ウェイトでのペアレントに失敗しました: {e}")
        # エラー発生時は選択状態を解除
        bpy.ops.object.select_all(action='DESELECT')
    except Exception as e:
        logger.error(f"リギング適用中に予期せぬエラーが発生しました: {e}")
        bpy.ops.object.select_all(action='DESELECT')


def diagnose_mesh_structure(obj: bpy.types.Object) -> Dict[str, Any]:
    """
    メッシュの構造（頂点数、頂点グループ、ボーンなど）を診断し、結果を辞書で返します。
    Args:
        obj: 診断するメッシュオブジェクト。
    Returns:
        診断結果を含む辞書。
    """
    diagnosis: Dict[str, Any] = {}
    if obj and obj.type == 'MESH':
        mesh = obj.data
        diagnosis['mesh_name'] = obj.name
        diagnosis['vertex_count'] = len(mesh.vertices)
        diagnosis['edge_count'] = len(mesh.edges)
        diagnosis['face_count'] = len(mesh.polygons)
        diagnosis['vertex_groups'] = [vg.name for vg in obj.vertex_groups]

        # アーマチュア関連情報を追加
        armature = find_armature(obj)
        if armature:
            diagnosis['armature'] = armature.name
            diagnosis['bones'] = [bone.name for bone in armature.data.bones]
        else:
            diagnosis['armature'] = None
            diagnosis['bones'] = []

        # モディファイア情報を追加
        diagnosis['modifiers'] = [mod.type for mod in obj.modifiers] # タイプ名のみをリストアップ

    return diagnosis

def select_single_object(obj: bpy.types.Object) -> None:
    """
    指定されたオブジェクトのみを選択状態にし、アクティブオブジェクトに設定します。
    Args:
        obj: 選択・アクティブ化するオブジェクト。
    """
    if obj:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        logger.debug(f"オブジェクト '{obj.name}' を選択しアクティブに設定しました。")
    else:
        logger.warning("選択・アクティブ化するオブジェクトが指定されていません。")

def cleanup_mesh(obj: bpy.types.Object, merge_distance: float = 0.0001) -> None:
    """
    メッシュのクリーンアップ（重複頂点除去など）を行います。
    Args:
        obj: クリーンアップするメッシュオブジェクト。
        merge_distance: 重複と見なす頂点間の最大距離。
    """
    if obj and obj.type == 'MESH':
        select_single_object(obj)
        try:
            bpy.ops.object.mode_set(mode='EDIT')
            # 重複頂点を除去
            bpy.ops.mesh.remove_doubles(threshold=merge_distance)
            bpy.ops.object.mode_set(mode='OBJECT')
            logger.debug(f"'{obj.name}' のメッシュクリーンアップ (重複頂点除去) を実行しました。")
        except RuntimeError as e:
            logger.error(f"'{obj.name}' のメッシュクリーンアップに失敗しました: {e}")
            # エラー発生時はオブジェクトモードに戻す
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except RuntimeError:
                pass # モード変更できない場合もある
        except Exception as e:
            logger.error(f"'{obj.name}' のメッシュクリーンアップ中に予期せぬエラーが発生しました: {e}")
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except RuntimeError:
                pass

    else:
        logger.warning(f"オブジェクト '{obj.name if obj else 'None'}' はメッシュではありません。クリーンアップをスキップします。")


def organize_to_collection(obj: bpy.types.Object, collection_name: str) -> None:
    """
    指定されたオブジェクトを指定されたコレクションに移動します。
    コレクションが存在しない場合は作成します。
    Args:
        obj: 移動するオブジェクト。
        collection_name: 移動先のコレクション名。
    """
    if not (obj and collection_name):
        logger.warning("オブジェクトまたはコレクション名が指定されていません。コレクションへの整理をスキップします。")
        return

    # 既存のコレクションを検索または作成
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
        logger.debug(f"コレクション '{collection_name}' を作成しました。")

    # オブジェクトが既に目的のコレクションにリンクされているか確認
    if collection in obj.users_collection:
        logger.debug(f"オブジェクト '{obj.name}' は既にコレクション '{collection_name}' にリンクされています。")
        return

    # オブジェクトを既存のコレクションからリンク解除
    # イテレーション中にコレクションを変更すると問題が発生するため、リストのコピーを使用
    for coll in list(obj.users_collection):
        coll.objects.unlink(obj)
        logger.debug(f"オブジェクト '{obj.name}' をコレクション '{coll.name}' からリンク解除しました。")

    # オブジェクトを新しいコレクションにリンク
    collection.objects.link(obj)
    logger.debug(f"オブジェクト '{obj.name}' をコレクション '{collection_name}' にリンクしました。")


def apply_subdivision_surface(obj: bpy.types.Object, levels: int, render_levels: Optional[int] = None) -> None:
    """
    オブジェクトにサブディビジョンサーフェスモディファイアを適用します。
    Args:
        obj: モディファイアを適用するオブジェクト。
        levels: ビューポートでのサブディビジョンレベル。
        render_levels: レンダリング時のサブディビジョンレベル。指定しない場合は levels と同じ。
    """
    if not (obj and obj.type == 'MESH' and levels >= 0):
        logger.warning(f"オブジェクト '{obj.name if obj else 'None'}' はメッシュではないか、レベルが不正です。サブディビジョンをスキップします。")
        return

    # 既存のSubdivisionモディファイアがあれば削除
    for mod in obj.modifiers:
        if mod.type == 'SUBSURF':
            obj.modifiers.remove(mod)
            logger.debug(f"既存のSubdivisionモディファイア '{mod.name}' を削除しました。")

    # 新しいSubdivisionモディファイアを追加
    mod = obj.modifiers.new(name="Subdivision", type='SUBSURF')
    mod.levels = levels
    mod.render_levels = render_levels if render_levels is not None else levels
    logger.debug(f"'{obj.name}' に Subdivision モディファイアを追加 (ビューポート: {mod.levels}, レンダリング: {mod.render_levels})")


def setup_cloth_simulation(garment: bpy.types.Object, base_body: bpy.types.Object) -> None:
    """
    衣装メッシュにクロスシミュレーションを設定し、素体をコリジョンオブジェクトとして設定します。
    Args:
        garment: クロスシミュレーションを設定する衣装オブジェクト。
        base_body: コリジョンオブジェクトとして設定する素体オブジェクト。
    """
    if not (garment and base_body and garment.type == 'MESH' and base_body.type == 'MESH'):
        logger.warning("クロスシミュレーション設定に必要なオブジェクトが不足しているか、タイプが不正です。")
        return

    logger.info(f"衣装 '{garment.name}' にクロスシミュレーションを設定開始...")

    # 衣装にクロスモディファイアを追加
    try:
        # 既存のClothモディファイアがあれば削除
        for mod in garment.modifiers:
            if mod.type == 'CLOTH':
                garment.modifiers.remove(mod)
                logger.debug(f"既存のClothモディファイア '{mod.name}' を削除しました。")

        cloth_mod = garment.modifiers.new(name="Cloth", type='CLOTH')
        # クロス設定の調整はここに追加可能 (例: cloth_mod.settings.mass = 0.3)
        logger.debug(f"'{garment.name}' に Cloth モディファイアを追加しました。")
    except Exception as e:
        logger.error(f"'{garment.name}' への Cloth モディファイア追加に失敗: {e}")

    # 素体にコリジョンモディファイアを追加
    try:
        # 既存のCollisionモディファイアがあれば削除
        for mod in base_body.modifiers:
            if mod.type == 'COLLISION':
                base_body.modifiers.remove(mod)
                logger.debug(f"既存のCollisionモディファイア '{mod.name}' を削除しました。")

        collision_mod = base_body.modifiers.new(name="Collision", type='COLLISION')
        # コリジョン設定の調整はここに追加可能 (例: collision_mod.settings.thickness_outer = 0.01)
        logger.debug(f"'{base_body.name}' に Collision モディファイアを追加しました。")
    except Exception as e:
        logger.error(f"'{base_body.name}' への Collision モディファイア追加に失敗: {e}")


def find_vertex_groups_by_type(obj: bpy.types.Object, group_type: str) -> List[bpy.types.VertexGroup]:
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
    if obj and obj.type == 'MESH' and obj.vertex_groups:
        search_term = group_type.lower()
        for vg in obj.vertex_groups:
            if search_term in vg.name.lower():
                found_groups.append(vg)
        logger.debug(f"オブジェクト '{obj.name}' からタイプ '{group_type}' に関連する頂点グループを {len(found_groups)} 個見つけました。")
    else:
        logger.warning(f"オブジェクト '{obj.name if obj else 'None'}' はメッシュではないか、頂点グループがありません。検索をスキップします。")

    return found_groups

def find_hand_vertex_groups(obj: bpy.types.Object) -> Tuple[Optional[bpy.types.VertexGroup], Optional[bpy.types.VertexGroup]]:
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

    if obj and obj.type == 'MESH' and obj.vertex_groups:
        for vg in obj.vertex_groups:
            name_lower = vg.name.lower()
            if 'hand.l' in name_lower or 'hand_l' in name_lower:
                left_hand_vg = vg
            elif 'hand.r' in name_lower or 'hand_r' in name_lower:
                right_hand_vg = vg

        logger.debug(f"オブジェクト '{obj.name}' から手の頂点グループを検索しました: 左={left_hand_vg.name if left_hand_vg else 'None'}, 右={right_hand_vg.name if right_hand_vg else 'None'}")
    else:
        logger.warning(f"オブジェクト '{obj.name if obj else 'None'}' はメッシュではないか、頂点グループがありません。手の頂点グループ検索をスキップします。")

    return left_hand_vg, right_hand_vg

def evaluate_pleats_geometry(skirt_obj: bpy.types.Object, expected_pleat_count: int) -> Dict[str, Any]:
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
        "actual_pleat_count_estimate": 0, # 実際のプリーツ数の推定値
        "vertex_count": 0,
        "face_count": 0,
        "manifold_check": False, # 多様体チェック
        "sharp_edge_count": 0, # シャープエッジ数
        "total_score": 0, # 総合スコア (0-100)
        "messages": [] # 評価メッセージ
    }

    if not (skirt_obj and skirt_obj.type == 'MESH'):
        report["messages"].append("評価するオブジェクトがメッシュではありません。")
        return report

    mesh = skirt_obj.data
    report["vertex_count"] = len(mesh.vertices)
    report["face_count"] = len(mesh.polygons)

    # 多様体チェック (bmeshが必要)
    try:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        # is_manifold は bmesh のプロパティ
        report["manifold_check"] = bm.calc_manifold()
        bm.free()
        if not report["manifold_check"]:
             report["messages"].append("メッシュが多様体ではありません。ジオメトリに問題がある可能性があります。")
    except Exception as e:
        report["messages"].append(f"多様体チェックに失敗しました: {e}")
        report["manifold_check"] = False # エラー時はFalseとする

    # シャープエッジ数のカウント (プリーツのエッジを想定)
    sharp_edges = [e for e in mesh.edges if e.use_edge_sharp]
    report["sharp_edge_count"] = len(sharp_edges)

    # プリーツ数の推定 (シャープエッジ数から単純に推定)
    # これは非常に単純な推定であり、実際のプリーツ構造に依存します
    # より正確な推定には高度なジオメトリ解析が必要です
    if report["sharp_edge_count"] > 0:
         # プリーツは通常、表と裏にシャープエッジを持つため、シャープエッジ数を2で割る
         # ただし、端の処理などにより誤差が生じます
        report["actual_pleat_count_estimate"] = max(1, round(report["sharp_edge_count"] / 2))
        if abs(report["actual_pleat_count_estimate"] - expected_pleat_count) > 2:
             report["messages"].append(f"推定プリーツ数 ({report['actual_pleat_count_estimate']}) が期待値 ({expected_pleat_count}) と大きく異なります。")
    else:
         report["messages"].append("シャープエッジが見つかりませんでした。プリーツが正しく形成されていない可能性があります。")


    # 総合スコア計算 (非常に単純な例)
    score = 0
    if report["manifold_check"]:
        score += 30
    if abs(report["actual_pleat_count_estimate"] - expected_pleat_count) <= 2:
        score += 40 # プリーツ数が近いほど高得点
    elif abs(report["actual_pleat_count_estimate"] - expected_pleat_count) <= 5:
        score += 20
    # 他の評価基準（面の向き、重なりなど）を追加可能

    report["total_score"] = min(100, max(0, score)) # スコアを0-100に制限

    logger.info(f"スカート品質評価結果: {report}")
    return report

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