import bpy
import bmesh
from mathutils import Vector
# from .utils import log_info, log_error, log_warning


def apply_fitting(garment_obj, base_obj, fit_settings):
    """衣装メッシュを素体メッシュにフィッティングさせる"""
    log_info(f"フィッティング処理開始: 衣装={garment_obj.name}, 素体={base_obj.name}")

    # シェイプキーが存在する場合、削除する (モディファイアー適用時のエラー回避のため)
    if garment_obj.data.shape_keys:
        log_info(f"フィッティング前にシェイプキーを削除します: {garment_obj.name}")
        garment_obj.shape_key_clear()

    # Shrinkwrapモディファイアーを追加
    sw_mod = garment_obj.modifiers.new(name="Shrinkwrap", type="SHRINKWRAP")
    sw_mod.target = base_obj
    sw_mod.wrap_method = fit_settings.shrinkwrap_method
    sw_mod.offset = fit_settings.shrinkwrap_offset
    sw_mod.use_project = fit_settings.shrinkwrap_use_project
    if fit_settings.shrinkwrap_use_project:
        sw_mod.project_limit = fit_settings.shrinkwrap_project_limit
        sw_mod.use_negative_direction = fit_settings.shrinkwrap_use_negative_direction
        sw_mod.use_positive_direction = fit_settings.shrinkwrap_use_positive_direction
    sw_mod.cull_face = fit_settings.shrinkwrap_cull_face
    sw_mod.wrap_mode = fit_settings.shrinkwrap_wrap_mode

    # オプション: サブディビジョンモディファイアーを追加 (フィッティング精度向上)
    if fit_settings.use_subdivision:
        subsurf_mod = garment_obj.modifiers.new(name="Subdivision", type="SUBSURF")
        subsurf_mod.levels = fit_settings.subdivision_levels
        subsurf_mod.render_levels = fit_settings.subdivision_levels
        # Shrinkwrapモディファイアーの上に配置
        bpy.context.view_layer.objects.active = garment_obj
        bpy.ops.object.modifier_move_to_immediately_above(modifier=sw_mod.name)

    # モディファイアーを適用
    try:
        bpy.context.view_layer.objects.active = garment_obj
        # サブディビジョンがあれば先に適用
        if fit_settings.use_subdivision:
            bpy.ops.object.modifier_apply(modifier="Subdivision")
        # Shrinkwrapモディファイアーを適用
        bpy.ops.object.modifier_apply(modifier=sw_mod.name)

        log_info(f"フィッティング処理完了: {garment_obj.name}")
        return True
    except Exception as e:
        log_error(f"フィッティングエラー: {str(e)}")
        # エラーが発生した場合、追加したモディファイアーを削除して元の状態に戻す試み
        if sw_mod in garment_obj.modifiers:
            garment_obj.modifiers.remove(sw_mod)
        if fit_settings.use_subdivision and "Subdivision" in garment_obj.modifiers:
            garment_obj.modifiers.remove(garment_obj.modifiers["Subdivision"])
        return False


def create_garment_from_base(base_obj, garment_settings):
    """素体メッシュから衣装メッシュを作成する"""
    log_info(f"衣装作成開始: 素体={base_obj.name}")

    # 素体オブジェクトの複製
    bpy.context.view_layer.objects.active = base_obj
    bpy.ops.object.duplicate(linked=False)
    garment_obj = bpy.context.object
    garment_obj.name = garment_settings.name

    # メッシュデータの複製 (リンク解除)
    garment_obj.data = garment_obj.data.copy()
    garment_obj.data.name = f"{garment_settings.name}_Mesh"

    # マテリアルを割り当て
    if garment_settings.material:
        # 既存のマテリアルを検索
        mat = bpy.data.materials.get(garment_settings.material)
        if not mat:
            # なければ新規作成 (簡易的に)
            mat = bpy.data.materials.new(name=garment_settings.material)
            mat.diffuse_color = (0.8, 0.1, 0.1, 1)  # 例として赤色
            log_warning(
                f"マテリアル '{garment_settings.material}' が見つかりませんでした。新規作成しました。"
            )
        if mat:
            if len(garment_obj.data.materials) == 0:
                garment_obj.data.materials.append(mat)
            else:
                garment_obj.data.materials[0] = mat

    log_info(f"衣装作成完了: {garment_obj.name}")
    return garment_obj


