from tests import helpers
helpers.setup_addon_import_path()
import pytest
# from adaptive_wear_generator_pro.core.fit_engine import load_fit_profiles

@pytest.mark.skip("load_fit_profiles is not implemented")
def test_load_fit_profiles_returns_list():
    profiles = load_fit_profiles()
    assert isinstance(profiles, list)