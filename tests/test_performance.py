import time
import bpy
import psutil
import gc
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class PerformanceProfiler:
    def __init__(self):
        self.results = {}
        self._setup_test_environment()

    def _setup_test_environment(self):
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete(use_global=False)

        bpy.ops.mesh.primitive_cube_add()
        self.test_body = bpy.context.active_object
        self.test_body.name = "PerfTestBody"

        self._create_performance_vertex_groups()

        if hasattr(bpy.context.scene, "adaptive_wear_generator_pro"):
            self.props = bpy.context.scene.adaptive_wear_generator_pro
            self.props.base_body = self.test_body
        else:
            raise RuntimeError("AdaptiveWear Generator Pro not properly registered")

    def _create_performance_vertex_groups(self):
        test_groups = [
            "chest",
            "hip",
            "arm.L",
            "arm.R",
            "hand.L",
            "hand.R",
            "leg.L",
            "leg.R",
            "foot.L",
            "foot.R",
            "torso",
            "neck",
        ]

        for group_name in test_groups:
            vg = self.test_body.vertex_groups.new(name=group_name)
            for i, vertex in enumerate(self.test_body.data.vertices):
                if i % len(test_groups) == test_groups.index(group_name):
                    vg.add([vertex.index], 1.0, "REPLACE")

    def profile_generation_speed(self) -> Dict[str, float]:
        wear_types = ["T_SHIRT", "PANTS", "BRA", "SOCKS", "GLOVES", "SKIRT"]
        generation_times = {}

        for wear_type in wear_types:
            logger.info(f"Performance test: {wear_type}")

            self.props.wear_type = wear_type
            self.props.quality_level = "MEDIUM"

            if wear_type == "SKIRT":
                self.props.pleat_count = 12
                self.props.pleat_depth = 0.05
            elif wear_type == "SOCKS":
                self.props.sock_length = 0.5
            elif wear_type == "GLOVES":
                self.props.glove_fingers = True

            gc.collect()

            start_time = time.time()
            try:
                result = bpy.ops.awgp.generate_wear()
                end_time = time.time()

                if result == {"FINISHED"}:
                    generation_times[wear_type] = end_time - start_time
                else:
                    generation_times[wear_type] = -1

            except Exception as e:
                logger.error(f"Performance test failed for {wear_type}: {e}")
                generation_times[wear_type] = -1

            self._cleanup_generated_objects()

        return generation_times

    def profile_memory_usage(self) -> Dict[str, Any]:
        import psutil

        process = psutil.Process()

        initial_memory = process.memory_info().rss / 1024 / 1024

        self.props.wear_type = "T_SHIRT"
        self.props.quality_level = "ULTIMATE"

        gc.collect()

        before_generation = process.memory_info().rss / 1024 / 1024

        try:
            bpy.ops.awgp.generate_wear()
            after_generation = process.memory_info().rss / 1024 / 1024
        except:
            after_generation = before_generation

        self._cleanup_generated_objects()
        gc.collect()

        final_memory = process.memory_info().rss / 1024 / 1024

        return {
            "initial_memory_mb": initial_memory,
            "before_generation_mb": before_generation,
            "after_generation_mb": after_generation,
            "final_memory_mb": final_memory,
            "memory_increase_mb": after_generation - before_generation,
            "memory_recovered_mb": after_generation - final_memory,
        }

    def profile_quality_vs_speed(self) -> Dict[str, Dict[str, float]]:
        quality_levels = ["MEDIUM", "HIGH", "STABLE", "ULTIMATE"]
        results = {}

        for quality in quality_levels:
            self.props.wear_type = "T_SHIRT"
            self.props.quality_level = quality

            times = []
            for i in range(3):
                gc.collect()

                start_time = time.time()
                try:
                    result = bpy.ops.awgp.generate_wear()
                    end_time = time.time()

                    if result == {"FINISHED"}:
                        times.append(end_time - start_time)
                    else:
                        times.append(-1)

                except Exception as e:
                    logger.error(f"Quality test failed for {quality}: {e}")
                    times.append(-1)

                self._cleanup_generated_objects()

            valid_times = [t for t in times if t > 0]
            if valid_times:
                results[quality] = {
                    "average_time": sum(valid_times) / len(valid_times),
                    "min_time": min(valid_times),
                    "max_time": max(valid_times),
                    "success_rate": len(valid_times) / len(times),
                }
            else:
                results[quality] = {
                    "average_time": -1,
                    "min_time": -1,
                    "max_time": -1,
                    "success_rate": 0,
                }

        return results

    def _cleanup_generated_objects(self):
        generated_objects = [
            obj
            for obj in bpy.context.scene.objects
            if obj != self.test_body and obj.name != "PerfTestBody"
        ]

        for obj in generated_objects:
            bpy.data.objects.remove(obj, do_unlink=True)

    def generate_performance_report(self) -> str:
        logger.info("=== Performance Profiling Started ===")

        speed_results = self.profile_generation_speed()
        memory_results = self.profile_memory_usage()
        quality_results = self.profile_quality_vs_speed()

        report = []
        report.append("=== AdaptiveWear Generator Pro Performance Report ===\n")

        report.append("Generation Speed Results:")
        for wear_type, time_taken in speed_results.items():
            if time_taken > 0:
                report.append(f"  {wear_type}: {time_taken:.2f} seconds")
                status = (
                    "GOOD"
                    if time_taken < 3.0
                    else "ACCEPTABLE"
                    if time_taken < 8.0
                    else "SLOW"
                )
                report.append(f"    Status: {status}")
            else:
                report.append(f"  {wear_type}: FAILED")

        report.append("\nMemory Usage Results:")
        report.append(f"  Initial Memory: {memory_results['initial_memory_mb']:.1f} MB")
        report.append(
            f"  Memory Increase: {memory_results['memory_increase_mb']:.1f} MB"
        )
        report.append(
            f"  Memory Recovered: {memory_results['memory_recovered_mb']:.1f} MB"
        )

        memory_status = (
            "GOOD"
            if memory_results["memory_increase_mb"] < 100
            else "ACCEPTABLE"
            if memory_results["memory_increase_mb"] < 300
            else "HIGH"
        )
        report.append(f"  Memory Status: {memory_status}")

        report.append("\nQuality vs Speed Results:")
        for quality, metrics in quality_results.items():
            if metrics["success_rate"] > 0:
                report.append(
                    f"  {quality}: {metrics['average_time']:.2f}s avg (success: {metrics['success_rate']:.0%})"
                )
            else:
                report.append(f"  {quality}: FAILED")

        report.append("\nRecommendations:")

        avg_time = sum(t for t in speed_results.values() if t > 0) / len(
            [t for t in speed_results.values() if t > 0]
        )
        if avg_time > 5.0:
            report.append(
                "  - Consider using lower quality settings for faster generation"
            )

        if memory_results["memory_increase_mb"] > 200:
            report.append(
                "  - Memory usage is high, consider closing other applications"
            )

        failed_types = [
            wear_type
            for wear_type, time_taken in speed_results.items()
            if time_taken < 0
        ]
        if failed_types:
            report.append(
                f"  - Failed generation types need investigation: {', '.join(failed_types)}"
            )

        report_text = "\n".join(report)
        logger.info(report_text)

        return report_text


def run_performance_tests():
    profiler = PerformanceProfiler()
    return profiler.generate_performance_report()


if __name__ == "__main__":
    run_performance_tests()
