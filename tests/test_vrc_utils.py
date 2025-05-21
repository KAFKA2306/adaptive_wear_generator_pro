from tests import helpers
helpers.setup_addon_import_path()
import pytest
from adaptive_wear_generator_pro.services.vrc_utils import dummy_vrc_helper

def test_dummy_vrc_helper_returns_true():
    assert dummy_vrc_helper() is True