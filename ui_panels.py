"""
AdaptiveWear Generator Pro UIパネル定義
サイドバーに表示される各種設定パネル
"""

import bpy
import logging
from . import core_properties
from . import core_operators

logger = logging.getLogger(__name__)

# メインパネル
class AWG_PT_MainPanel(bpy.types.Panel):
    """AdaptiveWear Generator Pro メインパネル"""
    bl_label = "AdaptiveWear Generator Pro"
    bl_idname = "AWG_PT_MainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AdaptiveWear"

    def draw(self, context: bpy.types.Context) -> None:
        """パネルUIの描画"""
        layout = self.layout
        scene = context.scene
        awg_props = scene.adaptive_wear_generator_pro

        # 基本設定
        box = layout.box()
        box.label(text="基本設定", icon='SETTINGS')
        box.prop(awg_props, "base_body")
        box.prop(awg_props, "wear_type")
        box.prop(awg_props, "quality_level")

        layout.separator()

        # 主要なオペレーターボタン
        # 素体メッシュが選択されていない場合はボタンを無効化
        generate_op = layout.operator(core_operators.AWGP_OT_GenerateWear.bl_idname, icon='OUTLINER_OB_GROUP_INSTANCE')
        generate_op.enabled = (awg_props.base_body is not None and awg_props.wear_type != 'NONE')


# 詳細設定パネル
class AWG_PT_AdvancedPanel(bpy.types.Panel):
    """AdaptiveWear Generator Pro 詳細設定パネル"""
    bl_label = "詳細設定"
    bl_idname = "AWG_PT_AdvancedPanel"
    bl_parent_id = "AWG_PT_MainPanel" # メインパネルの子として表示
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AdaptiveWear"
    bl_options = {'DEFAULT_CLOSED'} # デフォルトで閉じる

    def draw(self, context: bpy.types.Context) -> None:
        """パネルUIの描画"""
        layout = self.layout
        scene = context.scene
        awg_props = scene.adaptive_wear_generator_pro

        # フィッティング設定
        box = layout.box()
        box.label(text="フィッティング設定", icon='MOD_CLOTH')
        box.prop(awg_props, "tight_fit")
        box.prop(awg_props, "thickness")
        box.prop(awg_props, "progressive_fitting")

        layout.separator()

        # 品質設定
        box = layout.box()
        box.label(text="品質設定", icon='OUTLINER_OB_LIGHT')
        box.prop(awg_props, "enable_cloth_sim")
        box.prop(awg_props, "enable_edge_smoothing")
        box.prop(awg_props, "preserve_shapekeys")
        box.prop(awg_props, "use_vertex_groups")
        if awg_props.use_vertex_groups:
             box.prop(awg_props, "min_weight")

        layout.separator()

        # 衣装別設定
        box = layout.box()
        box.label(text="衣装別設定", icon='MOD_MESHDEFORM')
        # 靴下設定
        if awg_props.wear_type == 'SOCKS':
            box.prop(awg_props, "sock_length")
        # 手袋設定
        if awg_props.wear_type == 'GLOVES':
            box.prop(awg_props, "glove_fingers")
        # スカート設定
        if awg_props.wear_type == 'SKIRT':
            box.prop(awg_props, "skirt_length")
            box.prop(awg_props, "pleat_count")
            box.prop(awg_props, "pleat_depth")

        layout.separator()

        # マテリアル設定
        box = layout.box()
        box.label(text="マテリアル設定", icon='MATERIAL')
        box.prop(awg_props, "use_text_material")
        if awg_props.use_text_material:
            box.prop(awg_props, "material_prompt")

        layout.separator()

        # AI詳細設定
        box = layout.box()
        box.label(text="AI詳細設定 (上級者向け)", icon='NODE')
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


# ヘルプパネル
class AWG_PT_HelpPanel(bpy.types.Panel):
    """AdaptiveWear Generator Pro ヘルプパネル"""
    bl_label = "ヘルプ"
    bl_idname = "AWG_PT_HelpPanel"
    bl_parent_id = "AWG_PT_MainPanel" # メインパネルの子として表示
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "AdaptiveWear"
    bl_options = {'DEFAULT_CLOSED'} # デフォルトで閉じる

    def draw(self, context: bpy.types.Context) -> None:
        """パネルUIの描画"""
        layout = self.layout
        # scene = context.scene # 未使用
        # awg_props = scene.adaptive_wear_generator_pro # 未使用

        # ドキュメントURL
        layout.label(text="ドキュメント:", icon='FILE_TEXT')
        layout.operator("wm.url_open", text="オンラインドキュメント", icon='INFO').url = "https://example.com/awg-pro-docs" # 仮のURL

        layout.separator()

        # バージョン情報 (bl_info から取得)
        addon_info = bpy.context.preferences.addons.get(__package__).bl_info
        layout.label(text=f"バージョン: {addon_info.get('version', 'N/A')}")
        layout.label(text=f"Blender対応バージョン: {addon_info.get('blender', 'N/A')}")

        layout.separator()

        # 診断ボタン
        layout.operator(core_operators.AWGP_OT_DiagnoseBones.bl_idname, icon='VIEW_PERSPECTIVE')


# 登録クラス一覧
registration_classes = [
    AWG_PT_MainPanel,
    AWG_PT_AdvancedPanel,
    AWG_PT_HelpPanel,
]

# 登録関数
def register() -> None:
    """UIパネルクラスを登録"""
    for cls in registration_classes:
        try:
            bpy.utils.register_class(cls)
            logger.debug(f"UIクラス登録: {cls.__name__}")
        except Exception as e:
            logger.error(f"UIクラス登録失敗: {cls.__name__} - {e}")


# 登録解除関数
def unregister() -> None:
    """UIパネルクラスの登録を解除"""
    for cls in reversed(registration_classes):
        try:
            bpy.utils.unregister_class(cls)
            logger.debug(f"UIクラス登録解除: {cls.__name__}")
        except Exception as e:
            logger.error(f"UIクラス登録解除失敗: {cls.__name__} - {e}")