import bpy

class AWGP_PT_SettingsPanel(bpy.types.Panel):
    bl_label = "Settings (MVP)"
    bl_idname = "AWGP_PT_settings_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'AdaptiveWear'

    def draw(self, _context):
        layout = self.layout
        layout.label(text="設定項目（未実装）")

def register():
    bpy.utils.register_class(AWGP_PT_SettingsPanel)

def unregister():
    bpy.utils.unregister_class(AWGP_PT_SettingsPanel)