def prepare_garment_mesh(garment_obj, garment_settings):
    """衣装メッシュの準備処理 (厚み付けなど)"""
    log_info(f"衣装メッシュ準備開始: {garment_obj.name}")

    # Solidifyモディファイアーを追加 (厚み付け)
    if garment_settings.use_solidify:
        solidify_mod = garment_obj.modifiers.new(name="Solidify", type="SOLIDIFY")
        solidify_mod.thickness = garment_settings.solidify_thickness
        solidify_mod.offset = garment_settings.solidify_offset
        solidify_mod.use_even_offset = garment_settings.solidify_use_even_offset
        solidify_mod.use_quality_normals = garment_settings.solidify_use_quality_normals
        solidify_mod.material_offset = garment_settings.solidify_material_offset
        solidify_mod.shell_thickness = garment_settings.solidify_shell_thickness
        solidify_mod.rim_thickness = garment_settings.solidify_rim_thickness
        solidify_mod.use_rim = garment_settings.solidify_use_rim
        solidify_mod.use_rim_only = garment_settings.solidify_use_rim_only

        # Solidifyモディファイアーを適用
        try:
            bpy.context.view_layer.objects.active = garment_obj
            bpy.ops.object.modifier_apply(modifier=solidify_mod.name)
            log_info(f"Solidifyモディファイアー適用完了: {garment_obj.name}")
        except Exception as e:
            log_error(f"Solidifyモディファイアー適用エラー: {str(e)}")
            return False

    log_info(f"衣装メッシュ準備完了: {garment_obj.name}")
    return True


def clean_up_mesh(obj):
    """不要なデータをクリーンアップする"""
    log_info(f"メッシュクリーンアップ開始: {obj.name}")
    try:
        # 不要な頂点グループを削除
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.vertex_group_clean(group_select_mode="ALL")

        # 不要なUVマップを削除 (アクティブなUVマップ以外)
        if obj.data.uv_layers:
            active_uv = obj.data.uv_layers.active
            for uv_layer in obj.data.uv_layers:
                if uv_layer != active_uv:
                    obj.data.uv_layers.remove(uv_layer)

        # 不要な頂点カラーを削除
        if obj.data.vertex_colors:
            for vc in obj.data.vertex_colors:
                obj.data.vertex_colors.remove(vc)

        # 不要なシェイプキーを削除 (既にapply_fittingで削除されるが念のため)
        if obj.data.shape_keys:
            obj.shape_key_clear()

        log_info(f"メッシュクリーンアップ完了: {obj.name}")
        return True
    except Exception as e:
        log_error(f"メッシュクリーンアップエラー: {str(e)}")
        return False


def transfer_weights(source_obj, target_obj):
    """ウェイトを転送する"""
    log_info(f"ウェイト転送開始: 元={source_obj.name}, 先={target_obj.name}")
    try:
        # Data Transferモディファイアーを追加
        dt_mod = target_obj.modifiers.new(name="DataTransfer", type="DATA_TRANSFER")
        dt_mod.object = source_obj
        dt_mod.use_vert_data = True
        dt_mod.data_types_verts = {"VGROUP_WEIGHTS"}
        dt_mod.vert_mapping = (
            "NEAREST_VERTEX"  # または 'TOPOLOGY', 'NEARBY_FACE_INTERPOLATED' など
        )

        # Data Transferモディファイアーを適用
        bpy.context.view_layer.objects.active = target_obj
        bpy.ops.object.modifier_apply(modifier=dt_mod.name)

        log_info(f"ウェイト転送完了: {target_obj.name}")
        return True
    except Exception as e:
        log_error(f"ウェイト転送エラー: {str(e)}")
        # エラーが発生した場合、追加したモディファイアーを削除
        if dt_mod in target_obj.modifiers:
            target_obj.modifiers.remove(dt_mod)
        return False


