from tests import helpers
helpers.setup_addon_import_path()
import pytest
from adaptive_wear_generator_pro.ui.ui_utils import dummy_ui_helper

def test_dummy_ui_helper_returns_true():
    assert dummy_ui_helper() is True