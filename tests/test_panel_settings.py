from tests import helpers
helpers.setup_addon_import_path()
import bpy  # noqa: F401
import pytest  # noqa: F401
from adaptive_wear_generator_pro.ui.panel_settings import register, unregister, AWGP_PT_SettingsPanel

def test_panel_settings_register_unregister():
    try:
        register()
        assert AWGP_PT_SettingsPanel.bl_idname == "AWGP_PT_settings_panel"
    finally:
        unregister()