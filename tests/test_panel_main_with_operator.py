from tests import helpers
helpers.setup_addon_import_path()
import bpy
import pytest
from adaptive_wear_generator_pro.ui.panel_main import register, unregister, AWGP_PT_MainPanel
from adaptive_wear_generator_pro.core.mesh_generator import AWGP_OT_GenerateGarment

def test_panel_main_and_operator_register_unregister():
    try:
        register()
        assert AWGP_PT_MainPanel.bl_idname == "AWGP_PT_main_panel"
        assert AWGP_OT_GenerateGarment.bl_idname == "awgp.generate_garment"
    finally:
        unregister()
