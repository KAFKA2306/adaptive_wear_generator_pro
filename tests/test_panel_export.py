from tests import helpers
helpers.setup_addon_import_path()
import bpy
import pytest
from adaptive_wear_generator_pro.ui.panel_export import register, unregister, AWGP_PT_ExportPanel

def test_panel_export_register_unregister():
    try:
        register()
        assert AWGP_PT_ExportPanel.bl_idname == "AWGP_PT_export_panel"
    finally:
        unregister()