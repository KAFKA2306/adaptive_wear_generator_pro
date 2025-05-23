import bpy
from ..services import logging_service
from . import weight_transfer

def apply_rigging(garment_obj, base_obj, base_armature_obj):
    """
    生成された衣装メッシュに素体のボーン構造をコピーし、リギングを設定する
    """
    if garment_obj is None or garment_obj.type != 'MESH':
        logging_service.log_error("有効な衣装オブジェクトが指定されていません")
        return False

    if base_obj is None or base_obj.type != 'MESH':
        logging_service.log_error("有効な素体メッシュオブジェクトが指定されていません")
        return False

    if base_armature_obj is None or base_armature_obj.type != 'ARMATURE':
        logging_service.log_error("有効な素体アーマチュアオブジェクトが指定されていません")
        return False

    logging_service.log_info(f"リギング処理を開始します (衣装: {garment_obj.name}, 素体: {base_obj.name}, アーマチュア: {base_armature_obj.name})")

    try:
        # 既存のArmatureモディファイアを削除
        remove_existing_armature_modifiers(garment_obj)
        
        # Armatureモディファイアを追加
        armature_modifier = garment_obj.modifiers.new(name="Armature", type='ARMATURE')
        armature_modifier.object = base_armature_obj
        armature_modifier.use_deform_preserve_volume = True
        
        # ウェイト転送処理
        if not weight_transfer.transfer_weights(base_obj, garment_obj):
            logging_service.log_error("ウェイト転送に失敗しました")
            return False
        
        # ブレンドシェイプ転送
        if not transfer_blend_shapes(base_obj, garment_obj):
            logging_service.log_warning("ブレンドシェイプ転送に失敗しました")
            # ブレンドシェイプは必須ではないため、警告のみで続行
        
        logging_service.log_info("リギング処理完了")
        return True

    except Exception as e:
        logging_service.log_error(f"リギング処理中にエラーが発生しました: {str(e)}")
        return False

def remove_existing_armature_modifiers(obj):
    """既存のArmatureモディファイアを削除"""
    modifiers_to_remove = [mod for mod in obj.modifiers if mod.type == 'ARMATURE']
    for modifier in modifiers_to_remove:
        obj.modifiers.remove(modifier)

def transfer_blend_shapes(base_obj, garment_obj):
    """ブレンドシェイプを転送"""
    try:
        if not base_obj.data.shape_keys:
            logging_service.log_info("素体オブジェクトにブレンドシェイプがありません。転送をスキップします。")
            return True
        
        logging_service.log_info("ブレンドシェイプ転送処理を開始します")
        
        # 現在のアクティブオブジェクトを保存
        original_active = bpy.context.view_layer.objects.active
        original_selected = bpy.context.selected_objects[:]
        
        # 衣装オブジェクトにベーシスシェイプキーを追加（まだない場合）
        if not garment_obj.data.shape_keys:
            garment_obj.shape_key_add(name='Basis')
        
        # オブジェクトを適切に選択・アクティブ化
        bpy.ops.object.select_all(action='DESELECT')
        garment_obj.select_set(True)
        bpy.context.view_layer.objects.active = garment_obj
        
        # Surface Deform モディファイアを使用してブレンドシェイプを転送
        surface_deform_modifier = garment_obj.modifiers.new(name="SurfaceDeform", type='SURFACE_DEFORM')
        surface_deform_modifier.target = base_obj
        
        # バインド処理
        bpy.ops.object.surfacedeform_bind(modifier=surface_deform_modifier.name)
        
        # モディファイアを適用
        bpy.ops.object.modifier_apply(modifier=surface_deform_modifier.name)
        
        # 選択状態を復元
        bpy.ops.object.select_all(action='DESELECT')
        for obj in original_selected:
            if obj.name in bpy.data.objects:
                obj.select_set(True)
        if original_active and original_active.name in bpy.data.objects:
            bpy.context.view_layer.objects.active = original_active
        
        logging_service.log_info("ブレンドシェイプ転送処理完了")
        return True
        
    except Exception as e:
        logging_service.log_error(f"ブレンドシェイプ転送中にエラーが発生しました: {str(e)}")
        return False
