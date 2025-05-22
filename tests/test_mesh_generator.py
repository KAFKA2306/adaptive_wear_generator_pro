from tests import helpers
helpers.setup_addon_import_path()
import unittest
import bpy # 追加
from tests.helpers import BlenderTestCase, setup_module_path

# モジュールパス設定
setup_module_path()

class TestMeshGenerator(BlenderTestCase):
    def test_create_basic_garment(self): # Test name can remain, or be updated to reflect new function
        from adaptive_wear_generator_pro.core.mesh_generator import generate_initial_wear_mesh
        # generate_initial_wear_mesh expects a wear_type string and context
        # For a basic test, let's try generating "Pants"
        obj = None
        try:
            obj = generate_initial_wear_mesh("Pants", bpy.context)
            self.assertIsNotNone(obj, "generate_initial_wear_mesh should return an object for 'Pants'")
            self.assertEqual(obj.type, 'MESH', "Generated object should be a MESH")
            # Ensure the object is cleaned up if generated
            if obj and obj.name not in self.test_obj.name: # Avoid deleting the base test_obj
                 self._cleanup_generated_object(obj.name)
        except Exception as e:
            if obj and obj.name in bpy.data.objects and obj.name != self.test_obj.name:
                self._cleanup_generated_object(obj.name)
            self.fail(f"test_create_basic_garment (using generate_initial_wear_mesh) failed with {e}")

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

    def _cleanup_generated_object(self, obj_name):
        if obj_name and obj_name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[obj_name], do_unlink=True)
        
        # 関数内で生成される可能性のある一時オブジェクトも削除
        temp_prefixes = ("Temp_LeftLeg", "Temp_RightLeg", "Temp_Crotch",
                         "Temp_LeftCup", "Temp_RightCup", "Temp_Palm",
                         "Temp_Finger_", "Temp_Thumb", "Generated_Unknown_") # UnknownTypeのフォールバックも含む
        for obj in list(bpy.data.objects): # list() でコピーを作成してイテレート
            if any(obj.name.startswith(prefix) for prefix in temp_prefixes):
                 # BlenderTestCaseが作る self.test_obj とは異なることを確認 (もしあれば)
                if not hasattr(self, 'test_obj') or obj.name != self.test_obj.name:
                    bpy.data.objects.remove(obj, do_unlink=True)

    def test_generate_pants(self):
        from adaptive_wear_generator_pro.core.mesh_generator import generate_initial_wear_mesh
        obj = None
        try:
            obj = generate_initial_wear_mesh("Pants", bpy.context)
            self.assertIsNotNone(obj, "Pants mesh should be generated.")
            self.assertEqual(obj.name, "GeneratedPants")
            self.assertIsInstance(obj, bpy.types.Object)
            self.assertEqual(obj.type, 'MESH')
            self.assertIsNotNone(obj.data, "Pants mesh should have data.")
        finally:
            if obj: self._cleanup_generated_object(obj.name)

    def test_generate_bra(self):
        from adaptive_wear_generator_pro.core.mesh_generator import generate_initial_wear_mesh
        obj = None
        try:
            obj = generate_initial_wear_mesh("Bra", bpy.context)
            self.assertIsNotNone(obj, "Bra mesh should be generated.")
            self.assertEqual(obj.name, "GeneratedBra")
            self.assertIsInstance(obj, bpy.types.Object)
            self.assertEqual(obj.type, 'MESH')
            self.assertIsNotNone(obj.data, "Bra mesh should have data.")
        finally:
            if obj: self._cleanup_generated_object(obj.name)

    def test_generate_socks_default_length(self):
        from adaptive_wear_generator_pro.core.mesh_generator import generate_initial_wear_mesh
        obj = None
        try:
            obj = generate_initial_wear_mesh("Socks", bpy.context)
            self.assertIsNotNone(obj, "Socks mesh should be generated.")
            self.assertEqual(obj.name, "GeneratedSocks")
            self.assertIsInstance(obj, bpy.types.Object)
            self.assertEqual(obj.type, 'MESH')
            self.assertIsNotNone(obj.data, "Socks mesh should have data.")
            # デフォルトの長さを確認 (0.5)
            self.assertAlmostEqual(obj.dimensions[2], 0.5, delta=0.01, msg="Default sock length check")
        finally:
            if obj: self._cleanup_generated_object(obj.name)

    def test_generate_socks_custom_length(self):
        from adaptive_wear_generator_pro.core.mesh_generator import generate_initial_wear_mesh
        obj = None
        custom_length = 0.8
        try:
            obj = generate_initial_wear_mesh("Socks", bpy.context, additional_settings={"sock_length": custom_length})
            self.assertIsNotNone(obj, "Socks mesh with custom length should be generated.")
            self.assertEqual(obj.name, "GeneratedSocks")
            self.assertAlmostEqual(obj.dimensions[2], custom_length, delta=0.01, msg="Custom sock length check")
        finally:
            if obj: self._cleanup_generated_object(obj.name)

    def test_generate_gloves_mitten_default(self):
        from adaptive_wear_generator_pro.core.mesh_generator import generate_initial_wear_mesh
        obj = None
        try:
            obj = generate_initial_wear_mesh("Gloves", bpy.context) # default is glove_fingers=False
            self.assertIsNotNone(obj, "Mitten gloves mesh should be generated.")
            self.assertEqual(obj.name, "GeneratedGloves_Mitten")
            self.assertIsInstance(obj, bpy.types.Object)
            self.assertEqual(obj.type, 'MESH')
            self.assertIsNotNone(obj.data, "Mitten gloves mesh should have data.")
        finally:
            if obj: self._cleanup_generated_object(obj.name)

    def test_generate_gloves_with_fingers(self):
        from adaptive_wear_generator_pro.core.mesh_generator import generate_initial_wear_mesh
        obj_fingered = None
        obj_mitten_for_comparison = None
        try:
            obj_mitten_for_comparison = generate_initial_wear_mesh("Gloves", bpy.context, additional_settings={"glove_fingers": False})
            self.assertIsNotNone(obj_mitten_for_comparison)
            mitten_verts = len(obj_mitten_for_comparison.data.vertices)
            mitten_faces = len(obj_mitten_for_comparison.data.polygons)
            self._cleanup_generated_object(obj_mitten_for_comparison.name)
            obj_mitten_for_comparison = None # クリーンアップしたのでNoneに

            obj_fingered = generate_initial_wear_mesh("Gloves", bpy.context, additional_settings={"glove_fingers": True})
            self.assertIsNotNone(obj_fingered, "Fingered gloves mesh should be generated.")
            self.assertEqual(obj_fingered.name, "GeneratedGloves_Fingered")
            
            fingered_verts = len(obj_fingered.data.vertices)
            fingered_faces = len(obj_fingered.data.polygons)

            self.assertNotEqual(fingered_verts, mitten_verts, "Fingered gloves should have different vertex count than mitten.")
            self.assertNotEqual(fingered_faces, mitten_faces, "Fingered gloves should have different face count than mitten.")
        finally:
            if obj_fingered: self._cleanup_generated_object(obj_fingered.name)
            if obj_mitten_for_comparison: self._cleanup_generated_object(obj_mitten_for_comparison.name)


    def test_generate_gloves_mitten_explicit(self):
        from adaptive_wear_generator_pro.core.mesh_generator import generate_initial_wear_mesh
        obj = None
        try:
            obj = generate_initial_wear_mesh("Gloves", bpy.context, additional_settings={"glove_fingers": False})
            self.assertIsNotNone(obj, "Mitten gloves mesh (explicit) should be generated.")
            self.assertEqual(obj.name, "GeneratedGloves_Mitten")
        finally:
            if obj: self._cleanup_generated_object(obj.name)

    def test_generate_unknown_wear_type(self):
        from adaptive_wear_generator_pro.core.mesh_generator import generate_initial_wear_mesh
        # logging_service.py の実装によりロガー名が決まる。
        # ここでは、呼び出し元モジュール名がロガー名の一部として使われると仮定。
        # 実際のロガー名は 'adaptive_wear_generator_pro.services.logging_service' かもしれないし、
        # 'adaptive_wear_generator_pro.core.mesh_generator' かもしれない。
        # logging_service がルートロガーに直接書き込んでいる可能性もある。
        # ひとまず、関数内で使われている `log_warning` が属するモジュール名を試す。
        logger_name_candidate = "adaptive_wear_generator_pro.core.mesh_generator"
        # または、logging_service が公開しているロガー名
        # from adaptive_wear_generator_pro.services.logging_service import logger # 例
        # logger_name_candidate = logger.name

        obj = None
        try:
            with self.assertLogs(logger_name_candidate, level='WARNING') as cm:
                obj = generate_initial_wear_mesh("UnknownType", bpy.context)
            
            self.assertIsNotNone(obj, "Fallback mesh should be generated for unknown type.")
            # 関数は "Generated_Unknown_{wear_type}" という名前でオブジェクトを生成する
            self.assertEqual(obj.name, "Generated_Unknown_UnknownType")
            self.assertEqual(obj.type, 'MESH')
            
            self.assertTrue(any("未対応の wear_type: UnknownType" in log_msg for log_msg in cm.output),
                            f"Expected warning log not found. Logs: {cm.output}")
        finally:
            if obj: self._cleanup_generated_object(obj.name) # "Generated_Unknown_UnknownType" も削除対象

    def test_generate_with_invalid_additional_settings_key(self):
        from adaptive_wear_generator_pro.core.mesh_generator import generate_initial_wear_mesh
        obj = None
        try:
            obj = generate_initial_wear_mesh("Socks", bpy.context, additional_settings={"invalid_key": "some_value"})
            self.assertIsNotNone(obj, "Socks mesh should be generated even with invalid additional_settings key.")
            self.assertEqual(obj.name, "GeneratedSocks")
            self.assertAlmostEqual(obj.dimensions[2], 0.5, delta=0.01, msg="Default sock length with invalid key")
        finally:
            if obj: self._cleanup_generated_object(obj.name)

    def test_generate_socks_with_invalid_sock_length_value_type(self):
        from adaptive_wear_generator_pro.core.mesh_generator import generate_initial_wear_mesh
        obj = None
        logger_name_candidate = "adaptive_wear_generator_pro.core.mesh_generator"
        try:
            with self.assertLogs(logger_name_candidate, level='ERROR') as cm:
                obj = generate_initial_wear_mesh("Socks", bpy.context, additional_settings={"sock_length": "not_a_float"})
            
            self.assertIsNone(obj, "Mesh generation should fail and return None for invalid sock_length type.")
            self.assertTrue(any("generate_initial_wear_mesh でエラーが発生しました" in log_msg for log_msg in cm.output),
                            f"Expected error log not found. Logs: {cm.output}")
            # エラーメッセージの具体的な内容はBlenderのバージョンや内部実装に依存する可能性があるため、
            # "TypeError" や関連するキーワードが含まれているかで判断する方が堅牢かもしれない。
            # self.assertTrue(any("TypeError" in log_msg for log_msg in cm.output), "Expected TypeError in logs.")
        finally:
            if obj: self._cleanup_generated_object(obj.name) # objはNoneのはず

if __name__ == "__main__":
    unittest.main()