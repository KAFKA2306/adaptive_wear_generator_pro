from bpy.types import Panel


class AWG_PT_MainPanel(Panel):
    """AdaptiveWear Generator Pro メインパネル（最高品質版）"""

    bl_label = "AdaptiveWear Generator Pro"
    bl_idname = "AWG_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AdaptiveWear"

    def draw(self, context):
        layout = self.layout

        # プロパティ存在確認
        if not hasattr(context.scene, "adaptive_wear_generator_pro"):
            self._draw_error_state(layout)
            return

        props = context.scene.adaptive_wear_generator_pro

        # ヘッダー描画
        self._draw_header(layout)

        # 基本設定描画
        self._draw_basic_settings(layout, props)

        # 素体情報描画
        if props.base_body:
            self._draw_body_info(layout, props)

        # 詳細設定描画
        if props.wear_type != "NONE":
            self._draw_advanced_settings(layout, props)

        # 生成ボタン描画
        self._draw_generation_section(layout, props)

        # フッター描画
        self._draw_footer(layout)

    def _draw_error_state(self, layout):
        """エラー状態の描画"""
        error_box = layout.box()
        error_box.label(text="アドオンエラー", icon="ERROR")
        error_box.label(text="アドオン再インストールが必要")
        error_box.separator()
        error_box.operator("wm.console_toggle", text="コンソール確認", icon="CONSOLE")

    def _draw_header(self, layout):
        """ヘッダー描画"""
        header_box = layout.box()
        header_row = header_box.row()
        header_row.label(text="AI駆動衣装生成 v4.0", icon="MESH_CUBE")
        header_row.operator(
            "wm.url_open", text="", icon="HELP"
        ).url = "https://github.com/adaptivewear/docs"

    def _draw_basic_settings(self, layout, props):
        """基本設定描画"""
        layout.separator()
        main_box = layout.box()
        main_box.label(text="基本設定", icon="SETTINGS")

        # 素体選択
        main_box.prop(props, "base_body")

        # 衣装タイプ選択
        main_box.prop(props, "wear_type")

        # 品質レベル選択
        main_box.prop(props, "quality_level")

    def _draw_body_info(self, layout, props):
        """素体情報描画"""
        info_box = layout.box()
        info_box.label(text="素体情報", icon="INFO")
        info_col = info_box.column(align=True)

        # 基本情報
        vertex_count = len(props.base_body.data.vertices)
        info_col.label(text=f"名前: {props.base_body.name}")
        info_col.label(text=f"頂点数: {vertex_count:,}")

        # シェイプキー情報
        if props.base_body.data.shape_keys:
            shapekey_count = len(props.base_body.data.shape_keys.key_blocks)
            info_col.label(
                text=f"シェイプキー: {shapekey_count}個", icon="SHAPEKEY_DATA"
            )

        # 頂点グループ情報
        vgroup_count = len(props.base_body.vertex_groups)
        info_col.label(text=f"頂点グループ: {vgroup_count}個", icon="GROUP_VERTEX")

        # アーマチュア情報
        armature = self._find_armature(props.base_body)
        if armature:
            bone_count = len(armature.data.bones)
            info_col.label(
                text=f"アーマチュア: {armature.name} ({bone_count}ボーン)",
                icon="ARMATURE_DATA",
            )

        # 対応する頂点グループ表示
        if props.wear_type != "NONE":
            self._draw_target_groups(info_box, props)

        # 診断ボタン
        info_box.separator()
        info_box.operator("awgp.diagnose_bones", text="詳細診断実行", icon="ZOOM_ALL")

    def _draw_advanced_settings(self, layout, props):
        """詳細設定描画"""
        layout.separator()
        settings_box = layout.box()
        settings_box.label(text="詳細設定", icon="MODIFIER")

        # 基本設定
        basic_col = settings_box.column(align=True)
        basic_col.prop(props, "tight_fit")
        basic_col.prop(props, "thickness")

        # 頂点グループ設定
        settings_box.separator()
        vg_col = settings_box.column(align=True)
        vg_col.prop(props, "use_vertex_groups")
        if props.use_vertex_groups:
            vg_col.prop(props, "min_weight")

        # シェイプキー設定
        if props.base_body and props.base_body.data.shape_keys:
            settings_box.separator()
            sk_col = settings_box.column(align=True)
            sk_col.prop(props, "preserve_shapekeys")

        # 高度な設定
        if props.quality_level in ["HIGH", "ULTRA"]:
            self._draw_quality_settings(settings_box, props)

        # 衣装タイプ別設定
        self._draw_type_specific_settings(settings_box, props)

    def _draw_quality_settings(self, parent, props):
        """品質別設定描画"""
        parent.separator()
        advanced_col = parent.column(align=True)
        advanced_col.label(text="高度な設定:", icon="EXPERIMENTAL")
        advanced_col.prop(props, "enable_edge_smoothing")
        advanced_col.prop(props, "progressive_fitting")

        if props.quality_level == "ULTRA":
            advanced_col.prop(props, "enable_cloth_sim")

    def _draw_type_specific_settings(self, parent, props):
        """衣装タイプ別設定描画"""
        if props.wear_type == "SOCKS":
            parent.separator()
            sock_col = parent.column(align=True)
            sock_col.label(text="靴下設定:", icon="MOD_LENGTH")
            sock_col.prop(props, "sock_length")

        elif props.wear_type == "GLOVES":
            parent.separator()
            glove_col = parent.column(align=True)
            glove_col.label(text="手袋設定:", icon="HAND")
            glove_col.prop(props, "glove_fingers")

    def _draw_generation_section(self, layout, props):
        """生成セクション描画"""
        layout.separator()

        can_generate = props.base_body is not None and props.wear_type != "NONE"

        if not can_generate:
            self._draw_generation_warnings(layout, props)
        else:
            self._draw_generation_button(layout, props)

    def _draw_generation_warnings(self, layout, props):
        """生成警告描画"""
        warning_box = layout.box()
        warning_box.label(text="設定を完了してください", icon="INFO")

        if not props.base_body:
            warning_box.label(text="• 素体メッシュを選択", icon="BLANK1")
        if props.wear_type == "NONE":
            warning_box.label(text="• 衣装タイプを選択", icon="BLANK1")

    def _draw_generation_button(self, layout, props):
        """生成ボタン描画"""
        gen_box = layout.box()

        # 品質レベル別の説明
        quality_descriptions = {
            "FIXED": "安全モード（推奨）",
            "MEDIUM": "標準品質（推奨）",
            "HIGH": "高品質（エッジスムージング）",
            "ULTRA": "最高品質（クロスシミュレーション）",
        }

        description = quality_descriptions.get(props.quality_level, "")
        if description:
            gen_box.label(text=f"品質: {description}", icon="INFO")

        # 処理時間の予想
        time_estimates = {
            "FIXED": "処理時間: ~3秒",
            "MEDIUM": "処理時間: ~5秒",
            "HIGH": "処理時間: ~15秒",
            "ULTRA": "処理時間: ~30秒",
        }

        time_estimate = time_estimates.get(props.quality_level, "")
        if time_estimate:
            gen_box.label(text=time_estimate, icon="TIME")

        # メイン生成ボタン
        gen_box.separator()
        gen_row = gen_box.row()
        gen_row.scale_y = 2.0

        button_text = f"Generate {props.wear_type}"
        if props.quality_level == "ULTRA":
            button_text += " (最高品質)"

        gen_row.operator("awgp.generate_wear", text=button_text, icon="PLAY")

    def _draw_footer(self, layout):
        """フッター描画"""
        layout.separator()
        footer_box = layout.box()
        footer_col = footer_box.column(align=True)
        footer_col.scale_y = 0.8
        footer_col.label(text="AdaptiveWear Generator Pro v4.0.0")
        footer_col.label(text="© 2025 AdaptiveWear Team")

        # リンクボタン
        footer_row = footer_col.row(align=True)
        footer_row.operator(
            "wm.url_open", text="GitHub", icon="URL"
        ).url = "https://github.com/adaptivewear"
        footer_row.operator(
            "wm.url_open", text="Docs", icon="HELP"
        ).url = "https://adaptivewear.readthedocs.io"
        footer_row.operator(
            "wm.url_open", text="Discord", icon="COMMUNITY"
        ).url = "https://discord.gg/adaptivewear"

    def _draw_target_groups(self, parent, props):
        """対象グループ表示"""
        from . import core

        try:
            target_groups = core.SafeVertexGroupManager.find_matching_groups_safe(
                props.base_body, props.wear_type
            )

            if target_groups:
                parent.separator()
                parent.label(
                    text=f"対象グループ ({props.wear_type}):", icon="CHECKMARK"
                )

                group_col = parent.column(align=True)
                for group in target_groups[:5]:  # 最大5個まで表示
                    group_col.label(text=f" • {group}")

                if len(target_groups) > 5:
                    group_col.label(text=f" ...他{len(target_groups) - 5}個")
            else:
                parent.label(text="対象グループなし", icon="ERROR")

        except Exception as e:
            parent.label(text=f"グループ検索エラー: {str(e)}", icon="ERROR")

    def _find_armature(self, obj):
        """アーマチュア検索"""
        for modifier in obj.modifiers:
            if modifier.type == "ARMATURE" and modifier.object:
                return modifier.object
        return None


# =============================================================================
# エクスポート定義
# =============================================================================
__all__ = ["AWG_PT_MainPanel"]
