import bpy

class AWGP_PT_RiggingPanel(bpy.types.Panel):
    bl_label = "Rigging (MVP)"
    bl_idname = "AWGP_PT_rigging_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AdaptiveWear'

    def draw(self, context):
        layout = self.layout
        layout.label(text="リギングパネル（未実装）")

def register():
    bpy.utils.register_class(AWGP_PT_RiggingPanel)

def unregister():
    bpy.utils.unregister_class(AWGP_PT_RiggingPanel)