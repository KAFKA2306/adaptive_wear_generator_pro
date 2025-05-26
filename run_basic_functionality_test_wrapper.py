import sys
import os
import traceback

addon_dir = "c:/Program Files/Blender Foundation/Blender 4.1/4.1/scripts/addons/adaptive_wear_generator_pro"

if addon_dir not in sys.path:
    sys.path.append(addon_dir)

try:
    import tests.run_basic_functionality_test

    tests.run_basic_functionality_test.run_test()
    print("TEST_RESULT: SUCCESS")
except Exception as e:
    print(f"TEST_RESULT: FAILURE - {e}")
    traceback.print_exc()
    sys.exit(1)

sys.exit(0)
