from pathlib import Path
import unittest


class StrictGenerationContractTests(unittest.TestCase):
    def test_strict_post_processing_has_no_catch_all_handler(self):
        source = Path("core_safety.py").read_text(encoding="utf-8")
        function = source.split("def strict_apply_post_processing", 1)[1].split(
            "def install_strict_generation_contract", 1
        )[0]
        self.assertNotIn("except Exception", function)
        self.assertIn("raise RuntimeError", function)

    def test_operator_is_patched_before_registration(self):
        source = Path("__init__.py").read_text(encoding="utf-8")
        patch_at = source.index("install_strict_generation_contract")
        register_at = source.index("bpy.utils.register_class")
        self.assertLess(patch_at, register_at)

    def test_addon_no_longer_claims_ai_generation(self):
        source = Path("__init__.py").read_text(encoding="utf-8")
        self.assertNotIn('"description": "AI', source)
        self.assertIn('"version": (4, 1, 1)', source)


if __name__ == "__main__":
    unittest.main()
