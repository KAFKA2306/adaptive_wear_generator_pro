import bpy
from .panel_main import AWG_PT_MainPanel
from .panel_material import AWGP_PT_MaterialPanel
from .panel_export import AWGP_PT_ExportPanel

def register():
    bpy.utils.register_class(AWG_PT_MainPanel)
    bpy.utils.register_class(AWGP_PT_MaterialPanel)
    bpy.utils.register_class(AWGP_PT_ExportPanel)

def unregister():
    bpy.utils.unregister_class(AWGP_PT_ExportPanel)
    bpy.utils.unregister_class(AWGP_PT_MaterialPanel)
    bpy.utils.unregister_class(AWG_PT_MainPanel)