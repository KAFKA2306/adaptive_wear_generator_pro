from tests import helpers
helpers.setup_addon_import_path()
from adaptive_wear_generator_pro.core.blendshape_manager import load_blendshape_maps

def test_load_blendshape_maps_returns_list():
    maps = load_blendshape_maps()
    assert isinstance(maps, list)