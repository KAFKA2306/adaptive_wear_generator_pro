import bpy

class AWGP_PT_StylePanel(bpy.types.Panel):
    bl_label = "Garment Style (MVP)"
    bl_idname = "AWGP_PT_style_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AdaptiveWear'

    def draw(self, _context):
        layout = self.layout
        layout.label(text="スタイル選択（未実装）")

def register():
    bpy.utils.register_class(AWGP_PT_StylePanel)

def unregister():
    bpy.utils.unregister_class(AWGP_PT_StylePanel)