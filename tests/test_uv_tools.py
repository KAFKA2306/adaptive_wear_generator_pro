from tests import helpers
helpers.setup_addon_import_path()
import pytest
from adaptive_wear_generator_pro.core.uv_tools import unwrap_uv

def test_unwrap_uv_returns_true():
    result = unwrap_uv("dummy_garment")
    assert result is True