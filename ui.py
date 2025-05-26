from bpy.types import Panel
import bpy


class AWG_PT_MainPanel(Panel):
    bl_label = "AdaptiveWear Generator Pro"
    bl_idname = "AWG_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AdaptiveWear"

    def draw(self, context):
        layout = self.layout

        if not hasattr(context.scene, "adaptive_wear_generator_pro"):
            self._draw_error_state(layout)
            return

        props = context.scene.adaptive_wear_generator_pro

        self._draw_header(layout)
        self._draw_basic_settings(layout, props)

        if props.base_body:
            self._draw_body_info(layout, props)

        if props.wear_type != "NONE":
            self._draw_advanced_settings(layout, props)

        self._draw_generation_section(layout, props)
        self._draw_footer(layout)

    def _draw_error_state(self, layout):
        error_box = layout.box()
        error_box.label(text="アドオンエラー", icon="ERROR")
        error_box.label(text="アドオン再インストールが必要")
        error_box.separator()
        error_box.operator("wm.console_toggle", text="コンソール確認", icon="CONSOLE")

    def _draw_header(self, layout):
        header_box = layout.box()
        header_row = header_box.row()
        header_row.label(text="AI駆動衣装生成 v4.0", icon="MESH_CUBE")

        help_row = header_box.row()
        help_row.scale_y = 0.8
        help_row.operator(
            "wm.url_open", text="📖 使用方法", icon="HELP"
        ).url = "https://github.com/adaptivewear/docs"

    def _draw_basic_settings(self, layout, props):
        layout.separator()
        main_box = layout.box()
        main_box.label(text="🔧 基本設定", icon="SETTINGS")

        body_row = main_box.row()
        body_row.prop(props, "base_body")

        if not props.base_body:
            warning_row = main_box.row()
            warning_row.alert = True
            warning_row.label(text="⚠ 素体メッシュを選択してください", icon="ERROR")

        main_box.prop(props, "wear_type")

        quality_row = main_box.row()
        quality_row.prop(props, "quality_level")

        if props.quality_level == "ULTIMATE":
            info_row = main_box.row()
            info_row.label(text="🚀 最高品質モード（AI駆動）", icon="INFO")

    def _draw_body_info(self, layout, props):
        info_box = layout.box()
        info_box.label(text="📊 素体情報", icon="INFO")

        info_col = info_box.column(align=True)

        vertex_count = len(props.base_body.data.vertices)
        face_count = len(props.base_body.data.polygons)

        info_col.label(text=f"名前: {props.base_body.name}")
        info_col.label(text=f"頂点数: {vertex_count:,}")
        info_col.label(text=f"面数: {face_count:,}")

        if vertex_count > 50000:
            warning_row = info_col.row()
            warning_row.alert = True
            warning_row.label(text="⚠ 高密度メッシュ（処理時間長）", icon="ERROR")
        elif vertex_count > 20000:
            info_col.label(text="ℹ 中密度メッシュ", icon="INFO")

        if props.base_body.data.shape_keys:
            shapekey_count = len(props.base_body.data.shape_keys.key_blocks)
            info_col.label(
                text=f"🔑 シェイプキー: {shapekey_count}個", icon="SHAPEKEY_DATA"
            )

        vgroup_count = len(props.base_body.vertex_groups)
        if vgroup_count > 0:
            info_col.label(
                text=f"👥 頂点グループ: {vgroup_count}個", icon="GROUP_VERTEX"
            )
        else:
            warning_row = info_col.row()
            warning_row.alert = True
            warning_row.label(text="⚠ 頂点グループなし", icon="ERROR")

        armature = self._find_armature(props.base_body)
        if armature:
            bone_count = len(armature.data.bones)
            info_col.label(
                text=f"🦴 アーマチュア: {armature.name} ({bone_count}ボーン)",
                icon="ARMATURE_DATA",
            )
        else:
            info_col.label(text="⚠ アーマチュアなし（リギング無効）", icon="ERROR")

        if props.wear_type != "NONE":
            self._draw_target_groups(info_box, props)

        info_box.separator()
        diag_row = info_box.row()
        diag_row.scale_y = 1.2
        diag_row.operator(
            "awgp.diagnose_bones", text="🔍 詳細診断実行", icon="ZOOM_ALL"
        )

    def _draw_advanced_settings(self, layout, props):
        layout.separator()
        settings_box = layout.box()
        settings_box.label(text="⚙️ 詳細設定", icon="MODIFIER")

        basic_section = settings_box.box()
        basic_section.label(text="基本設定:")

        basic_col = basic_section.column(align=True)
        basic_col.prop(props, "tight_fit")
        basic_col.prop(props, "thickness")

        if props.quality_level == "ULTIMATE":
            ai_section = settings_box.box()
            ai_section.label(text="🤖 AI設定:")

            ai_col = ai_section.column(align=True)
            ai_col.prop(props, "ai_quality_mode")

            if props.ai_quality_mode:
                ai_col.prop(props, "ai_threshold")
                ai_col.prop(props, "ai_thickness_multiplier")
                ai_col.prop(props, "ai_subdivision")

        quality_section = settings_box.box()
        quality_section.label(text="🎨 品質設定:")

        quality_col = quality_section.column(align=True)
        quality_col.prop(props, "enable_edge_smoothing")

        if props.quality_level in ["HIGH", "ULTIMATE"]:
            quality_col.prop(props, "progressive_fitting")

        if props.quality_level == "ULTIMATE":
            cloth_row = quality_col.row()
            cloth_row.prop(props, "enable_cloth_sim")
            if props.enable_cloth_sim:
                help_row = quality_col.row()
                help_row.scale_y = 0.8
                help_row.label(text="ℹ 物理シミュレーション有効", icon="INFO")

        self._draw_type_specific_settings(settings_box, props)

        compatibility_section = settings_box.box()
        compatibility_section.label(text="🔄 互換性設定:")

        compat_col = compatibility_section.column(align=True)
        compat_col.scale_y = 0.9
        compat_col.prop(props, "preserve_shapekeys")
        compat_col.prop(props, "use_vertex_groups")

        if props.use_vertex_groups:
            compat_col.prop(props, "min_weight")

    def _draw_type_specific_settings(self, parent, props):
        if props.wear_type == "SOCKS":
            parent.separator()
            sock_section = parent.box()
            sock_section.label(text="🧦 靴下設定:", icon="MOD_LENGTH")
            sock_section.prop(props, "sock_length")

            if props.sock_length < 0.3:
                sock_section.label(text="📏 アンクルソックス", icon="INFO")
            elif props.sock_length < 0.7:
                sock_section.label(text="📏 クルーソックス", icon="INFO")
            else:
                sock_section.label(text="📏 ハイソックス", icon="INFO")

        elif props.wear_type == "GLOVES":
            parent.separator()
            glove_section = parent.box()
            glove_section.label(text="🧤 手袋設定:", icon="HAND")
            glove_section.prop(props, "glove_fingers")

            if not props.glove_fingers:
                glove_section.label(text="✋ ミトンタイプ", icon="INFO")
            else:
                glove_section.label(text="🖐️ フィンガータイプ", icon="INFO")

        elif props.wear_type in ["T_SHIRT", "BRA"]:
            parent.separator()
            top_section = parent.box()
            top_section.label(text="👕 上衣設定:")
            top_section.label(text="📋 標準設定を使用", icon="CHECKMARK")

    def _draw_generation_section(self, layout, props):
        layout.separator()

        can_generate = props.base_body is not None and props.wear_type != "NONE"

        if not can_generate:
            self._draw_generation_warnings(layout, props)
        else:
            self._draw_generation_button(layout, props)

    def _draw_generation_warnings(self, layout, props):
        warning_box = layout.box()
        warning_box.alert = True
        warning_box.label(text="⚠️ 設定を完了してください", icon="INFO")

        requirements_col = warning_box.column(align=True)
        requirements_col.scale_y = 0.9

        if not props.base_body:
            req_row = requirements_col.row()
            req_row.label(text="❌ 素体メッシュを選択", icon="BLANK1")
        else:
            req_row = requirements_col.row()
            req_row.label(text="✅ 素体メッシュ選択済み", icon="BLANK1")

        if props.wear_type == "NONE":
            req_row = requirements_col.row()
            req_row.label(text="❌ 衣装タイプを選択", icon="BLANK1")
        else:
            req_row = requirements_col.row()
            req_row.label(text="✅ 衣装タイプ選択済み", icon="BLANK1")

    def _draw_generation_button(self, layout, props):
        gen_box = layout.box()

        quality_info = {
            "ULTIMATE": {
                "description": "🚀 AI最高品質モード",
                "time": "⏱️ 処理時間: ~30-60秒",
                "features": [
                    "AI駆動メッシュ生成",
                    "高度エッジスムージング",
                    "クロスシミュレーション",
                    "PBRマテリアル",
                ],
                "color": "INFO",
            },
            "STABLE": {
                "description": "🛡️ 安定モード",
                "time": "⏱️ 処理時間: ~10-20秒",
                "features": ["実績のある手法", "安定した結果", "エラー耐性"],
                "color": "NONE",
            },
            "HIGH": {
                "description": "⭐ 高品質モード",
                "time": "⏱️ 処理時間: ~15-30秒",
                "features": ["エッジスムージング", "高品質マテリアル"],
                "color": "NONE",
            },
            "MEDIUM": {
                "description": "📊 標準品質モード",
                "time": "⏱️ 処理時間: ~5-10秒",
                "features": ["基本品質", "高速処理"],
                "color": "NONE",
            },
        }

        info = quality_info.get(props.quality_level, quality_info["MEDIUM"])

        info_section = gen_box.box()
        info_row = info_section.row()
        info_row.label(text=info["description"], icon="SETTINGS")

        time_row = info_section.row()
        time_row.scale_y = 0.8
        time_row.label(text=info["time"], icon="TIME")

        if props.quality_level == "ULTIMATE":
            features_col = info_section.column(align=True)
            features_col.scale_y = 0.8
            for feature in info["features"]:
                features_col.label(text=f"• {feature}")

        if props.base_body and len(props.base_body.data.vertices) > 50000:
            warning_row = gen_box.row()
            warning_row.alert = True
            warning_row.label(
                text="⚠️ 高密度メッシュ - 処理時間が長くなります", icon="ERROR"
            )

        gen_box.separator()
        button_row = gen_box.row()
        button_row.scale_y = 2.5

        button_text = f"🎯 Generate {props.wear_type}"
        if props.quality_level == "ULTIMATE":
            button_text += " (AI最高品質)"

        generate_op = button_row.operator(
            "awgp.generate_wear", text=button_text, icon="PLAY"
        )

        options_row = gen_box.row(align=True)
        options_row.scale_y = 0.8

    def _draw_footer(self, layout):
        layout.separator()
        footer_box = layout.box()

        version_row = footer_box.row()
        version_row.scale_y = 0.9
        version_row.label(text="AdaptiveWear Generator Pro v4.0.0", icon="INFO")

        copyright_row = footer_box.row()
        copyright_row.scale_y = 0.8
        copyright_row.label(text="© 2025 AdaptiveWear Team")

        footer_box.separator()
        links_row = footer_box.row(align=True)
        links_row.scale_y = 0.9

        github_op = links_row.operator("wm.url_open", text="📁 GitHub", icon="URL")
        github_op.url = "https://github.com/adaptivewear"

        docs_op = links_row.operator("wm.url_open", text="📖 Docs", icon="HELP")
        docs_op.url = "https://adaptivewear.readthedocs.io"

        discord_op = links_row.operator(
            "wm.url_open", text="💬 Discord", icon="COMMUNITY"
        )
        discord_op.url = "https://discord.gg/adaptivewear"

        feedback_row = footer_box.row()
        feedback_row.scale_y = 0.8
        feedback_op = feedback_row.operator(
            "wm.url_open", text="💡 フィードバック送信", icon="URL"
        )
        feedback_op.url = "https://github.com/adaptivewear/feedback"

    def _draw_target_groups(self, parent, props):
        try:
            # 修正: 直接インポートではなく、core.pyからアクセス
            from . import core

            wear_type_mapping = {
                "PANTS": "hip",
                "T_SHIRT": "chest",
                "BRA": "chest",
                "SOCKS": "foot",
                "GLOVES": "hand",
            }

            group_type = wear_type_mapping.get(props.wear_type)
            if not group_type:
                return

            target_groups = core.find_vertex_groups_by_type(props.base_body, group_type)

            parent.separator()
            target_section = parent.box()

            if target_groups:
                target_section.label(
                    text=f"🎯 対象グループ ({props.wear_type}):", icon="CHECKMARK"
                )

                group_col = target_section.column(align=True)
                group_col.scale_y = 0.8

                for i, group in enumerate(target_groups[:5]):
                    group_col.label(text=f"  • {group.name}")

                if len(target_groups) > 5:
                    group_col.label(text=f"  ...他{len(target_groups) - 5}個")

                stats_row = target_section.row()
                stats_row.scale_y = 0.8
                stats_row.label(
                    text=f"📊 合計: {len(target_groups)}グループ", icon="INFO"
                )
            else:
                target_section.alert = True
                target_section.label(text="❌ 対象グループなし", icon="ERROR")

                suggestion_col = target_section.column(align=True)
                suggestion_col.scale_y = 0.8
                suggestion_col.label(text="💡 提案:")
                suggestion_col.label(text="  • 詳細診断を実行")
                suggestion_col.label(text="  • 頂点グループを確認")

        except Exception as e:
            parent.separator()
            error_section = parent.box()
            error_section.alert = True
            error_section.label(text="❌ グループ検索エラー", icon="ERROR")
            error_section.label(text=f"詳細: {str(e)}")

    def _find_armature(self, obj):
        if not obj or not obj.modifiers:
            return None

        for modifier in obj.modifiers:
            if modifier.type == "ARMATURE" and modifier.object:
                return modifier.object
        return None


