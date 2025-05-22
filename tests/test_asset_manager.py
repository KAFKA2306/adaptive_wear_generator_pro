from tests import helpers
helpers.setup_addon_import_path()
import pytest
from services.asset_manager import load_texture

def test_load_texture_returns_true():
    assert load_texture("dummy_path") is True