def generate_wear(base_obj, garment_settings, fit_settings):
    """衣装を生成するメイン関数"""
    log_info("衣装生成処理開始")

    # 1. 素体から衣装メッシュを作成
    garment_obj = create_garment_from_base(base_obj, garment_settings)
    if not garment_obj:
        log_error("衣装メッシュの作成に失敗しました。")
        return None

    # 2. 衣装メッシュの準備 (厚み付けなど)
    if not prepare_garment_mesh(garment_obj, garment_settings):
        log_error("衣装メッシュの準備に失敗しました。")
        bpy.data.objects.remove(garment_obj, do_unlink=True)  # 失敗したら削除
        return None

    # 3. フィッティング処理
    if not apply_fitting(garment_obj, base_obj, fit_settings):
        log_error("フィッティング処理に失敗しました。")
        bpy.data.objects.remove(garment_obj, do_unlink=True)  # 失敗したら削除
        return None

    # 4. 不要なデータのクリーンアップ
    if not clean_up_mesh(garment_obj):
        log_warning(
            "メッシュクリーンアップ中に問題が発生しましたが、処理を続行します。"
        )

    # 5. ウェイト転送
    if fit_settings.transfer_weights:
        if not transfer_weights(base_obj, garment_obj):
            log_warning("ウェイト転送に失敗しましたが、処理を続行します。")

    log_info("衣装生成処理完了")
    return garment_obj
    name = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", name)
    name = re.sub(r"([A-Z])([A-Z])(?=[a-z])", r"\1_\2", name)
    name = name.lower()
    name = re.sub(r"\.\d+$", "", name)
    name = re.sub(r"_\d+$", "", name)

    base_name_for_alias, temp_side_suffix_for_alias = name, ""
    if base_name_for_alias.endswith("_l"):
        temp_side_suffix_for_alias, base_name_for_alias = (
            "_l",
            base_name_for_alias[:-2].rstrip("_"),
        )
    elif base_name_for_alias.endswith("_r"):
        temp_side_suffix_for_alias, base_name_for_alias = (
            "_r",
            base_name_for_alias[:-2].rstrip("_"),
        )

    if base_name_for_alias in BONE_ALIASES:
        name = BONE_ALIASES[base_name_for_alias] + temp_side_suffix_for_alias
    elif name in BONE_ALIASES:
        name = BONE_ALIASES[name]

    if ends_with_end_suffix:
        name += "_end"
    if (
        side_suffix
        and not name.endswith(("_l", "_r"))
        and not name.endswith(side_suffix[1:])
    ):
        name += side_suffix
    name = re.sub(r"_+", "_", name).strip("_")
    return name


@performance_monitor
def find_vertex_group_by_patterns(mesh_obj, patterns):
    if not mesh_obj or not mesh_obj.vertex_groups:
        return None
    for pattern in patterns:
        for vg in mesh_obj.vertex_groups:
            if vg.name.lower() == pattern.lower():
                return vg
        normalized_pattern = normalize_bone_name(pattern)
        for vg in mesh_obj.vertex_groups:
            if normalize_bone_name(vg.name) == normalized_pattern:
                return vg
        for vg in mesh_obj.vertex_groups:
            if pattern.lower() in vg.name.lower():
                return vg
    return None


def find_hand_vertex_groups(mesh_obj):
    if not mesh_obj or not mesh_obj.vertex_groups:
        return None, None
    left_patterns = [
        "Hand_L",
        "hand_l",
        "hand.l",
        "lefthand",
        "left_hand",
        "l_hand",
        "hand_left",
        "LeftHand",
        "Left_Hand",
        "HandL",
        "hand_L_ctrl",
        "def_hand_l",
        "ctrl_hand_l",
        "ai_hand_left",
    ]
    right_patterns = [
        "Hand_R",
        "hand_r",
        "hand.r",
        "righthand",
        "right_hand",
        "r_hand",
        "hand_right",
        "RightHand",
        "Right_Hand",
        "HandR",
        "hand_R_ctrl",
        "def_hand_r",
        "ctrl_hand_r",
        "ai_hand_right",
    ]
    left_hand, right_hand = (
        find_vertex_group_by_patterns(mesh_obj, left_patterns),
        find_vertex_group_by_patterns(mesh_obj, right_patterns),
    )
    return left_hand, right_hand


@performance_monitor
def find_vertex_groups_by_type(mesh_obj, group_type):
    if (
        not mesh_obj
        or not mesh_obj.vertex_groups
        or group_type not in ADVANCED_VERTEX_PATTERNS
    ):
        return []
    pattern_config, found_groups = ADVANCED_VERTEX_PATTERNS[group_type], []
    all_patterns = (
        pattern_config["primary"]
        + pattern_config["secondary"]
        + pattern_config["ai_patterns"]
    )
    for pattern in all_patterns:
        for vg in mesh_obj.vertex_groups:
            if pattern.lower() in vg.name.lower() and vg not in found_groups:
                found_groups.append(vg)
    return found_groups