class AWG_PT_AdvancedPanel(Panel):
    bl_label = "高度設定 & 診断"
    bl_idname = "AWG_PT_advanced_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AdaptiveWear"
    bl_parent_id = "AWG_PT_main_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        if not hasattr(context.scene, "adaptive_wear_generator_pro"):
            layout.label(text="プロパティが見つかりません", icon="ERROR")
            return

        props = context.scene.adaptive_wear_generator_pro

        if props.quality_level == "ULTIMATE":
            self._draw_ai_settings(layout, props)

        self._draw_debug_section(layout, props)
        self._draw_export_settings(layout, props)

    def _draw_ai_settings(self, layout, props):
        ai_box = layout.box()
        ai_box.label(text="🤖 AI詳細設定", icon="SETTINGS")

        threshold_col = ai_box.column(align=True)
        threshold_col.prop(props, "ai_threshold")

        if hasattr(props, "ai_hand_threshold"):
            threshold_col.prop(props, "ai_hand_threshold")
        if hasattr(props, "ai_bra_threshold"):
            threshold_col.prop(props, "ai_bra_threshold")
        if hasattr(props, "ai_tshirt_threshold"):
            threshold_col.prop(props, "ai_tshirt_threshold")

        ai_box.separator()

        multiplier_col = ai_box.column(align=True)
        multiplier_col.prop(props, "ai_thickness_multiplier")

        if hasattr(props, "ai_sock_multiplier"):
            multiplier_col.prop(props, "ai_sock_multiplier")

    def _draw_debug_section(self, layout, props):
        debug_box = layout.box()
        debug_box.label(text="🐛 デバッグ & 診断", icon="CONSOLE")

        diag_col = debug_box.column(align=True)
        diag_col.operator(
            "awgp.diagnose_bones", text="🔍 頂点グループ診断", icon="ZOOM_ALL"
        )
        diag_col.operator(
            "wm.console_toggle", text="📋 システムコンソール", icon="CONSOLE"
        )

    def _draw_export_settings(self, layout, props):
        export_box = layout.box()
        export_box.label(text="📤 エクスポート設定", icon="EXPORT")

        export_col = export_box.column(align=True)
        export_col.scale_y = 0.9
        export_col.label(text="🚧 開発中の機能:", icon="INFO")
        export_col.label(text="  • FBXエクスポート")
        export_col.label(text="  • OBJエクスポート")
        export_col.label(text="  • glTFエクスポート")


