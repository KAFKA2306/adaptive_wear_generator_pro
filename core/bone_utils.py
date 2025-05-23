# core/bone_utils.py

import re
import bpy
from ..services import logging_service

logger = logging_service.get_addon_logger()

# Blender/VRChat系のボーンエイリアス辞書（BoneMatchingCore.csを参考に拡張）
BONE_ALIASES = {
    "pelvis": "hips",
    "waist": "hips",
    "spine0": "spine",
    "spine_0": "spine",
    "spine1": "spine",
    "spine_1": "spine",
    "spine2": "chest",
    "spine_2": "chest",
    "upperchest": "chest",
    "upper_chest": "chest",
    "thorax": "chest",
    "collar": "clavicle",
    "upperarm": "arm",
    "upper_arm": "arm",
    "lowerarm": "forearm",
    "lower_arm": "forearm",
    "elbow": "forearm",
    "thigh": "upperleg",
    "upleg": "upperleg",
    "upper_leg": "upperleg",
    "shin": "lowerleg",
    "calf": "lowerleg",
    "leg": "lowerleg",
    "ankle": "foot",
    "toebase": "toes",
    # 手関連の拡張
    "thumb": "thumb",
    "thunb": "thumb",
    "thunb1": "thumb_proximal",
    "thunb2": "thumb_intermediate",
    "thunb3": "thumb_distal",
    "index1": "index_proximal",
    "index2": "index_intermediate",
    "index3": "index_distal",
    "middle1": "middle_proximal",
    "middle2": "middle_intermediate",
    "middle3": "middle_distal",
    "ring1": "ring_proximal",
    "ring2": "ring_intermediate",
    "ring3": "ring_distal",
    "little1": "little_proximal",
    "little2": "little_intermediate",
    "little3": "little_distal",
    # 胸部関連
    "bust": "breast",
    "breast_root": "breast_root",
    "breast1": "breast_1",
    "breast_1": "breast_1",
    "breast2": "breast_2",
    "breast_2": "breast_2",
    "bustdynamicbone": "breast",
    "boobs": "breast",
    "front_chest": "breast_upper",
}


