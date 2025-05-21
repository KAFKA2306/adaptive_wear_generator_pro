import os
import json
import bpy

def create_basic_material(name="MVP_Material", color=(0.8, 0.8, 0.8, 1.0)):
    """Blender 4.1対応の基本マテリアルを作成"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    # プリンシプルBSDFノードを取得
    principled = mat.node_tree.nodes.get('Principled BSDF')
    if principled:
        # Blender 4.1では直接RGBAを設定可能
        principled.inputs['Base Color'].default_value = color

    return mat

def apply_basic_material(garment_obj, color=(0.8, 0.8, 0.8, 1.0)):
    """オブジェクトに基本マテリアルを適用"""
    if garment_obj and garment_obj.type == 'MESH':
        # 既存のマテリアルスロットをクリア
        garment_obj.data.materials.clear()

        # 新しいマテリアルを作成して適用
        mat = create_basic_material(
            name=f"MVP_{garment_obj.name}_Material",
            color=color
        )
        garment_obj.data.materials.append(mat)
        return mat
    return None
def load_material_presets():
    """マテリアルプリセットを読み込む"""
    this_dir = os.path.dirname(__file__)
    presets_path = os.path.join(this_dir, "..", "presets", "materials.json")
    try:
        with open(presets_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception:
        return []