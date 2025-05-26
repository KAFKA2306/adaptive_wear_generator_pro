import unittest
import bpy
import sys
import os
import time
import logging

logger = logging.getLogger(__name__)

class TestAdaptiveWearGeneratorPro(unittest.TestCase):
    
    def setUp(self):
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        
        bpy.ops.mesh.primitive_cube_add()
        self.test_obj = bpy.context.active_object
        self.test_obj.name = "TestBody"
        
        self._create_test_vertex_groups()
        
        if hasattr(bpy.context.scene, 'adaptive_wear_generator_pro'):
            self.props = bpy.context.scene.adaptive_wear_generator_pro
            self.props.base_body = self.test_obj
        else:
            self.skipTest("AdaptiveWear Generator Pro not properly registered")

    def _create_test_vertex_groups(self):
        test_groups = ["chest", "hip", "arm.L", "arm.R", "hand.L", "hand.R", "leg.L", "leg.R", "foot.L", "foot.R"]
        
        for group_name in test_groups:
            vg = self.test_obj.vertex_groups.new(name=group_name)
            
            for i, vertex in enumerate(self.test_obj.data.vertices):
                if i % len(test_groups) == test_groups.index(group_name):
                    vg.add([vertex.index], 1.0, 'REPLACE')

    def test_addon_registration(self):
        self.assertTrue(hasattr(bpy.context.scene, 'adaptive_wear_generator_pro'))
        self.assertIsNotNone(bpy.context.scene.adaptive_wear_generator_pro)

    def test_property_validation(self):
        is_valid, errors = self.props.validate_settings()
        
        self.props.wear_type = "NONE"
        is_valid, errors = self.props.validate_settings()
        self.assertFalse(is_valid)
        self.assertIn("衣装タイプが選択されていません", errors)
        
        self.props.wear_type = "T_SHIRT"
        self.props.thickness = 0.0005
        is_valid, errors = self.props.validate_settings()
        self.assertFalse(is_valid)

    def test_tshirt_generation(self):
        self.props.wear_type = "T_SHIRT"
        self.props.quality_level = "MEDIUM"
        
        start_time = time.time()
        result = bpy.ops.awgp.generate_wear()
        end_time = time.time()
        
        self.assertEqual(result, {'FINISHED'})
        self.assertLess(end_time - start_time, 10.0)
        
        generated_objects = [obj for obj in bpy.context.scene.objects if "tshirt" in obj.name.lower()]
        self.assertGreater(len(generated_objects), 0)

    def test_pants_generation(self):
        self.props.wear_type = "PANTS"
        self.props.quality_level = "MEDIUM"
        
        result = bpy.ops.awgp.generate_wear()
        self.assertEqual(result, {'FINISHED'})
        
        generated_objects = [obj for obj in bpy.context.scene.objects if "pants" in obj.name.lower()]
        self.assertGreater(len(generated_objects), 0)

    def test_skirt_generation(self):
        self.props.wear_type = "SKIRT"
        self.props.pleat_count = 12
        self.props.pleat_depth = 0.05
        
        result = bpy.ops.awgp.generate_wear()
        self.assertEqual(result, {'FINISHED'})
        
        generated_objects = [obj for obj in bpy.context.scene.objects if "skirt" in obj.name.lower()]
        self.assertGreater(len(generated_objects), 0)

    def test_bra_generation(self):
        self.props.wear_type = "BRA"
        self.props.quality_level = "HIGH"
        
        result = bpy.ops.awgp.generate_wear()
        self.assertEqual(result, {'FINISHED'})

    def test_socks_generation(self):
        self.props.wear_type = "SOCKS"
        self.props.sock_length = 0.7
        
        result = bpy.ops.awgp.generate_wear()
        self.assertEqual(result, {'FINISHED'})

    def test_gloves_generation(self):
        self.props.wear_type = "GLOVES"
        self.props.glove_fingers = True
        
        result = bpy.ops.awgp.generate_wear()
        self.assertEqual(result, {'FINISHED'})

    def test_material_application(self):
        self.props.wear_type = "T_SHIRT"
        self.props.use_text_material = True
        self.props.material_prompt = "red silk glossy"
        
        result = bpy.ops.awgp.generate_wear()
        self.assertEqual(result, {'FINISHED'})
        
        generated_objects = [obj for obj in bpy.context.scene.objects if "tshirt" in obj.name.lower()]
        if generated_objects:
            obj = generated_objects[0]
            self.assertGreater(len(obj.data.materials), 0)

    def test_diagnosis_operation(self):
        result = bpy.ops.awgp.diagnose_bones()
        self.assertEqual(result, {'FINISHED'})

    def test_comprehensive_diagnosis(self):
        if hasattr(bpy.ops.awgp, 'comprehensive_diagnosis'):
            result = bpy.ops.awgp.comprehensive_diagnosis()
            self.assertEqual(result, {'FINISHED'})

    def test_error_handling(self):
        self.props.base_body = None
        
        result = bpy.ops.awgp.generate_wear()
        self.assertEqual(result, {'CANCELLED'})

    def test_quality_levels(self):
        quality_levels = ["MEDIUM", "HIGH", "STABLE", "ULTIMATE"]
        
        for quality in quality_levels:
            with self.subTest(quality=quality):
                self.props.wear_type = "T_SHIRT"
                self.props.quality_level = quality
                
                start_time = time.time()
                result = bpy.ops.awgp.generate_wear()
                end_time = time.time()
                
                self.assertEqual(result, {'FINISHED'})
                
                if quality == "ULTIMATE":
                    self.assertLess(end_time - start_time, 15.0)
                else:
                    self.assertLess(end_time - start_time, 8.0)

    def test_ai_settings_validation(self):
        ai_settings = self.props.get_ai_settings()
        
        self.assertIn("quality_mode", ai_settings)
        self.assertIn("threshold", ai_settings)
        self.assertIsInstance(ai_settings["threshold"], float)
        self.assertGreaterEqual(ai_settings["threshold"], 0.0)
        self.assertLessEqual(ai_settings["threshold"], 1.0)

    def tearDown(self):
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)

def run_all_tests():
    unittest.main(argv=[''], exit=False, verbosity=2)

if __name__ == '__main__':
    run_all_tests()
