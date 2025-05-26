import sys
import os
import traceback

# Add the addon directory to sys.path
addon_dir = "c:/Program Files/Blender Foundation/Blender 4.1/4.1/scripts/addons/adaptive_wear_generator_pro"
if addon_dir not in sys.path:
    sys.path.append(addon_dir)

try:
    # Import and run the specific test script
    import tests.run_basic_functionality_test
    tests.run_basic_functionality_test.run_test()
    print("TEST_RESULT: SUCCESS") # Add a marker for success
except Exception as e:
    print(f"TEST_RESULT: FAILURE - {e}") # Add a marker for failure
    traceback.print_exc()
    sys.exit(1) # Exit with non-zero code on failure

sys.exit(0) # Exit with zero code on success