class AWG_PT_HelpPanel(Panel):
    bl_label = "ヘルプ & サポート"
    bl_idname = "AWG_PT_help_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AdaptiveWear"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout

        self._draw_quick_start(layout)
        self._draw_troubleshooting(layout)
        self._draw_resources(layout)

    def _draw_quick_start(self, layout):
        start_box = layout.box()
        start_box.label(text="🚀 クイックスタート", icon="PLAY")

        steps_col = start_box.column(align=True)
        steps_col.scale_y = 0.9

        steps = [
            "1️⃣ 素体メッシュを選択",
            "2️⃣ 衣装タイプを選択",
            "3️⃣ 品質レベルを設定",
            "4️⃣ Generateボタンをクリック",
        ]

        for step in steps:
            steps_col.label(text=step)

    def _draw_troubleshooting(self, layout):
        trouble_box = layout.box()
        trouble_box.label(text="🔧 トラブルシューティング", icon="QUESTION")

        trouble_col = trouble_box.column(align=True)
        trouble_col.scale_y = 0.9

        issues = [
            "❓ 生成が失敗する → 詳細診断を実行",
            "❓ 結果が不自然 → 品質レベルを変更",
            "❓ 処理が遅い → メッシュ密度を確認",
            "❓ エラーが発生 → コンソールを確認",
        ]

        for issue in issues:
            trouble_col.label(text=issue)

    def _draw_resources(self, layout):
        resource_box = layout.box()
        resource_box.label(text="📚 リソース", icon="URL")

        docs_row = resource_box.row()
        docs_op = docs_row.operator(
            "wm.url_open", text="📖 オンラインマニュアル", icon="HELP"
        )
        docs_op.url = "https://adaptivewear.readthedocs.io"

        tutorial_row = resource_box.row()
        tutorial_op = tutorial_row.operator(
            "wm.url_open", text="🎥 ビデオチュートリアル", icon="PLAY"
        )
        tutorial_op.url = "https://youtube.com/adaptivewear"

        community_row = resource_box.row()
        community_op = community_row.operator(
            "wm.url_open", text="💬 コミュニティサポート", icon="COMMUNITY"
        )
        community_op.url = "https://discord.gg/adaptivewear"


__all__ = ["AWG_PT_MainPanel", "AWG_PT_AdvancedPanel", "AWG_PT_HelpPanel"]
