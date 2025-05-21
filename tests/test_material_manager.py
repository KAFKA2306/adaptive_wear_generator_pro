from tests import helpers
helpers.setup_addon_import_path()
import bpy
import pytest
from adaptive_wear_generator_pro.core.material_manager import apply_basic_material

@pytest.mark.parametrize("dummy_obj", [None])
def test_apply_basic_material_returns_material(dummy_obj):
    # dummy_obj は None だが、エラーが出ないことを確認
    # テスト実行時には事前にオブジェクトを作成して渡すことを想定
    # ここでは例外処理が発生しないことだけを確認
    try:
        mat = apply_basic_material(bpy.data.objects.new("Dummy", bpy.data.meshes.new("Mesh")))
    except Exception as e:
        pytest.fail(f"apply_basic_material raised an exception: {e}")