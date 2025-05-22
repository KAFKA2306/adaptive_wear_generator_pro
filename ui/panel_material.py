import bpy

class AWGP_PT_MaterialPanel(bpy.types.Panel):
    bl_label = "Material Settings (MVP)"
    bl_idname = "AWGP_PT_material_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AdaptiveWear'

    def draw(self, _context):
        layout = self.layout
        layout.label(text="マテリアルパネル（未実装）")

def register():
    try:
        bpy.utils.unregister_class(AWGP_PT_MaterialPanel)
    except RuntimeError:
        pass
    bpy.utils.register_class(AWGP_PT_MaterialPanel)

def unregister():
    bpy.utils.unregister_class(AWGP_PT_MaterialPanel)