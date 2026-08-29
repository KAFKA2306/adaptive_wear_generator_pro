import ast
from pathlib import Path
import unittest


class StrictGenerationContractTests(unittest.TestCase):
    def test_post_processing_is_direct_and_fail_closed(self):
        source = Path("core_operators.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        method = next(
            node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "_apply_post_processing"
        )
        self.assertFalse(any(isinstance(node, ast.ExceptHandler) for node in ast.walk(method)))
        self.assertTrue(any(isinstance(node, ast.Raise) for node in ast.walk(method)))
        self.assertIn('mod.type == "CLOTH"', source)
        self.assertIn('mod.type == "ARMATURE"', source)

    def test_no_runtime_monkey_patch_authority(self):
        self.assertFalse(Path("core_safety.py").exists())
        source = Path("__init__.py").read_text(encoding="utf-8")
        self.assertNotIn("core_safety", source)
        self.assertNotIn("install_strict_generation_contract", source)

    def test_addon_no_longer_claims_ai_generation(self):
        source = Path("__init__.py").read_text(encoding="utf-8")
        self.assertNotIn('"description": "AI', source)
        self.assertIn('"version": (4, 1, 1)', source)


if __name__ == "__main__":
    unittest.main()