def normalize_bone_name(bone_name, custom_prefix=None, custom_suffix=None):
    """
    ボーン名を正規化してBlender標準形式に変換
    BoneMatchingCore.csのNormalizeBoneNameを参考に実装
    """
    if not bone_name:
        return ""

    name = bone_name.lower()
    logger.debug(f"ボーン名正規化開始: '{bone_name}' -> '{name}'")

    # _endサフィックスの処理
    ends_with_end_suffix = False
    if name.endswith("_end"):
        ends_with_end_suffix = True
        name = name[:-4]  # "_end"を削除

    # カスタムプレフィックス・サフィックス除去
    if custom_prefix and name.startswith(custom_prefix.lower()):
        name = name[len(custom_prefix) :]
    if custom_suffix and name.endswith(custom_suffix.lower()):
        name = name[: -len(custom_suffix)]

    # 一般的なプレフィックス除去
    common_prefixes = ["mixamorig", "bip01", "bip", "character", "bone", "rig"]
    for prefix in common_prefixes:
        if name.startswith(prefix):
            name = re.sub(
                f"^{re.escape(prefix)}[\\._\\s]*", "", name, flags=re.IGNORECASE
            )
            break

    # 前後の区切り文字を削除
    name = name.strip("_. ")

    # サイド情報の正規化
    side_suffix = ""

    # 左右プレフィックスのチェック
    left_prefix_match = re.match(r"^(l|left)[\._\s]*", name, re.IGNORECASE)
    if left_prefix_match:
        side_suffix = "_l"
        name = name[left_prefix_match.end() :]
    else:
        right_prefix_match = re.match(r"^(r|right)[\._\s]*", name, re.IGNORECASE)
        if right_prefix_match:
            side_suffix = "_r"
            name = name[right_prefix_match.end() :]

    # 左右サフィックスのチェック（プレフィックスが見つからなかった場合）
    if not side_suffix:
        left_suffix_match = re.search(r"[\._\s]*(l|left)$", name, re.IGNORECASE)
        if left_suffix_match:
            side_suffix = "_l"
            name = name[: left_suffix_match.start()]
        else:
            right_suffix_match = re.search(r"[\._\s]*(r|right)$", name, re.IGNORECASE)
            if right_suffix_match:
                side_suffix = "_r"
                name = name[: right_suffix_match.start()]

    # 前後の区切り文字を再度削除
    name = name.strip("_. ")

    # 区切り文字の正規化
    name = re.sub(r"[\.\-\s]", "_", name)

    # キャメルケースをスネークケースに変換
    name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    name = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", name)
    name = re.sub(r"([A-Z])([A-Z])(?=[a-z])", r"\1_\2", name)

    # 小文字に変換
    name = name.lower()

    # 数字のサフィックスを削除
    name = re.sub(r"\.\d+$", "", name)
    name = re.sub(r"_\d+$", "", name)

    # エイリアス適用
    base_name_for_alias = name
    temp_side_suffix_for_alias = ""

    if base_name_for_alias.endswith("_l"):
        temp_side_suffix_for_alias = "_l"
        base_name_for_alias = base_name_for_alias[:-2].rstrip("_")
    elif base_name_for_alias.endswith("_r"):
        temp_side_suffix_for_alias = "_r"
        base_name_for_alias = base_name_for_alias[:-2].rstrip("_")

    if base_name_for_alias in BONE_ALIASES:
        name = BONE_ALIASES[base_name_for_alias] + temp_side_suffix_for_alias
    elif name in BONE_ALIASES:
        name = BONE_ALIASES[name]

    # _endサフィックスを復元
    if ends_with_end_suffix:
        name += "_end"

    # サイド情報を追加（まだ付いていない場合）
    if side_suffix and not name.endswith(("_l", "_r")):
        if not name.endswith(side_suffix[1:]):  # 既に"l"や"r"で終わっていない場合
            name += side_suffix

    # 連続するアンダースコアを正規化
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")

    logger.debug(f"ボーン名正規化完了: '{bone_name}' -> '{name}'")
    return name


def find_vertex_group_by_patterns(mesh_obj, patterns):
    """
    指定されたパターンリストに基づいて頂点グループを柔軟に検索
    """
    if not mesh_obj or not mesh_obj.vertex_groups:
        return None

    for pattern in patterns:
        # 完全一致
        for vg in mesh_obj.vertex_groups:
            if vg.name.lower() == pattern.lower():
                logger.debug(f"頂点グループ完全一致: '{pattern}' -> '{vg.name}'")
                return vg

        # 正規化して比較
        normalized_pattern = normalize_bone_name(pattern)
        for vg in mesh_obj.vertex_groups:
            normalized_vg_name = normalize_bone_name(vg.name)
            if normalized_vg_name == normalized_pattern:
                logger.debug(f"頂点グループ正規化一致: '{pattern}' -> '{vg.name}'")
                return vg

        # 部分一致
        for vg in mesh_obj.vertex_groups:
            if pattern.lower() in vg.name.lower():
                logger.debug(f"頂点グループ部分一致: '{pattern}' -> '{vg.name}'")
                return vg

    logger.warning(f"頂点グループが見つかりません: {patterns}")
    return None


def find_hand_vertex_groups(mesh_obj):
    """
    手関連の頂点グループを柔軟に検索（画像のボーン構造を考慮）
    """
    if not mesh_obj or not mesh_obj.vertex_groups:
        return None, None

    # 画像で確認されたボーン構造に基づく検索パターン
    left_patterns = [
        "Hand_L",  # 画像で確認された形式
        "hand_l",
        "hand.l",
        "lefthand",
        "left_hand",
        "l_hand",
        "hand_left",
        "LeftHand",
        "Left_Hand",
    ]
    right_patterns = [
        "Hand_R",  # 画像で確認された形式
        "hand_r",
        "hand.r",
        "righthand",
        "right_hand",
        "r_hand",
        "hand_right",
        "RightHand",
        "Right_Hand",
    ]

    left_hand = find_vertex_group_by_patterns(mesh_obj, left_patterns)
    right_hand = find_vertex_group_by_patterns(mesh_obj, right_patterns)

    if left_hand:
        logging_service.log_info(f"左手頂点グループ発見: '{left_hand.name}'")
    if right_hand:
        logging_service.log_info(f"右手頂点グループ発見: '{right_hand.name}'")

    return left_hand, right_hand


