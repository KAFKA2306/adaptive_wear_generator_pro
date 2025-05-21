import bpy

class AWGP_PT_MainPanel(bpy.types.Panel):
    bl_label = "AdaptiveWear Generator"
    bl_idname = "AWGP_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AdaptiveWear'

    def draw(self, context):
        layout = self.layout
        props = context.scene.adaptive_wear_props # シーンプロパティを取得

        # Blender 4.1新機能：レイアウトパネル
        header, panel = layout.panel("generate_options", default_closed=False)
        header.label(text="衣装生成オプション")

        if panel:
            col = panel.column()
            col.prop(props, "garment_type", text="衣装タイプ") # 衣装タイプドロップダウンを追加
            col.operator("awgp.generate_garment", text="基本衣装を生成")
            # 衣装タイプを選択して生成オペレーターを呼び出す
            generate_op = col.operator("awgp.generate_wear", text="生成")
            generate_op.garment_type = props.garment_type
            generate_op.fit_tightly = props.fit_tightly
            generate_op.thickness = props.thickness

            # パネル内にプロパティを表示
            box = col.box()
            box.label(text="フィット設定")
            box.prop(props, "fit_tightly", text="フィット感を密着させる")
            box.prop(props, "thickness", text="厚み")

class AWGP_PT_MaterialPanel(bpy.types.Panel):
    bl_label = "マテリアル設定"
    bl_idname = "AWGP_PT_material_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AdaptiveWear'
    bl_parent_id = "AWGP_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        # マテリアルプレビュー（Blender 4.1新機能活用）
        row = layout.row()
        row.template_ID_preview(context.active_object, "active_material",
                               new="material.new", rows=3, cols=8)

        # カラーピッカー
        if context.active_object and context.active_object.active_material:
            mat = context.active_object.active_material
            if mat.use_nodes:
                # ノードベースマテリアルのカラーを設定
                principled = mat.node_tree.nodes.get('Principled BSDF')
                if principled:
                    layout.prop(principled.inputs['Base Color'], "default_value", text="色")
                    layout.prop(principled.inputs['Alpha'], "default_value", text="不透明度")
def register():
    bpy.utils.register_class(AWGP_PT_MainPanel)
    bpy.utils.register_class(AWGP_PT_MaterialPanel)
    bpy.utils.register_class(AWGP_PT_ExportPanel)
    bpy.utils.register_class(AWGP_OT_ExportFBX)

def unregister():
    bpy.utils.unregister_class(AWGP_OT_ExportFBX)
    bpy.utils.unregister_class(AWGP_PT_ExportPanel)
    bpy.utils.unregister_class(AWGP_PT_MaterialPanel)
    bpy.utils.unregister_class(AWGP_PT_MainPanel)
class AWGP_PT_ExportPanel(bpy.types.Panel):
    bl_label = "エクスポート"
    bl_idname = "AWGP_PT_export_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AdaptiveWear'
    bl_parent_id = "AWGP_PT_main_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, _context): # context を _context に変更
        layout = self.layout
        col = layout.column(align=True)

        col.label(text="選択したオブジェクトをエクスポート:")
        col.operator("awgp.export_fbx", text="FBXとして保存")

class AWGP_OT_ExportFBX(bpy.types.Operator):
    bl_idname = "awgp.export_fbx"
    bl_label = "FBXエクスポート"
    bl_description = "選択した衣装をFBXとしてエクスポート"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="FBXファイルの保存先",
        default="//adaptive_wear.fbx",
        subtype='FILE_PATH'
    )

    def execute(self, context):
        obj = context.active_object
        if not obj:
            self.report({'ERROR'}, "オブジェクトが選択されていません")
            return {'CANCELLED'}

        from ..core.export_tools import export_to_fbx
        success = export_to_fbx(obj, self.filepath)

        if success:
            self.report({'INFO'}, f"FBXエクスポート成功: {self.filepath}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "FBXエクスポートに失敗しました")
            return {'CANCELLED'}

    def invoke(self, context, _event): # event を _event に変更
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# --- パネル ---
class UNDERWEAR_PT_Main(bpy.types.Panel):
    bl_label = "ミニマル下着生成"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "下着"

    def draw(self, context):
        props = context.scene.underwear_props
        layout = self.layout
        layout.prop_search(props, "base_body", bpy.data, "objects", text="素体")
        layout.operator("underwear.generate", text="パンツ生成")