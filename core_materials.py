"""
コアマテリアル処理関数群
マテリアル生成と適用
"""

import bpy
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def apply_text_material(obj: bpy.types.Object, wear_type: str, material_prompt: str) -> None:
    """
    テキストプロンプトに基づいてマテリアルを生成し、オブジェクトに適用します。
    (スタブ実装 - AIマテリアル生成機能は未実装)
    Args:
        obj: マテリアルを適用するオブジェクト。
        wear_type: 衣装タイプ。
        material_prompt: マテリアル生成のためのテキストプロンプト。
    """
    if not obj or obj.type != 'MESH':
        logger.warning(f"オブジェクト '{obj.name if obj else 'None'}' はメッシュではないため、テキストマテリアル適用をスキップします。")
        return

    logger.info(f"オブジェクト '{obj.name}' にテキストマテリアルを適用 (タイプ: {wear_type}, プロンプト: '{material_prompt}')")
    # TODO: Implement AI-based material generation and application
    # 現在はデフォルトマテリアルを適用するなどのフォールバック処理を検討可能
    apply_default_material(obj, wear_type)
    logger.warning("AIベースのテキストマテリアル生成機能は現在未実装です。デフォルトマテリアルを適用しました。")


def apply_default_material(obj: bpy.types.Object, wear_type: str) -> None:
    """
    衣装タイプに応じたデフォルトのPrincipled BSDFマテリアルをオブジェクトに適用します。
    Args:
        obj: マテリアルを適用するオブジェクト。
        wear_type: 衣装タイプ。
    """
    if not obj or obj.type != 'MESH':
        logger.warning(f"オブジェクト '{obj.name if obj else 'None'}' はメッシュではないため、デフォルトマテリアル適用をスキップします。")
        return

    mat_name = f"AWGP_Default_{wear_type}"
    mat = bpy.data.materials.get(mat_name)

    if mat is None:
        try:
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
            nodes = mat.node_tree.nodes
            nodes.clear()

            # Principled BSDFノードを作成
            principled_bsdf = nodes.new('ShaderNodeBsdfPrincipled')
            principled_bsdf.location = (0, 0)

            # Material Outputノードを作成
            material_output = nodes.new('ShaderNodeOutputMaterial')
            material_output.location = (300, 0)

            # Principled BSDFをMaterial Outputに接続
            links = mat.node_tree.links
            links.new(principled_bsdf.outputs['BSDF'], material_output.inputs['Surface'])

            # デフォルトの色を設定 (衣装タイプによって色を変える)
            color = (0.5, 0.5, 0.5, 1) # デフォルトはグレー
            if wear_type.lower() == "t_shirt":
                color = (0.8, 0.2, 0.2, 1) # 赤っぽい色
            elif wear_type.lower() == "pants":
                color = (0.2, 0.2, 0.8, 1) # 青っぽい色
            elif wear_type.lower() == "bra":
                color = (0.8, 0.5, 0.2, 1) # オレンジっぽい色
            elif wear_type.lower() == "socks":
                color = (0.3, 0.3, 0.3, 1) # ダークグレー
            elif wear_type.lower() == "gloves":
                color = (0.2, 0.8, 0.2, 1) # 緑っぽい色
            elif wear_type.lower() == "skirt":
                color = (0.8, 0.2, 0.8, 1) # 紫っぽい色

            principled_bsdf.inputs['Base Color'].default_value = color
            logger.debug(f"新しいデフォルトマテリアル '{mat_name}' を作成しました。")

        except Exception as e:
            logger.error(f"デフォルトマテリアル '{mat_name}' の作成に失敗しました: {e}")
            return # マテリアル作成失敗時は適用しない

    # オブジェクトにマテリアルを適用
    try:
        if obj.data.materials:
            # 既存のマテリアルを置き換える
            obj.data.materials[0] = mat
            logger.debug(f"オブジェクト '{obj.name}' の既存マテリアルを '{mat_name}' に置き換えました。")
        else:
            # 新しいマテリアルを追加する
            obj.data.materials.append(mat)
            logger.debug(f"オブジェクト '{obj.name}' にデフォルトマテリアル '{mat_name}' を追加しました。")
    except Exception as e:
        logger.error(f"オブジェクト '{obj.name}' へのマテリアル適用に失敗しました: {e}")