from tests import helpers
helpers.setup_addon_import_path()
import unittest
from tests.helpers import BlenderTestCase, setup_module_path

# モジュールパス設定
setup_module_path()

class TestMeshGenerator(BlenderTestCase):
    def test_create_basic_garment(self):
        from adaptive_wear_generator_pro.core.mesh_generator import create_basic_garment_mesh
        obj = create_basic_garment_mesh(self.test_obj)
        self.assertIsNotNone(obj)
        self.assertEqual(obj.type, 'MESH')

    def test_find_vertex_group_by_keyword(self):
        from adaptive_wear_generator_pro.core.mesh_generator import find_vertex_group_by_keyword

        # 頂点グループ追加
        _vg1 = self.test_obj.vertex_groups.new(name="hand_L")
        _vg2 = self.test_obj.vertex_groups.new(name="hand_R")
        _vg3 = self.test_obj.vertex_groups.new(name="foot_L")

        # キーワード検索
        result = find_vertex_group_by_keyword(self.test_obj, ["hand"])
        self.assertEqual(len(result), 2)
        self.assertIn("hand_L", result)
        self.assertIn("hand_R", result)

if __name__ == "__main__":
    unittest.main()