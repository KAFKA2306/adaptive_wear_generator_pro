import bpy
import re
import logging
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)


def apply_text_material(
    obj: bpy.types.Object, wear_type: str, material_prompt: str
) -> None:
    if not obj or obj.type != "MESH":
        logger.warning(
            f"オブジェクト '{obj.name if obj else 'None'}' はメッシュではないため、テキストマテリアル適用をスキップします。"
        )
        return

    logger.info(
        f"オブジェクト '{obj.name}' にテキストマテリアルを適用 (タイプ: {wear_type}, プロンプト: '{material_prompt}')"
    )

    material_properties = _parse_material_prompt(material_prompt)
    mat = _create_ai_material(obj, wear_type, material_properties)
    _apply_material_to_object(obj, mat)


def _parse_material_prompt(prompt: str) -> Dict[str, Any]:
    properties = {
        "base_color": (0.5, 0.5, 0.5, 1.0),
        "metallic": 0.0,
        "roughness": 0.5,
        "emission": (0.0, 0.0, 0.0, 1.0),
        "emission_strength": 0.0,
        "subsurface": 0.0,
        "specular": 0.5,
        "alpha": 1.0,
    }

    prompt_lower = prompt.lower()

    if "シルク" in prompt or "silk" in prompt_lower:
        properties["base_color"] = (0.9, 0.9, 0.85, 1.0)
        properties["roughness"] = 0.1
        properties["specular"] = 0.8
    elif "レザー" in prompt or "leather" in prompt_lower:
        properties["base_color"] = (0.3, 0.2, 0.1, 1.0)
        properties["roughness"] = 0.3
        properties["specular"] = 0.6
    elif "メタル" in prompt or "metal" in prompt_lower:
        properties["base_color"] = (0.7, 0.7, 0.7, 1.0)
        properties["metallic"] = 1.0
        properties["roughness"] = 0.2
    elif "光沢" in prompt or "glossy" in prompt_lower:
        properties["roughness"] = 0.1
        properties["specular"] = 0.9
    elif "マット" in prompt or "matte" in prompt_lower:
        properties["roughness"] = 0.9
        properties["specular"] = 0.1

    color_patterns = {
        r"赤|red": (0.8, 0.2, 0.2, 1.0),
        r"青|blue": (0.2, 0.2, 0.8, 1.0),
        r"緑|green": (0.2, 0.8, 0.2, 1.0),
        r"黄|yellow": (0.8, 0.8, 0.2, 1.0),
        r"黒|black": (0.1, 0.1, 0.1, 1.0),
        r"白|white": (0.9, 0.9, 0.9, 1.0),
        r"紫|purple": (0.6, 0.2, 0.8, 1.0),
    }

    for pattern, color in color_patterns.items():
        if re.search(pattern, prompt):
            properties["base_color"] = color
            break

    if "発光" in prompt or "glow" in prompt_lower or "emit" in prompt_lower:
        properties["emission"] = properties["base_color"][:3] + (1.0,)
        properties["emission_strength"] = 2.0

    if "透明" in prompt or "transparent" in prompt_lower:
        properties["alpha"] = 0.5
    elif "半透明" in prompt or "translucent" in prompt_lower:
        properties["alpha"] = 0.7
        properties["subsurface"] = 0.3

    return properties


