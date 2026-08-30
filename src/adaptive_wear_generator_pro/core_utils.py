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
    report: Dict[str, Any] = {
        "object_name": skirt_obj.name if skirt_obj else "None",
        "expected_pleat_count": expected_pleat_count,
        "actual_pleat_count_estimate": 0,
        "vertex_count": 0,
        "face_count": 0,
        "manifold_check": False,
        "sharp_edge_count": 0,
        "total_score": 0,
        "messages": [],
    }

    if not (skirt_obj and skirt_obj.type == "MESH"):
        report["messages"].append("評価するオブジェクトがメッシュではありません。")
        return report

    mesh = skirt_obj.data
    report["vertex_count"] = len(mesh.vertices)
    report["face_count"] = len(mesh.polygons)

    try:
        bm = bmesh.new()
        bm.from_mesh(mesh)

        try:
            if hasattr(bm, "is_valid"):
                report["manifold_check"] = bm.is_valid()
                if not report["manifold_check"]:
                    report["messages"].append(
                        "メッシュが有効ではありません (bmesh.is_valid() 判定)。ジオメトリに問題がある可能性があります。"
                    )
            else:
                report["messages"].append(
                    "bmeshオブジェクトに多様体チェックまたは有効性チェックの属性が見つかりませんでした。"
                )
                report["manifold_check"] = False
        except Exception as e:
            report["messages"].append(
                f"多様体チェックまたはbmesh有効性チェック中にエラーが発生しました: {e}"
            )
            report["manifold_check"] = False
        finally:
            bm.free()
    except Exception as e:
        report["messages"].append(
            f"bmeshオブジェクトの作成またはメッシュからのデータ読み込みに失敗しました: {e}"
        )
        report["manifold_check"] = False

    try:
        sharp_edges = [e for e in mesh.edges if e.use_edge_sharp]
        report["sharp_edge_count"] = len(sharp_edges)
    except Exception as e:
        report["messages"].append(
            f"シャープエッジのカウント中にエラーが発生しました: {e}"
        )
        report["sharp_edge_count"] = 0

    if report["sharp_edge_count"] > 0:
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

    score = 0
    if report["manifold_check"]:
        score += 30
    if abs(report["actual_pleat_count_estimate"] - expected_pleat_count) <= 2:
        score += 40

    report["total_score"] = score
    return report


def log_progress(current: int, total: int, message: str) -> None:
    progress_percent = (current / total) * 100 if total > 0 else 0
    logger.info(f"進捗: {current}/{total} ({progress_percent:.1f}%) - {message}")


def select_single_object(obj: bpy.types.Object) -> None:
    if obj:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        logger.debug(f"オブジェクト '{obj.name}' を選択しアクティブに設定しました。")
    else:
        logger.warning("選択・アクティブ化するオブジェクトが指定されていません。")


def find_armature(obj: bpy.types.Object) -> Optional[bpy.types.Object]:
    if not obj:
        return None
    for modifier in obj.modifiers:
        if modifier.type == "ARMATURE":
            return modifier.object
    return None


def apply_rigging(
    garment: bpy.types.Object, base_body: bpy.types.Object, armature: bpy.types.Object
) -> None:
    if not (garment and base_body and armature):
        return
    try:
        garment.modifiers.new(name="Armature", type="ARMATURE")
        garment.modifiers["Armature"].object = armature
        logger.info(f"リギング適用完了: {garment.name}")
    except Exception as e:
        logger.error(f"リギング適用エラー: {e}")


def setup_cloth_simulation(
    garment: bpy.types.Object, base_body: bpy.types.Object
) -> None:
    if not (garment and base_body):
        return
    try:
        cloth_mod = garment.modifiers.new(name="Cloth", type="CLOTH")
        cloth_mod.settings.quality = 5
        logger.info(f"クロスシミュレーション設定完了: {garment.name}")
    except Exception as e:
        logger.error(f"クロスシミュレーション設定エラー: {e}")