class SafeBlenderContext:
    def __init__(self, target_obj=None):
        self.target_obj = target_obj
        self.original_active, self.original_selected, self.original_mode = (
            None,
            [],
            None,
        )

    def __enter__(self):
        try:
            self.original_active = bpy.context.view_layer.objects.active
            self.original_selected = [obj for obj in bpy.context.selected_objects]
            if self.original_active and self.original_active.mode != "OBJECT":
                self.original_mode = self.original_active.mode
                bpy.ops.object.mode_set(mode="OBJECT")
            if self.target_obj:
                bpy.ops.object.select_all(action="DESELECT")
                self.target_obj.select_set(True)
                bpy.context.view_layer.objects.active = self.target_obj
        except Exception as e:
            log_error(f"コンテキスト設定エラー: {str(e)}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if (
                bpy.context.view_layer.objects.active
                and bpy.context.view_layer.objects.active.mode != "OBJECT"
            ):
                bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="DESELECT")
            for obj in self.original_selected:
                if obj and obj.name in bpy.data.objects:
                    obj.select_set(True)
            if self.original_active and self.original_active.name in bpy.data.objects:
                bpy.context.view_layer.objects.active = self.original_active
                if self.original_mode and self.original_mode != "OBJECT":
                    bpy.ops.object.mode_set(mode=self.original_mode)
        except Exception as e:
            log_warning(f"コンテキスト復元警告: {str(e)}")


@performance_monitor
def transfer_weights(source_obj, target_obj):
    if not (
        source_obj
        and source_obj.type == "MESH"
        and target_obj
        and target_obj.type == "MESH"
    ):
        return False
    try:
        with SafeBlenderContext(target_obj):
            for mod in [
                m
                for m in target_obj.modifiers
                if m.type == "DATA_TRANSFER" and "AI_" in m.name
            ]:
                target_obj.modifiers.remove(mod)
            dt_mod = target_obj.modifiers.new(
                name="AI_DataTransfer", type="DATA_TRANSFER"
            )
            dt_mod.object, dt_mod.use_vert_data, dt_mod.data_types_verts = (
                source_obj,
                True,
                {"VGROUP_WEIGHTS"},
            )
            (
                dt_mod.vert_mapping,
                dt_mod.layers_vgroup_select_src,
                dt_mod.layers_vgroup_select_dst,
            ) = "NEAREST", "ALL", "NAME"
            dt_mod.use_max_distance, dt_mod.max_distance = True, 0.1
            bpy.ops.object.modifier_apply(modifier=dt_mod.name)
            return True
    except Exception as e:
        log_error(f"ウェイト転送エラー: {str(e)}")
        return False


@performance_monitor
def apply_rigging(garment_obj, base_obj, base_armature_obj):
    if not (
        garment_obj
        and garment_obj.type == "MESH"
        and base_obj
        and base_obj.type == "MESH"
        and base_armature_obj
        and base_armature_obj.type == "ARMATURE"
    ):
        return False
    try:
        with SafeBlenderContext(garment_obj):
            for mod in [
                m
                for m in garment_obj.modifiers
                if m.type == "ARMATURE" and "AI_" in m.name
            ]:
                garment_obj.modifiers.remove(mod)
            arm_mod = garment_obj.modifiers.new(name="AI_Armature", type="ARMATURE")
            arm_mod.object, arm_mod.use_deform_preserve_volume = base_armature_obj, True
            arm_mod.use_bone_envelopes, arm_mod.use_vertex_groups = False, True
            if not transfer_weights(base_obj, garment_obj):
                return False
            return True
    except Exception as e:
        log_error(f"リギングエラー: {str(e)}")
        return False


@performance_monitor
def apply_fitting(garment_obj, base_obj, fit_settings):
    if not (
        garment_obj
        and garment_obj.type == "MESH"
        and base_obj
        and base_obj.type == "MESH"
    ):
        return False
    try:
        with SafeBlenderContext(garment_obj):
            for mod in [
                m
                for m in garment_obj.modifiers
                if m.type == "SHRINKWRAP" and "AI_" in m.name
            ]:
                garment_obj.modifiers.remove(mod)
            sw_mod = garment_obj.modifiers.new(name="AI_Shrinkwrap", type="SHRINKWRAP")
            sw_mod.target = base_obj
            if getattr(fit_settings, "tight_fit", False):
                (
                    sw_mod.wrap_method,
                    sw_mod.use_project_x,
                    sw_mod.use_project_y,
                    sw_mod.use_project_z,
                ) = "PROJECT", True, True, True
                sw_mod.use_negative_direction, sw_mod.use_positive_direction = (
                    True,
                    True,
                )
                sw_mod.offset = getattr(fit_settings, "ai_tight_offset", 0.001)
            else:
                sw_mod.wrap_method = "NEAREST_SURFACEPOINT"
                sw_mod.offset = fit_settings.thickness * getattr(
                    fit_settings, "ai_offset_multiplier", 0.5
                )
            # Blender 4.1互換性対応
            if hasattr(sw_mod, "use_keep_above_surface"):
                sw_mod.use_keep_above_surface = True
            else:
                # Blender 4.1以降の場合、use_keep_above_surfaceはuse_invert_cullの反転に相当
                # cull_face = "FRONT" の場合、use_invert_cull は False に設定
                if hasattr(sw_mod, "use_invert_cull"):
                    sw_mod.use_invert_cull = False

            if hasattr(sw_mod, "cull_face"):
                sw_mod.cull_face = "FRONT"
            bpy.ops.object.modifier_apply(modifier=sw_mod.name)
            return True
    except Exception as e:
        log_error(f"フィッティングエラー: {str(e)}")
        return False


