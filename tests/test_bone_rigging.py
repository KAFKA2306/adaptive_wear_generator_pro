from tests import helpers
helpers.setup_addon_import_path()
import pytest
from adaptive_wear_generator_pro.core.bone_rigging import rig_basic_garment

def test_rig_basic_garment_returns_true():
    result = rig_basic_garment("garment_obj", "armature_obj")
    assert result is True