def _create_ai_material(
    obj: bpy.types.Object, wear_type: str, properties: Dict[str, Any]
) -> bpy.types.Material:
    mat_name = f"AWGP_AI_{wear_type}_{obj.name}"
    mat = bpy.data.materials.get(mat_name)

    if mat is None:
        try:
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            nodes.clear()

            principled_bsdf = nodes.new("ShaderNodeBsdfPrincipled")
            principled_bsdf.location = (0, 0)

            material_output = nodes.new("ShaderNodeOutputMaterial")
            material_output.location = (300, 0)

            links = mat.node_tree.links
            links.new(
                principled_bsdf.outputs["BSDF"], material_output.inputs["Surface"]
            )

            principled_bsdf.inputs["Base Color"].default_value = properties[
                "base_color"
            ]
            principled_bsdf.inputs["Metallic"].default_value = properties["metallic"]
            principled_bsdf.inputs["Roughness"].default_value = properties["roughness"]
            principled_bsdf.inputs["Specular"].default_value = properties["specular"]
            principled_bsdf.inputs["Alpha"].default_value = properties["alpha"]

            if hasattr(principled_bsdf.inputs, "Subsurface"):
                principled_bsdf.inputs["Subsurface"].default_value = properties[
                    "subsurface"
                ]

            if properties["emission_strength"] > 0:
                principled_bsdf.inputs["Emission"].default_value = properties[
                    "emission"
                ]
                if hasattr(principled_bsdf.inputs, "Emission Strength"):
                    principled_bsdf.inputs[
                        "Emission Strength"
                    ].default_value = properties["emission_strength"]

            if properties["alpha"] < 1.0:
                mat.blend_method = "BLEND"
                mat.use_screen_refraction = True

            _add_texture_nodes(mat, wear_type, properties)

            logger.debug(f"新しいAIマテリアル '{mat_name}' を作成しました。")
        except Exception as e:
            logger.error(f"AIマテリアル '{mat_name}' の作成に失敗しました: {e}")
            return _create_fallback_material(wear_type)

    return mat


def _add_texture_nodes(
    mat: bpy.types.Material, wear_type: str, properties: Dict[str, Any]
) -> None:
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    principled_bsdf = nodes.get("Principled BSDF")
    if not principled_bsdf:
        return

    if wear_type.lower() in ["t_shirt", "pants"]:
        _add_fabric_texture(nodes, links, principled_bsdf)
    elif wear_type.lower() == "bra":
        _add_lace_texture(nodes, links, principled_bsdf)
    elif wear_type.lower() in ["socks", "gloves"]:
        _add_knit_texture(nodes, links, principled_bsdf)
    elif wear_type.lower() == "skirt":
        _add_pleated_texture(nodes, links, principled_bsdf)


def _add_fabric_texture(nodes, links, principled_bsdf):
    noise_texture = nodes.new("ShaderNodeTexNoise")
    noise_texture.location = (-400, 0)
    noise_texture.inputs["Scale"].default_value = 10.0
    noise_texture.inputs["Detail"].default_value = 2.0
    noise_texture.inputs["Roughness"].default_value = 0.5

    color_ramp = nodes.new("ShaderNodeValToRGB")
    color_ramp.location = (-200, 0)
    color_ramp.color_ramp.elements[0].position = 0.4
    color_ramp.color_ramp.elements[1].position = 0.6

    links.new(noise_texture.outputs["Fac"], color_ramp.inputs["Fac"])
    links.new(color_ramp.outputs["Color"], principled_bsdf.inputs["Roughness"])


def _add_lace_texture(nodes, links, principled_bsdf):
    voronoi_texture = nodes.new("ShaderNodeTexVoronoi")
    voronoi_texture.location = (-400, 0)
    voronoi_texture.inputs["Scale"].default_value = 20.0

    color_ramp = nodes.new("ShaderNodeValToRGB")
    color_ramp.location = (-200, 0)
    color_ramp.color_ramp.elements[0].position = 0.3
    color_ramp.color_ramp.elements[1].position = 0.7

    links.new(voronoi_texture.outputs["Distance"], color_ramp.inputs["Fac"])
    links.new(color_ramp.outputs["Alpha"], principled_bsdf.inputs["Alpha"])


def _add_knit_texture(nodes, links, principled_bsdf):
    wave_texture = nodes.new("ShaderNodeTexWave")
    wave_texture.location = (-400, 0)
    wave_texture.inputs["Scale"].default_value = 5.0
    wave_texture.inputs["Distortion"].default_value = 2.0

    bump_node = nodes.new("ShaderNodeBump")
    bump_node.location = (-200, 0)
    bump_node.inputs["Strength"].default_value = 0.3

    links.new(wave_texture.outputs["Color"], bump_node.inputs["Height"])
    links.new(bump_node.outputs["Normal"], principled_bsdf.inputs["Normal"])


