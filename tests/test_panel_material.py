from tests import helpers
helpers.setup_addon_import_path()
import bpy
import pytest
from adaptive_wear_generator_pro.ui.panel_material import register, unregister, AWGP_PT_MaterialPanel

def test_panel_material_register_unregister():
    try:
        register()
        assert AWGP_PT_MaterialPanel.bl_idname == "AWGP_PT_material_panel"
    finally:
        unregister()