from tests import helpers
helpers.setup_addon_import_path()
import bpy
import pytest
from adaptive_wear_generator_pro.ui.panel_fit_adjust import register, unregister, AWGP_PT_FitAdjustPanel

def test_panel_fit_adjust_register_unregister():
    try:
        register()
        assert AWGP_PT_FitAdjustPanel.bl_idname == "AWGP_PT_fit_adjust_panel"
    finally:
        unregister()