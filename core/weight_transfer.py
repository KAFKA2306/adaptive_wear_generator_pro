import bpy
from ..services import logging_service


def transfer_weights(source_obj, target_obj):
    """素体オブジェクトから衣装オブジェクトへウェイト情報を転送する"""
    if source_obj is None or source_obj.type != "MESH":
        logging_service.log_error(
            "ウェイト転送元として有効な素体オブジェクトが指定されていません"
        )
        return False

    if target_obj is None or target_obj.type != "MESH":
        logging_service.log_error(
            "ウェイト転送先として有効な衣装オブジェクトが指定されていません"
        )
        return False

    logging_service.log_info(
        f"ウェイト転送処理を開始します (元: {source_obj.name}, 先: {target_obj.name})"
    )

    # 現在の状態を保存
    original_active_obj = bpy.context.view_layer.objects.active
    original_select_state = [obj for obj in bpy.context.selected_objects if obj]

    try:
        # ターゲットオブジェクトをアクティブにして選択
        bpy.ops.object.select_all(action="DESELECT")
        target_obj.select_set(True)
        bpy.context.view_layer.objects.active = target_obj

        # 既存のData Transferモディファイアを削除
        remove_existing_data_transfer_modifiers(target_obj)

        # Data Transferモディファイアを追加
        data_transfer_modifier = target_obj.modifiers.new(
            name="DataTransfer", type="DATA_TRANSFER"
        )
        data_transfer_modifier.object = source_obj

        # 頂点グループ転送の設定
        data_transfer_modifier.use_vert_data = True
        data_transfer_modifier.data_types_verts = {"VGROUP_WEIGHTS"}
        data_transfer_modifier.vert_mapping = "NEAREST"

        # 高品質設定
        data_transfer_modifier.layers_vgroup_select_src = "ALL"
        data_transfer_modifier.layers_vgroup_select_dst = "NAME"

        # モディファイアを適用（安全なコンテキストで）
        with bpy.context.temp_override(active_object=target_obj):
            bpy.ops.object.modifier_apply(modifier=data_transfer_modifier.name)

        logging_service.log_info("ウェイト転送処理完了")
        return True

    except Exception as e:
        logging_service.log_error(f"ウェイト転送中にエラーが発生しました: {str(e)}")
        return False

    finally:
        # 元の選択状態を復元
        try:
            bpy.ops.object.select_all(action="DESELECT")
            for obj in original_select_state:
                if obj and obj.name in bpy.data.objects:
                    obj.select_set(True)

            if original_active_obj and original_active_obj.name in bpy.data.objects:
                bpy.context.view_layer.objects.active = original_active_obj
            else:
                bpy.context.view_layer.objects.active = None

        except Exception as e:
            logging_service.log_warning(f"選択状態復元中に警告: {str(e)}")


def remove_existing_data_transfer_modifiers(obj):
    """既存のData Transferモディファイアを削除"""
    modifiers_to_remove = [mod for mod in obj.modifiers if mod.type == "DATA_TRANSFER"]
    for modifier in modifiers_to_remove:
        obj.modifiers.remove(modifier)
