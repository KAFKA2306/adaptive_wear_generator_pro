from tests import helpers
helpers.setup_addon_import_path()
import bpy
import pytest
from adaptive_wear_generator_pro.ui.panel_main import register, unregister, AWG_PT_MainPanel

def test_panel_main_register_unregister():
    try:
        register()
        assert AWG_PT_MainPanel.bl_idname == "AWG_PT_MainPanel"
    finally:
        unregister()