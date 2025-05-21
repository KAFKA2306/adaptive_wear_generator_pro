from tests import helpers
helpers.setup_addon_import_path()
import pytest
from adaptive_wear_generator_pro.core.weight_transfer import transfer_weights

def test_transfer_weights_returns_true():
    result = transfer_weights("source", "target")
    assert result is True