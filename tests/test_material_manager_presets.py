from tests import helpers
helpers.setup_addon_import_path()
import pytest
from adaptive_wear_generator_pro.core.material_manager import load_material_presets

def test_load_material_presets_returns_list():
    presets = load_material_presets()
    assert isinstance(presets, list)