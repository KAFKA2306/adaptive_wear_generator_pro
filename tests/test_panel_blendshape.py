from tests import helpers
helpers.setup_addon_import_path()
import bpy
import pytest
from adaptive_wear_generator_pro.ui.panel_blendshape import register, unregister, AWGP_PT_BlendshapePanel

def test_panel_blendshape_register_unregister():
    try:
        register()
        assert AWGP_PT_BlendshapePanel.bl_idname == "AWGP_PT_blendshape_panel"
    finally:
        unregister()