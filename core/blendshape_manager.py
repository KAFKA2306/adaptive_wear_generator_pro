def transfer_blendshapes(source_obj, target_obj):
    """
    TODO: ブレンドシェイプを転送する実装を後で追加。
    ここでは何もしないスタブ。
    """
    return True
import json
import os

def load_blendshape_maps():
    """
    presets/blendshape_maps.json を読み込むスタブ。空リストを返す。
    """
    this_dir = os.path.dirname(__file__)
    presets_path = os.path.join(this_dir, "..", "presets", "blendshape_maps.json")
    try:
        with open(presets_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except Exception:
        return []