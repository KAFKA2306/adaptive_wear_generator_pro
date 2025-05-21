from tests import helpers
helpers.setup_addon_import_path()
import bpy
import pytest
from adaptive_wear_generator_pro.ui.panel_style import register, unregister, AWGP_PT_StylePanel

def test_panel_style_register_unregister():
    try:
        register()
        assert AWGP_PT_StylePanel.bl_idname == "AWGP_PT_style_panel"
    finally:
        unregister()