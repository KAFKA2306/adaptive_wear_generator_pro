# ui/panel_main.py

import bpy
from bpy.types import Panel
from ..services import logging_service

logger = logging_service.get_addon_logger()


class AWG_PT_MainPanel(Panel):
    """AdaptiveWear Generator Pro メインパネル"""

    bl_label = "AdaptiveWear Generator"
    bl_idname = "AWG_PT_MainPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AdaptiveWear"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        logger.debug(f"MainPanel.draw() が呼び出されました。Context: {context}")

        # プロパティの安全なアクセス
        if not hasattr(scene, "adaptive_wear_generator_pro"):
            logger.error(
                "シーンプロパティ 'adaptive_wear_generator_pro' が見つかりません！"
            )
            layout.label(text="プロパティが見つかりません", icon="ERROR")
            return

        props = scene.adaptive_wear_generator_pro
        logger.debug(f"取得したプロパティオブジェクト: {props}, 型: {type(props)}")

        # 基本設定セクション
        self.draw_basic_settings(layout, props)

        # 衣装タイプ固有の設定
        self.draw_type_specific_settings(layout, props)

        # フィット設定セクション
        self.draw_fit_settings(layout, props)

        # 診断ツールセクション
        self.draw_diagnostic_tools(layout, props)

        # 生成ボタン
        self.draw_generate_button(layout, props)

    def draw_basic_settings(self, layout, props):
        """基本設定セクションを描画"""
        box = layout.box()
        box.label(text="基本設定", icon="OBJECT_DATA")

        row = box.row()
        row.prop(props, "base_body")

        row = box.row()
        row.prop(props, "wear_type")

    def draw_type_specific_settings(self, layout, props):
        """衣装タイプ固有の設定を描画"""
        wear_type = props.wear_type
        if wear_type == "NONE":
            return

        # 追加設定があるかチェック
        additional_props = self.get_additional_properties_for_wear_type(wear_type)
        if additional_props:
            box = layout.box()
            box.label(text="タイプ別設定", icon="SETTINGS")

            for prop_name in additional_props:
                if hasattr(props, prop_name):
                    box.prop(props, prop_name)

    def get_additional_properties_for_wear_type(self, wear_type):
        """衣装タイプに応じた追加プロパティリストを取得"""
        type_specific_props = {
            "SOCKS": ["sock_length"],
            "GLOVES": ["glove_fingers"],
        }
        return type_specific_props.get(wear_type, [])

    def draw_fit_settings(self, layout, props):
        """フィット設定セクションを描画"""
        box = layout.box()
        box.label(text="フィット設定", icon="MOD_CLOTH")

        row = box.row()
        row.prop(props, "tight_fit")

        row = box.row()
        row.prop(props, "thickness")

    def draw_diagnostic_tools(self, layout, props):
        """診断ツールセクションを描画"""
        box = layout.box()
        box.label(text="診断ツール", icon="TOOL_SETTINGS")

        row = box.row()
        row.operator(
            "awgp.diagnose_bones", text="ボーン・頂点グループ診断", icon="BONE_DATA"
        )

    def draw_generate_button(self, layout, props):
        """生成ボタンを描画"""
        layout.separator()

        row = layout.row(align=True)
        row.scale_y = 1.5

        # ボタンの有効/無効状態を制御
        is_valid = self.validate_settings(props)
        row.enabled = is_valid

        # ボタンテキストを動的に変更
        button_text = self.get_button_text(props, is_valid)

        # 正しいオペレーターIDに修正
        row.operator("awgp.generate_wear", text=button_text, icon="PLAY")

        # 検証エラーがある場合は警告を表示
        if not is_valid:
            self.draw_validation_warnings(layout, props)

    def validate_settings(self, props):
        """設定の検証"""
        if not props.base_body or props.base_body.type != "MESH":
            return False
        if props.wear_type == "NONE":
            return False
        return True

    def get_button_text(self, props, is_valid):
        """ボタンテキストを取得"""
        if not is_valid:
            if not props.base_body:
                return "素体を選択してください"
            if props.base_body and props.base_body.type != "MESH":
                return "素体がメッシュではありません"
            if props.wear_type == "NONE":
                return "衣装タイプを選択してください"
            return "設定を確認してください"

        wear_type = props.wear_type

        # 衣装タイプの表示名を取得
        try:
            if hasattr(props, "bl_rna") and hasattr(props.bl_rna, "properties"):
                enum_items = props.bl_rna.properties["wear_type"].enum_items
                if wear_type in enum_items:
                    type_name_display = enum_items[wear_type].name
                else:
                    type_name_display = wear_type
            else:
                type_name_display = wear_type
        except Exception as e:
            logger.warning(f"wear_type の表示名取得に失敗: {e}")
            type_name_display = wear_type

        return f"{type_name_display}を生成"

    def draw_validation_warnings(self, layout, props):
        """検証警告を表示"""
        if not props.base_body:
            layout.label(text="素体メッシュを選択してください", icon="ERROR")
        elif props.base_body.type != "MESH":
            layout.label(
                text="選択されたオブジェクトはメッシュではありません", icon="ERROR"
            )

        if props.wear_type == "NONE":
            layout.label(text="衣装タイプを選択してください", icon="ERROR")


# 登録用のクラスリスト
classes = (AWG_PT_MainPanel,)
