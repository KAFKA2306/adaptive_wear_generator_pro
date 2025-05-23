import bpy
from ..services import logging_service


def apply_fitting(garment_obj, base_obj, fit_settings):
    """生成された衣装メッシュを素体メッシュにフィットさせる"""
    if garment_obj is None or garment_obj.type != "MESH":
        logging_service.log_error("有効な衣装オブジェクトが指定されていません")
        return False

    if base_obj is None or base_obj.type != "MESH":
        logging_service.log_error("有効な素体オブジェクトが指定されていません")
        return False

    logging_service.log_info(
        f"フィッティング処理を開始します (衣装: {garment_obj.name}, 素体: {base_obj.name})"
    )

    try:
        # 既存のShrinkwrapモディファイアを削除
        remove_existing_shrinkwrap_modifiers(garment_obj)

        # 現在のアクティブオブジェクトを保存
        original_active = bpy.context.view_layer.objects.active

        # 衣装オブジェクトをアクティブに設定
        bpy.context.view_layer.objects.active = garment_obj

        # Shrinkwrapモディファイアを追加
        shrinkwrap_modifier = garment_obj.modifiers.new(
            name="Shrinkwrap", type="SHRINKWRAP"
        )
        shrinkwrap_modifier.target = base_obj

        # フィット設定を反映
        configure_shrinkwrap_modifier(shrinkwrap_modifier, fit_settings)

        # モディファイアを適用（安全なコンテキストで）
        with bpy.context.temp_override(active_object=garment_obj):
            bpy.ops.object.modifier_apply(modifier=shrinkwrap_modifier.name)

        # 元のアクティブオブジェクトを復元
        if original_active:
            bpy.context.view_layer.objects.active = original_active

        logging_service.log_info("フィッティング処理完了")
        return True

    except Exception as e:
        logging_service.log_error(
            f"フィッティング処理中にエラーが発生しました: {str(e)}"
        )
        return False


def remove_existing_shrinkwrap_modifiers(obj):
    """既存のShrinkwrapモディファイアを削除"""
    modifiers_to_remove = [mod for mod in obj.modifiers if mod.type == "SHRINKWRAP"]
    for modifier in modifiers_to_remove:
        obj.modifiers.remove(modifier)


def configure_shrinkwrap_modifier(modifier, fit_settings):
    """Shrinkwrapモディファイアの設定"""
    if fit_settings.tight_fit:
        # 密着設定
        modifier.wrap_method = "PROJECT"
        modifier.use_project_x = True
        modifier.use_project_y = True
        modifier.use_project_z = True
        modifier.use_negative_direction = True
        modifier.use_positive_direction = True
        modifier.offset = 0.001  # 最小限のオフセット
    else:
        # 通常のフィット
        modifier.wrap_method = "NEAREST_SURFACEPOINT"
        modifier.offset = (
            fit_settings.thickness * 0.5
        )  # 厚みの半分をオフセットとして使用

    # 品質設定
    modifier.use_keep_above_surface = True
