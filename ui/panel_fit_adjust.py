import bpy

class AWGP_PT_FitAdjustPanel(bpy.types.Panel):
    bl_label = "Fit Adjust (MVP)"
    bl_idname = "AWGP_PT_fit_adjust_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AdaptiveWear'

    def draw(self, _context):
        layout = self.layout
        layout.label(text="フィット感調整パネル（未実装）")

def register():
    bpy.utils.register_class(AWGP_PT_FitAdjustPanel)

def unregister():
    bpy.utils.unregister_class(AWGP_PT_FitAdjustPanel)