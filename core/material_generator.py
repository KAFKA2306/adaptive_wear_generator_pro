import os
import json
import bpy
from ..services import logging_service


def apply_wear_material(garment_obj, wear_type, fit_settings):
    """生成された衣装メッシュにマテリアルを適用する"""
    if garment_obj is None or garment_obj.type != "MESH":
        logging_service.log_error(
            "マテリアル適用対象として有効な衣装オブジェクトが指定されていません"
        )
        return False

    logging_service.log_info(
        f"マテリアル適用処理を開始します (衣装: {garment_obj.name}, タイプ: {wear_type})"
    )

    try:
        # 既存のマテリアルスロットをクリア
        garment_obj.data.materials.clear()

        # マテリアルプリセットを読み込み
        material_settings = get_material_settings_for_wear_type(wear_type)

        # マテリアルを作成
        if material_settings:
            material = create_material_from_settings(material_settings, wear_type)
        else:
            logging_service.log_warning(
                f"'{wear_type}' のマテリアルプリセットが見つかりませんでした。デフォルトマテリアルを使用します。"
            )
            material = create_default_material(wear_type)

        if material:
            # マテリアルを衣装オブジェクトに適用
            garment_obj.data.materials.append(material)
            logging_service.log_info(f"マテリアル '{material.name}' を適用しました")
            return True
        else:
            logging_service.log_error("マテリアルの作成に失敗しました")
            return False

    except Exception as e:
        logging_service.log_error(f"マテリアル適用中にエラーが発生しました: {str(e)}")
        return False


def get_material_settings_for_wear_type(wear_type):
    """衣装タイプに対応するマテリアル設定を取得"""
    presets = load_material_presets()
    for preset in presets:
        if preset.get("wear_type") == wear_type:
            return preset
    return None


def load_material_presets():
    """マテリアルプリセットを読み込む"""
    try:
        # アドオンディレクトリを取得
        addon_dir = os.path.dirname(os.path.dirname(__file__))
        presets_path = os.path.join(addon_dir, "presets", "materials.json")

        if os.path.exists(presets_path):
            with open(presets_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logging_service.log_info(
                f"マテリアルプリセットを読み込みました: {presets_path}"
            )
            return data
        else:
            logging_service.log_warning(
                f"マテリアルプリセットファイルが見つかりません: {presets_path}"
            )
            return get_default_material_presets()

    except json.JSONDecodeError as e:
        logging_service.log_error(
            f"マテリアルプリセットファイルの形式が不正です: {str(e)}"
        )
        return get_default_material_presets()

    except Exception as e:
        logging_service.log_error(
            f"マテリアルプリセットの読み込み中にエラーが発生しました: {str(e)}"
        )
        return get_default_material_presets()


def get_default_material_presets():
    """デフォルトのマテリアルプリセットを返す"""
    return [
        {
            "wear_type": "PANTS",
            "name": "Default_Pants_Material",
            "color": [0.2, 0.3, 0.8, 1.0],
            "alpha": 1.0,
            "specular": 0.3,
            "roughness": 0.8,
        },
        {
            "wear_type": "T_SHIRT",
            "name": "Default_TShirt_Material",
            "color": [0.8, 0.8, 0.8, 1.0],
            "alpha": 1.0,
            "specular": 0.2,
            "roughness": 0.9,
        },
        {
            "wear_type": "BRA",
            "name": "Default_Bra_Material",
            "color": [0.9, 0.7, 0.8, 1.0],
            "alpha": 1.0,
            "specular": 0.4,
            "roughness": 0.6,
        },
        {
            "wear_type": "SOCKS",
            "name": "Default_Socks_Material",
            "color": [0.1, 0.1, 0.1, 1.0],
            "alpha": 1.0,
            "specular": 0.1,
            "roughness": 0.95,
        },
        {
            "wear_type": "GLOVES",
            "name": "Default_Gloves_Material",
            "color": [0.3, 0.2, 0.1, 1.0],
            "alpha": 1.0,
            "specular": 0.3,
            "roughness": 0.7,
        },
    ]


def create_material_from_settings(settings, wear_type):
    """設定からマテリアルを作成"""
    material_name = settings.get("name", f"{wear_type}_Material")
    color = tuple(settings.get("color", [0.8, 0.8, 0.8, 1.0]))
    alpha = settings.get("alpha", 1.0)
    specular = settings.get("specular", 0.5)
    roughness = settings.get("roughness", 0.5)

    return create_principled_material(
        name=material_name,
        base_color=color,
        alpha=alpha,
        specular=specular,
        roughness=roughness,
    )


def create_default_material(wear_type):
    """デフォルトマテリアルを作成"""
    color_map = {
        "PANTS": (0.2, 0.3, 0.8, 1.0),
        "T_SHIRT": (0.8, 0.8, 0.8, 1.0),
        "BRA": (0.9, 0.7, 0.8, 1.0),
        "SOCKS": (0.1, 0.1, 0.1, 1.0),
        "GLOVES": (0.3, 0.2, 0.1, 1.0),
    }

    color = color_map.get(wear_type, (0.5, 0.5, 0.5, 1.0))
    material_name = f"{wear_type}_DefaultMaterial"

    return create_principled_material(
        name=material_name, base_color=color, alpha=1.0, specular=0.5, roughness=0.5
    )


def create_principled_material(
    name, base_color=(0.8, 0.8, 0.8, 1.0), alpha=1.0, specular=0.5, roughness=0.5
):
    """Principled BSDFを使用したマテリアルを作成"""
    # 既存のマテリアルをチェック
    if name in bpy.data.materials:
        return bpy.data.materials[name]

    # 新しいマテリアルを作成
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    # ブレンドモードを設定
    mat.blend_method = "OPAQUE" if alpha >= 1.0 else "BLEND"

    # ノードツリーをクリア
    mat.node_tree.nodes.clear()

    # Principled BSDFノードを追加
    principled = mat.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    principled.location = (0, 0)

    # Material Outputノードを追加
    output = mat.node_tree.nodes.new(type="ShaderNodeOutputMaterial")
    output.location = (400, 0)

    # ノードを接続
    mat.node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])

    # プロパティを設定
    principled.inputs["Base Color"].default_value = base_color
    principled.inputs["Alpha"].default_value = alpha
    principled.inputs["Roughness"].default_value = roughness

    # Blender 4.x対応: Specular設定
    if "Specular IOR Level" in principled.inputs:
        # Blender 4.0以降
        principled.inputs["Specular IOR Level"].default_value = specular
    elif "Specular" in principled.inputs:
        # 従来のバージョン
        principled.inputs["Specular"].default_value = specular

    return mat
