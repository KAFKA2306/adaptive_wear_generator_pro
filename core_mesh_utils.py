"""
メッシュ操作ユーティリティ関数群
"""

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
            # Blender 4.x対応の修正
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.faces_shade_smooth()
            bpy.ops.object.mode_set(mode="OBJECT")

            # Blender 4.0以降のオートスムース設定
            # メッシュデータに直接 auto_smooth_angle を設定 (Blender 4.1では変更の可能性あり)
            # オブジェクトレベルでのスムージング設定を試みる
            if hasattr(obj, 'use_edge_angle'): # Blender 4.1+ の可能性
                 obj.use_edge_angle = True
                 obj.edge_angle = angle
                 logger.debug(f"{obj.name} にエッジスムージング (オブジェクトレベル) を適用")
            elif hasattr(obj.data, 'use_auto_smooth'): # Blender 4.0 以前の可能性
                obj.data.use_auto_smooth = True # オートスムースを有効化
                obj.data.auto_smooth_angle = angle # 角度を設定
                logger.debug(f"{obj.name} にエッジスムージング (メッシュデータレベル) を適用")
            else:
                logger.warning(f"{obj.name}: オートスムース設定のための既知の属性が見つかりませんでした。")

        except Exception as e:
            logger.error(f"{obj.name} のエッジスムージング適用に失敗: {e}")


def apply_fitting(
    garment: bpy.types.Object, base_body: bpy.types.Object, props
) -> None:
    """フィッティング処理を適用"""
    if not (garment and base_body):
        logger.warning("フィッティング適用に必要なオブジェクトが不足")
        return

    try:
        # 基本的なフィッティング処理
        if props.tight_fit:
            # 密着フィット処理
            offset_distance = props.ai_tight_offset * props.ai_offset_multiplier
        else:
            # 通常フィット処理
            offset_distance = props.thickness

        # メッシュ調整処理
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
    """重複頂点の修正"""
    if obj and obj.type == "MESH":
        # cleanup_meshに依存しているため、cleanup_meshもこのファイルに移動させるか、インポートが必要
        # 今回はcleanup_meshも移動させるため、直接呼び出す
        cleanup_mesh(obj)


def cleanup_mesh(obj: bpy.types.Object, merge_distance: float = 0.0001) -> None:
    """
    メッシュのクリーンアップ（重複頂点除去など）を行います。
    Args:
        obj: クリーンアップするメッシュオブジェクト。
        merge_distance: 重複と見なす頂点間の最大距離。
    """
    if obj and obj.type == "MESH":
        # select_single_objectに依存しているため、これも移動させるかインポートが必要
        # 今回はcore_blender_utils.pyに移動させるため、後でインポートを追加する必要がある
        # 一旦コメントアウトまたは仮の関数呼び出しとしておく
        # select_single_object(obj) # TODO: core_blender_utils からインポート

        # 暫定的に直接Blender APIを呼び出すか、select_single_objectをここに含める
        # 今回はselect_single_objectもメッシュ操作と関連が深いため、一時的にここに含める
        # 最終的にはcore_blender_utilsに移動し、ここからインポートする設計が良いだろう

        # select_single_object関数の定義を一時的に追加 (後で削除しインポートに置き換え)
        def select_single_object(obj: bpy.types.Object) -> None:
            """
            指定されたオブジェクトのみを選択状態にし、アクティブオブジェクトに設定します。
            Args:
                obj: 選択・アクティブ化するオブジェクト。
            """
            if obj:
                bpy.ops.object.select_all(action="DESELECT")
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj
                logger.debug(f"オブジェクト '{obj.name}' を選択しアクティブに設定しました。")
            else:
                logger.warning("選択・アクティブ化するオブジェクトが指定されていません。")
        # 一時的な定義ここまで

        select_single_object(obj) # 一時的な定義を使用

        try:
            bpy.ops.object.mode_set(mode="EDIT")
            # 重複頂点を除去
            bpy.ops.mesh.remove_doubles(threshold=merge_distance)
            bpy.ops.object.mode_set(mode="OBJECT")
            logger.debug(
                f"'{obj.name}' のメッシュクリーンアップ (重複頂点除去) を実行しました。"
            )
        except RuntimeError as e:
            logger.error(f"'{obj.name}' のメッシュクリーンアップに失敗しました: {e}")
            # エラー発生時はオブジェクトモードに戻す
            try:
                bpy.ops.object.mode_set(mode="OBJECT")
            except RuntimeError:
                pass  # モード変更できない場合もある
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
    """
    オブジェクトにサブディビジョンサーフェスモディファイアを適用します。
    Args:
        obj: モディファイアを適用するオブジェクト。
        levels: ビューポートでのサブディビジョンレベル。
        render_levels: レンダリング時のサブディビジョンレベル。指定しない場合は levels と同じ。
    """
    if not (obj and obj.type == "MESH" and levels >= 0):
        logger.warning(
            f"オブジェクト '{obj.name if obj else 'None'}' はメッシュではないか、レベルが不正です。サブディビジョンをスキップします。"
        )
        return

    # 既存のSubdivisionモディファイアがあれば削除
    for mod in obj.modifiers:
        if mod.type == "SUBSURF":
            obj.modifiers.remove(mod)
            logger.debug(
                f"既存のSubdivisionモディファイア '{mod.name}' を削除しました。"
            )

    # 新しいSubdivisionモディファイアを追加
    mod = obj.modifiers.new(name="Subdivision", type="SUBSURF")
    mod.levels = levels
    mod.render_levels = render_levels if render_levels is not None else levels
    logger.debug(
        f"'{obj.name}' に Subdivision モディファイアを追加 (ビューポート: {mod.levels}, レンダリング: {mod.render_levels})"
    )