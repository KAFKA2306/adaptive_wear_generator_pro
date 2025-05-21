import bpy

class AWGP_PT_BlendshapePanel(bpy.types.Panel):
    bl_label = "Blendshape (MVP)"
    bl_idname = "AWGP_PT_blendshape_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AdaptiveWear'

    def draw(self, context):
        layout = self.layout
        layout.label(text="ブレンドシェイプパネル（未実装）")

def register():
    bpy.utils.register_class(AWGP_PT_BlendshapePanel)

def unregister():
    bpy.utils.unregister_class(AWGP_PT_BlendshapePanel)