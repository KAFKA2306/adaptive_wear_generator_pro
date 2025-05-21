from tests import helpers
helpers.setup_addon_import_path()
import pytest
from adaptive_wear_generator_pro.core.fit_engine import fit_mesh_to_body

def test_fit_mesh_to_body_returns_true():
    # ダミーのオブジェクトを渡したとしても、True を返す
    result = fit_mesh_to_body("dummy_garment", "dummy_body")
    assert result is True