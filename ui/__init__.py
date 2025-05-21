import bpy
from .panel_main import AWGP_PT_MainPanel, AWGP_PT_MaterialPanel, AWGP_PT_ExportPanel

def register():
    bpy.utils.register_class(AWGP_PT_MainPanel)
    bpy.utils.register_class(AWGP_PT_MaterialPanel)
    bpy.utils.register_class(AWGP_PT_ExportPanel)

def unregister():
    bpy.utils.unregister_class(AWGP_PT_ExportPanel)
    bpy.utils.unregister_class(AWGP_PT_MaterialPanel)
    bpy.utils.unregister_class(AWGP_PT_MainPanel)