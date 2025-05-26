import bpy
import logging
from . import core_properties
from . import core_operators

logger = logging.getLogger(__name__)


class AWG_PT_MainPanel(bpy.types.Panel):
    bl_label = "AdaptiveWear Generator Pro"
    bl_idname = "AWG_PT_MainPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AdaptiveWear"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene = context.scene
        awg_props = scene.adaptive_wear_generator_pro

        box = layout.box()
        box.label(text="基本設定", icon="SETTINGS")
        box.prop(awg_props, "base_body")
        box.prop(awg_props, "wear_type")
        box.prop(awg_props, "quality_level")

        layout.separator()

        generate_op = layout.operator(
            core_operators.AWGP_OT_GenerateWear.bl_idname,
            icon="OUTLINER_OB_GROUP_INSTANCE",
        )

        if not (awg_props.base_body is not None and awg_props.wear_type != "NONE"):
            generate_op = layout.operator(
                core_operators.AWGP_OT_GenerateWear.bl_idname,
                icon="OUTLINER_OB_GROUP_INSTANCE",
                text="Generate Wear (要設定)",
            )


class AWG_PT_AdvancedPanel(bpy.types.Panel):
    bl_label = "詳細設定"
    bl_idname = "AWG_PT_AdvancedPanel"
    bl_parent_id = "AWG_PT_MainPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AdaptiveWear"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        scene = context.scene
        awg_props = scene.adaptive_wear_generator_pro

        box = layout.box()
        box.label(text="フィッティング設定", icon="MOD_CLOTH")
        box.prop(awg_props, "tight_fit")
        box.prop(awg_props, "thickness")
        box.prop(awg_props, "progressive_fitting")

        layout.separator()

        box = layout.box()
        box.label(text="品質設定", icon="OUTLINER_OB_LIGHT")
        box.prop(awg_props, "enable_cloth_sim")
        box.prop(awg_props, "enable_edge_smoothing")
        box.prop(awg_props, "preserve_shapekeys")
        box.prop(awg_props, "use_vertex_groups")
        if awg_props.use_vertex_groups:
            box.prop(awg_props, "min_weight")

        layout.separator()

        box = layout.box()
        box.label(text="衣装別設定", icon="MOD_MESHDEFORM")

        if awg_props.wear_type == "SOCKS":
            box.prop(awg_props, "sock_length")

        if awg_props.wear_type == "GLOVES":
            box.prop(awg_props, "glove_fingers")

        if awg_props.wear_type == "SKIRT":
            box.prop(awg_props, "skirt_length")
            box.prop(awg_props, "pleat_count")
            box.prop(awg_props, "pleat_depth")

        layout.separator()

        box = layout.box()
        box.label(text="マテリアル設定", icon="MATERIAL")
        box.prop(awg_props, "use_text_material")
        if awg_props.use_text_material:
            box.prop(awg_props, "material_prompt")

        layout.separator()

        box = layout.box()
        box.label(text="AI詳細設定 (上級者向け)", icon="NODE")
        box.prop(awg_props, "ai_quality_mode")
        if awg_props.ai_quality_mode:
            box.prop(awg_props, "ai_threshold")
            box.prop(awg_props, "ai_subdivision")
            box.prop(awg_props, "ai_thickness_multiplier")
            box.prop(awg_props, "ai_hand_threshold")
            box.prop(awg_props, "ai_bra_threshold")
            box.prop(awg_props, "ai_tshirt_threshold")
            box.prop(awg_props, "ai_sock_multiplier")
            box.prop(awg_props, "ai_tight_offset")
            box.prop(awg_props, "ai_offset_multiplier")


class AWG_PT_HelpPanel(bpy.types.Panel):
    bl_label = "ヘルプ"
    bl_idname = "AWG_PT_HelpPanel"
    bl_parent_id = "AWG_PT_MainPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AdaptiveWear"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout

        layout.label(text="ドキュメント:", icon="FILE_TEXT")
        layout.operator(
            "wm.url_open", text="オンラインドキュメント", icon="INFO"
        ).url = "https://example.com/awg-pro-docs"

        layout.separator()

        addon_info = bpy.context.preferences.addons.get(__package__).bl_info
        layout.label(text=f"バージョン: {addon_info.get('version', 'N/A')}")
        layout.label(text=f"Blender対応バージョン: {addon_info.get('blender', 'N/A')}")

        layout.separator()

        layout.operator(
            core_operators.AWGP_OT_DiagnoseBones.bl_idname, icon="VIEW_PERSPECTIVE"
        )


registration_classes = [
    AWG_PT_MainPanel,
    AWG_PT_AdvancedPanel,
    AWG_PT_HelpPanel,
]


def register() -> None:
    for cls in registration_classes:
        try:
            bpy.utils.register_class(cls)
            logger.debug(f"UIクラス登録: {cls.__name__}")
        except Exception as e:
            logger.error(f"UIクラス登録失敗: {cls.__name__} - {e}")


def unregister() -> None:
    for cls in reversed(registration_classes):
        try:
            bpy.utils.unregister_class(cls)
            logger.debug(f"UIクラス登録解除: {cls.__name__}")
        except Exception as e:
            logger.error(f"UIクラス登録解除失敗: {cls.__name__} - {e}")
