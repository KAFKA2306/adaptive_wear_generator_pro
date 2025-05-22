import bpy

class AWGP_PT_ExportPanel(bpy.types.Panel):
    bl_label = "Export (MVP)"
    bl_idname = "AWGP_PT_export_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AdaptiveWear'

    def draw(self, context):
        layout = self.layout
        layout.label(text="エクスポートパネル（未実装）")

def register():
    try:
        bpy.utils.unregister_class(AWGP_PT_ExportPanel)
    except RuntimeError:
        pass
    bpy.utils.register_class(AWGP_PT_ExportPanel)

def unregister():
    bpy.utils.unregister_class(AWGP_PT_ExportPanel)