def _add_pleated_texture(nodes, links, principled_bsdf):
    gradient_texture = nodes.new("ShaderNodeTexGradient")
    gradient_texture.location = (-400, 0)
    gradient_texture.gradient_type = "LINEAR"

    mapping_node = nodes.new("ShaderNodeMapping")
    mapping_node.location = (-600, 0)
    mapping_node.inputs["Scale"].default_value = (1.0, 10.0, 1.0)

    texture_coord = nodes.new("ShaderNodeTexCoord")
    texture_coord.location = (-800, 0)

    links.new(texture_coord.outputs["Generated"], mapping_node.inputs["Vector"])
    links.new(mapping_node.outputs["Vector"], gradient_texture.inputs["Vector"])
    links.new(gradient_texture.outputs["Color"], principled_bsdf.inputs["Base Color"])


def _apply_material_to_object(
    obj: bpy.types.Object, material: bpy.types.Material
) -> None:
    try:
        if obj.data.materials:
            obj.data.materials[0] = material
            logger.debug(
                f"オブジェクト '{obj.name}' の既存マテリアルを '{material.name}' に置き換えました。"
            )
        else:
            obj.data.materials.append(material)
            logger.debug(
                f"オブジェクト '{obj.name}' にAIマテリアル '{material.name}' を追加しました。"
            )
    except Exception as e:
        logger.error(f"オブジェクト '{obj.name}' へのマテリアル適用に失敗しました: {e}")


def _create_fallback_material(wear_type: str) -> bpy.types.Material:
    mat_name = f"AWGP_Fallback_{wear_type}"
    mat = bpy.data.materials.get(mat_name)

    if mat is None:
        mat = bpy.data.materials.new(name=mat_name)
        mat.diffuse_color = (0.5, 0.5, 0.5, 1.0)

    return mat


def apply_default_material(obj: bpy.types.Object, wear_type: str) -> None:
    if not obj or obj.type != "MESH":
        logger.warning(
            f"オブジェクト '{obj.name if obj else 'None'}' はメッシュではないため、デフォルトマテリアル適用をスキップします。"
        )
        return

    mat_name = f"AWGP_Default_{wear_type}"
    mat = bpy.data.materials.get(mat_name)
    if mat is None:
        try:
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            nodes.clear()

            principled_bsdf = nodes.new("ShaderNodeBsdfPrincipled")
            principled_bsdf.location = (0, 0)

            material_output = nodes.new("ShaderNodeOutputMaterial")
            material_output.location = (300, 0)

            links = mat.node_tree.links
            links.new(
                principled_bsdf.outputs["BSDF"], material_output.inputs["Surface"]
            )

            color = (0.5, 0.5, 0.5, 1)
            if wear_type.lower() == "t_shirt":
                color = (0.8, 0.2, 0.2, 1)
            elif wear_type.lower() == "pants":
                color = (0.2, 0.2, 0.8, 1)
            elif wear_type.lower() == "bra":
                color = (0.8, 0.5, 0.2, 1)
            elif wear_type.lower() == "socks":
                color = (0.3, 0.3, 0.3, 1)
            elif wear_type.lower() == "gloves":
                color = (0.2, 0.8, 0.2, 1)
            elif wear_type.lower() == "skirt":
                color = (0.8, 0.2, 0.8, 1)

            principled_bsdf.inputs["Base Color"].default_value = color
            logger.debug(f"新しいデフォルトマテリアル '{mat_name}' を作成しました。")
        except Exception as e:
            logger.error(f"デフォルトマテリアル '{mat_name}' の作成に失敗しました: {e}")
            return

    try:
        if obj.data.materials:
            obj.data.materials[0] = mat
            logger.debug(
                f"オブジェクト '{obj.name}' の既存マテリアルを '{mat_name}' に置き換えました。"
            )
        else:
            obj.data.materials.append(mat)
            logger.debug(
                f"オブジェクト '{obj.name}' にデフォルトマテリアル '{mat_name}' を追加しました。"
            )
    except Exception as e:
        logger.error(f"オブジェクト '{obj.name}' へのマテリアル適用に失敗しました: {e}")