@performance_monitor
def create_ai_principled_material(
    name,
    base_color=(0.8, 0.8, 0.8, 1.0),
    alpha=1.0,
    specular=0.5,
    roughness=0.5,
    metallic=0.0,
):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes, mat.blend_method = True, "OPAQUE" if alpha >= 1.0 else "BLEND"
    mat.node_tree.nodes.clear()
    principled = mat.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    output = mat.node_tree.nodes.new(type="ShaderNodeOutputMaterial")
    principled.location, output.location = (0, 0), (400, 0)
    mat.node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    (
        principled.inputs["Base Color"].default_value,
        principled.inputs["Alpha"].default_value,
    ) = base_color, alpha
    (
        principled.inputs["Roughness"].default_value,
        principled.inputs["Metallic"].default_value,
    ) = roughness, metallic
    if "Specular IOR Level" in principled.inputs:
        principled.inputs["Specular IOR Level"].default_value = specular
    elif "Specular" in principled.inputs:
        principled.inputs["Specular"].default_value = specular
    if alpha < 1.0:
        mat.use_backface_culling = False
    return mat


@performance_monitor
def apply_wear_material(garment_obj, wear_type):
    if not (garment_obj and garment_obj.type == "MESH"):
        return False
    try:
        garment_obj.data.materials.clear()
        color_map = {
            "PANTS": {
                "base_color": (0.2, 0.3, 0.8, 1.0),
                "roughness": 0.7,
                "metallic": 0.0,
                "specular": 0.5,
            },
            "T_SHIRT": {
                "base_color": (0.8, 0.8, 0.8, 1.0),
                "roughness": 0.8,
                "metallic": 0.0,
                "specular": 0.3,
            },
            "BRA": {
                "base_color": (0.9, 0.7, 0.8, 1.0),
                "roughness": 0.6,
                "metallic": 0.0,
                "specular": 0.4,
            },
            "SOCKS": {
                "base_color": (0.1, 0.1, 0.1, 1.0),
                "roughness": 0.9,
                "metallic": 0.0,
                "specular": 0.2,
            },
            "GLOVES": {
                "base_color": (0.3, 0.2, 0.1, 1.0),
                "roughness": 0.8,
                "metallic": 0.0,
                "specular": 0.3,
            },
        }
        cfg = color_map.get(
            wear_type,
            {
                "base_color": (0.5, 0.5, 0.5, 1.0),
                "roughness": 0.7,
                "metallic": 0.0,
                "specular": 0.4,
            },
        )
        mat_name = f"AI_{wear_type}_UltraMaterial"
        material = create_ai_principled_material(
            name=mat_name,
            base_color=cfg["base_color"],
            alpha=1.0,
            specular=cfg["specular"],
            roughness=cfg["roughness"],
            metallic=cfg["metallic"],
        )
        if material:
            garment_obj.data.materials.append(material)
            return True
        else:
            log_error("マテリアル作成失敗")
            return False
    except Exception as e:
        log_error(f"マテリアル適用エラー: {str(e)}")
        return False


__all__ = [
    "AWGLogger",
    "performance_monitor",
    "normalize_bone_name",
    "find_vertex_group_by_patterns",
    "find_hand_vertex_groups",
    "find_vertex_groups_by_type",
    "SafeBlenderContext",
    "BONE_ALIASES",
    "ADVANCED_VERTEX_PATTERNS",
    "log_info",
    "log_warning",
    "log_error",
    "log_debug",
    "transfer_weights",
    "apply_rigging",
    "apply_fitting",
    "create_ai_principled_material",
    "apply_wear_material",
]
