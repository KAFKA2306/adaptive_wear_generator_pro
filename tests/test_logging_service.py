from tests import helpers
helpers.setup_addon_import_path()
import pytest # pylint: disable=unused-import
from adaptive_wear_generator_pro.services.logging_service import log_info, log_error

def test_log_info_returns_true():
    assert log_info("info") is True

def test_log_error_returns_true():
    assert log_error("error") is True