def apply_fitting(
    garment: bpy.types.Object, base_body: bpy.types.Object, props
) -> None:
    if not (garment and base_body):
        logger.warning("フィッティング適用に必要なオブジェクトが不足")
        return
    try:
        if props.tight_fit:
            offset_distance = props.ai_tight_offset * props.ai_offset_multiplier
        else:
            offset_distance = props.thickness

        bpy.context.view_layer.objects.active = garment
        bpy.ops.object.mode_set(mode="EDIT")
        bm = bmesh.from_edit_mesh(garment.data)
        for vert in bm.verts:
            vert.co += vert.normal * offset_distance
        bmesh.update_edit_mesh(garment.data)
        bpy.ops.object.mode_set(mode="OBJECT")
        logger.info(f"フィッティング処理完了: {garment.name}")
    except Exception as e:
        logger.error(f"フィッティング処理エラー: {e}")
        try:
            bpy.ops.object.mode_set(mode="OBJECT")
        except:
            pass


def fix_duplicate_vertices(obj: bpy.types.Object) -> None:
    if obj and obj.type == "MESH":
        cleanup_mesh(obj)


def cleanup_mesh(obj: bpy.types.Object, merge_distance: float = 0.0001) -> None:
    if obj and obj.type == "MESH":
        select_single_object(obj)
        try:
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.remove_doubles(threshold=merge_distance)
            bpy.ops.object.mode_set(mode="OBJECT")
            logger.debug(
                f"'{obj.name}' のメッシュクリーンアップ (重複頂点除去) を実行しました。"
            )
        except RuntimeError as e:
            logger.error(f"'{obj.name}' のメッシュクリーンアップに失敗しました: {e}")
            try:
                bpy.ops.object.mode_set(mode="OBJECT")
            except RuntimeError:
                pass
        except Exception as e:
            logger.error(
                f"'{obj.name}' のメッシュクリーンアップ中に予期せぬエラーが発生しました: {e}"
            )
            try:
                bpy.ops.object.mode_set(mode="OBJECT")
            except RuntimeError:
                pass
    else:
        logger.warning(
            f"オブジェクト '{obj.name if obj else 'None'}' はメッシュではありません。クリーンアップをスキップします。"
        )


def apply_edge_smoothing(obj: bpy.types.Object, angle: float = 0.785398) -> None:
    if obj and obj.type == "MESH":
        try:
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.faces_shade_smooth()
            bpy.ops.object.mode_set(mode="OBJECT")

            if hasattr(obj, "use_edge_angle"):
                obj.use_edge_angle = True
                obj.edge_angle = angle
                logger.debug(
                    f"{obj.name} にエッジスムージング (オブジェクトレベル) を適用"
                )
            elif hasattr(obj.data, "use_auto_smooth"):
                obj.data.use_auto_smooth = True
                obj.data.auto_smooth_angle = angle
                logger.debug(
                    f"{obj.name} にエッジスムージング (メッシュデータレベル) を適用"
                )
            else:
                logger.warning(
                    f"{obj.name}: オートスムース設定のための既知の属性が見つかりませんでした。"
                )
        except Exception as e:
            logger.error(f"{obj.name} のエッジスムージング適用に失敗: {e}")


def apply_subdivision_surface(
    obj: bpy.types.Object, levels: int, render_levels: Optional[int] = None
) -> None:
    if not (obj and obj.type == "MESH" and levels >= 0):
        logger.warning(
            f"オブジェクト '{obj.name if obj else 'None'}' はメッシュではないか、レベルが不正です。サブディビジョンをスキップします。"
        )
        return

    for mod in obj.modifiers:
        if mod.type == "SUBSURF":
            obj.modifiers.remove(mod)
            logger.debug(
                f"既存のSubdivisionモディファイア '{mod.name}' を削除しました。"
            )

    mod = obj.modifiers.new(name="Subdivision", type="SUBSURF")
    mod.levels = levels
    mod.render_levels = render_levels if render_levels is not None else levels
    logger.debug(
        f"'{obj.name}' に Subdivision モディファイアを追加 (ビューポート: {mod.levels}, レンダリング: {mod.render_levels})"
    )
