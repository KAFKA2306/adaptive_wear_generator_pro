from tests import helpers
helpers.setup_addon_import_path()
import bpy
import pytest
from adaptive_wear_generator_pro.ui.panel_rigging import register, unregister, AWGP_PT_RiggingPanel

def test_panel_rigging_register_unregister():
    try:
        register()
        assert AWGP_PT_RiggingPanel.bl_idname == "AWGP_PT_rigging_panel"
    finally:
        unregister()