def find_vertex_groups_by_type(mesh_obj, group_type):
    """
    指定されたタイプ（chest, hip, footなど）の頂点グループを検索
    """
    if not mesh_obj or not mesh_obj.vertex_groups:
        return []

    type_patterns = {
        "chest": ["chest", "breast", "bust", "thorax", "upper_chest", "胸"],
        "hip": ["hip", "hips", "pelvis", "waist", "腰"],
        "foot": ["foot", "feet", "ankle", "toe", "足"],
        "leg": ["leg", "thigh", "shin", "calf", "upperleg", "lowerleg", "脚"],
        "arm": ["arm", "shoulder", "upperarm", "lowerarm", "forearm", "腕", "肩"],
        "hand": [
            "hand",
            "finger",
            "thumb",
            "index",
            "middle",
            "ring",
            "little",
            "手",
            "指",
        ],
    }

    patterns = type_patterns.get(group_type, [group_type])
    found_groups = []

    for pattern in patterns:
        for vg in mesh_obj.vertex_groups:
            if pattern.lower() in vg.name.lower() and vg not in found_groups:
                found_groups.append(vg)
                logger.debug(f"'{group_type}'タイプ頂点グループ発見: '{vg.name}'")

    return found_groups


def diagnose_bone_vertex_group_mapping(mesh_obj, armature_obj=None):
    """
    メッシュオブジェクトのボーンと頂点グループの対応関係を診断
    """
    if not mesh_obj or not mesh_obj.vertex_groups:
        logging_service.log_error(
            "メッシュオブジェクトまたは頂点グループが見つかりません"
        )
        return

    logging_service.log_info(f"=== {mesh_obj.name} の頂点グループ診断 ===")
    logging_service.log_info(f"頂点グループ数: {len(mesh_obj.vertex_groups)}")

    # 頂点グループ一覧を表示
    vertex_groups = [vg.name for vg in mesh_obj.vertex_groups]
    logging_service.log_info(f"頂点グループ一覧: {vertex_groups}")

    # アーマチュア情報も取得
    if armature_obj and armature_obj.type == "ARMATURE":
        logging_service.log_info(f"=== {armature_obj.name} のボーン診断 ===")
        bones = [bone.name for bone in armature_obj.data.bones]
        logging_service.log_info(f"ボーン数: {len(bones)}")
        logging_service.log_info(f"ボーン一覧: {bones}")

        # ボーンと頂点グループの対応チェック
        logging_service.log_info("=== 対応関係チェック ===")
        for bone_name in bones:
            if bone_name in vertex_groups:
                logging_service.log_info(f"✓ {bone_name}: 対応する頂点グループあり")
            else:
                logging_service.log_warning(f"✗ {bone_name}: 対応する頂点グループなし")

        # 逆チェック：頂点グループにあってボーンにないもの
        for vg_name in vertex_groups:
            if vg_name not in bones:
                logging_service.log_warning(
                    f"! {vg_name}: 頂点グループのみ（対応ボーンなし）"
                )

    # タイプ別チェック
    for group_type in ["hand", "chest", "hip", "foot", "leg", "arm"]:
        groups = find_vertex_groups_by_type(mesh_obj, group_type)
        if groups:
            group_names = [g.name for g in groups]
            logging_service.log_info(f"{group_type}関連の頂点グループ: {group_names}")
        else:
            logging_service.log_warning(
                f"{group_type}関連の頂点グループが見つかりません"
            )


# 登録用のクラスリスト（空のタプル）
classes = ()
