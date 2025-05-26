import bpy
import bmesh
import mathutils
from mathutils import Vector
from typing import Optional, Dict, Any, Tuple, List
import logging

logger = logging.getLogger(__name__)


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

        def select_single_object(obj: bpy.types.Object) -> None:
            if obj:
                bpy.ops.object.select_all(action="DESELECT")
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj
                logger.debug(
                    f"オブジェクト '{obj.name}' を選択しアクティブに設定しました。"
                )
            else:
                logger.warning(
                    "選択・アクティブ化するオブジェクトが指定されていません。"
                )

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
