"""Regression test for fail-closed garment generation rollback in Blender."""

import bpy

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.preferences.addon_enable(module="adaptive_wear_generator_pro")

from adaptive_wear_generator_pro import core_operators


def make_body():
    mesh = bpy.data.meshes.new("RollbackBodyMesh")
    mesh.from_pydata(
        [(-1, -1, 0), (1, -1, 0), (1, 1, 0), (-1, 1, 0)],
        [],
        [(0, 1, 2, 3)],
    )
    body = bpy.data.objects.new("RollbackBody", mesh)
    bpy.context.collection.objects.link(body)
    return body


def state():
    return {
        "objects": {obj.as_pointer() for obj in bpy.data.objects},
        "meshes": {mesh.as_pointer() for mesh in bpy.data.meshes},
        "materials": {mat.as_pointer() for mat in bpy.data.materials},
    }


def new_garment(stage):
    mesh = bpy.data.meshes.new(f"RollbackGarmentMesh_{stage}")
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    garment = bpy.data.objects.new(f"RollbackGarment_{stage}", mesh)
    bpy.context.collection.objects.link(garment)
    return garment


body = make_body()
marker = bpy.data.materials.new("PreexistingMarker")
props = bpy.context.scene.adaptive_wear_generator_pro
props.base_body = body
props.wear_type = "T_SHIRT"
props.auto_rigging = False
props.enable_cloth_sim = False
props.use_text_material = False

bpy.ops.object.select_all(action="DESELECT")
body.select_set(True)
bpy.context.view_layer.objects.active = body

baseline = state()
original_generate = core_operators.AWGP_OT_GenerateWear._generate_garment
original_post = core_operators.AWGP_OT_GenerateWear._apply_post_processing

try:
    for stage in ("fitting", "quality_enhancement", "finalization"):
        def fail_during_generate(self, _props, stage=stage):
            new_garment(stage)
            raise RuntimeError(f"injected {stage} failure")

        core_operators.AWGP_OT_GenerateWear._generate_garment = fail_during_generate
        core_operators.AWGP_OT_GenerateWear._apply_post_processing = original_post

        for attempt in range(2):
            result = bpy.ops.awgp.generate_wear()
            assert "CANCELLED" in result, (stage, attempt, result)
            assert state() == baseline, (stage, attempt, state(), baseline)
            assert bpy.context.view_layer.objects.active == body
            assert set(bpy.context.selected_objects) == {body}

    for stage in ("material", "cloth", "rigging"):
        def generate(self, _props, stage=stage):
            return new_garment(stage)

        def fail_during_post(self, garment, _props, stage=stage):
            material = bpy.data.materials.new(f"RollbackMaterial_{stage}")
            garment.data.materials.append(material)
            if stage == "cloth":
                garment.modifiers.new("RollbackCloth", "CLOTH")
            raise RuntimeError(f"injected {stage} failure")

        core_operators.AWGP_OT_GenerateWear._generate_garment = generate
        core_operators.AWGP_OT_GenerateWear._apply_post_processing = fail_during_post

        for attempt in range(2):
            result = bpy.ops.awgp.generate_wear()
            assert "CANCELLED" in result, (stage, attempt, result)
            assert state() == baseline, (stage, attempt, state(), baseline)
            assert bpy.context.view_layer.objects.active == body
            assert set(bpy.context.selected_objects) == {body}
finally:
    core_operators.AWGP_OT_GenerateWear._generate_garment = original_generate
    core_operators.AWGP_OT_GenerateWear._apply_post_processing = original_post

assert marker.name in bpy.data.materials
print("ATOMIC_ROLLBACK_TEST_SUCCESS")
