from tests import helpers
helpers.setup_addon_import_path()
import bpy
import pytest
from adaptive_wear_generator_pro.ui.panel_main import register, unregister, AWGP_PT_MainPanel

def test_panel_main_register_unregister():
    try:
        register()
        assert AWGP_PT_MainPanel.bl_idname == "AWGP_PT_main_panel"
    finally:
        unregister()