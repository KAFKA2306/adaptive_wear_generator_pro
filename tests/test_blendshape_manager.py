from tests import helpers
helpers.setup_addon_import_path()
import pytest
from adaptive_wear_generator_pro.core.blendshape_manager import transfer_blendshapes

def test_transfer_blendshapes_returns_true():
    result = transfer_blendshapes("source", "target")
    assert result is True