import bpy
from bpy.types import PropertyGroup
from bpy.props import (
    PointerProperty,
    EnumProperty,
    BoolProperty,
    FloatProperty,
    IntProperty,
    StringProperty,
)
from typing import Optional


def poll_mesh_objects(self, obj: bpy.types.Object) -> bool:
    return obj.type == "MESH"


class AWGProPropertyGroup(PropertyGroup):
    base_body: PointerProperty(
        name="素体メッシュ",
        description="衣装生成の基となる3Dメッシュ",
        type=bpy.types.Object,
        poll=poll_mesh_objects,
    )

    wear_type: EnumProperty(
        name="衣装タイプ",
        description="生成する衣装の種類を選択",
        items=[
            ("NONE", "未選択", "衣装タイプを選択してください"),
            ("T_SHIRT", "Tシャツ", "カジュアルなTシャツを生成"),
            ("PANTS", "パンツ", "フィット感のあるパンツを生成"),
            ("BRA", "ブラ", "サポート性の高いブラを生成"),
            ("SOCKS", "靴下", "足にフィットする靴下を生成"),
            ("GLOVES", "手袋", "手の形状に合わせた手袋を生成"),
            ("SKIRT", "プリーツスカート", "動きのあるプリーツスカートを生成"),
        ],
        default="T_SHIRT",
    )

    quality_level: EnumProperty(
        name="品質レベル",
        description="生成品質と処理時間のバランス",
        items=[
            ("ULTIMATE", "AI最高品質", "最高品質のAI駆動生成（時間要）"),
            ("STABLE", "安定モード", "バランスの取れた高品質生成"),
            ("HIGH", "高品質", "高品質な標準生成"),
            ("MEDIUM", "中品質", "高速処理優先"),
        ],
        default="ULTIMATE",
    )

    tight_fit: BoolProperty(
        name="密着フィット",
        description="素体に密着したフィッティングを適用",
        default=False,
    )

    thickness: FloatProperty(
        name="厚み",
        description="生成される衣装の厚み（メートル単位）",
        default=0.01,
        min=0.001,
        max=0.1,
        step=0.1,
        precision=3,
    )

    ai_quality_mode: BoolProperty(
        name="AI品質モード", description="AI による高度な品質向上を有効化", default=True
    )

    ai_threshold: FloatProperty(
        name="AI閾値",
        description="AIによる頂点選択の閾値（低いほど多くの頂点を選択）",
        default=0.3,
        min=0.0,
        max=1.0,
        precision=2,
    )

    ai_subdivision: BoolProperty(
        name="AIサブディビジョン",
        description="AI による表面分割を有効化（最高品質時のみ）",
        default=False,
    )

    ai_thickness_multiplier: FloatProperty(
        name="AI厚み倍率",
        description="AI による厚み調整の倍率",
        default=1.0,
        min=0.1,
        max=3.0,
        precision=2,
    )

    sock_length: FloatProperty(
        name="靴下の長さ",
        description="靴下の長さ（0.0=足首、1.0=膝上）",
        default=0.5,
        min=0.0,
        max=1.0,
        precision=2,
    )

    glove_fingers: BoolProperty(
        name="指あり手袋",
        description="True=指あり手袋、False=ミトンタイプ",
        default=False,
    )

    skirt_length: FloatProperty(
        name="スカート丈",
        description="スカートの丈の長さ（0.0=膝上、1.0=足首）",
        default=0.6,
        min=0.0,
        max=1.0,
        precision=2,
    )

    pleat_count: IntProperty(
        name="プリーツ数",
        description="プリーツの数（6-24推奨）",
        default=12,
        min=6,
        max=24,
    )

    pleat_depth: FloatProperty(
        name="プリーツ深さ",
        description="プリーツの折り込み深さ",
        default=0.05,
        min=0.01,
        max=0.2,
        precision=3,
    )

    enable_cloth_sim: BoolProperty(
        name="クロスシミュレーション",
        description="リアルな布の動きをシミュレート",
        default=True,
    )

    enable_edge_smoothing: BoolProperty(
        name="エッジスムージング", description="滑らかなエッジ処理を適用", default=True
    )

    progressive_fitting: BoolProperty(
        name="多段階フィット", description="段階的なフィッティング処理", default=True
    )

    preserve_shapekeys: BoolProperty(
        name="シェイプキー保持", description="元のシェイプキーを保持", default=True
    )

    use_vertex_groups: BoolProperty(
        name="頂点グループ使用", description="頂点グループによる精密制御", default=True
    )

    min_weight: FloatProperty(
        name="最小ウェイト",
        description="頂点グループの最小ウェイト値",
        default=0.1,
        min=0.0,
        max=1.0,
        precision=2,
    )

    use_text_material: BoolProperty(
        name="テキストマテリアル使用",
        description="テキストプロンプトからマテリアルを生成",
        default=False,
    )

    material_prompt: StringProperty(
        name="マテリアル指示",
        description="マテリアルの特徴を記述（例：シルク素材の光沢のある）",
        default="",
        maxlen=200,
    )

    ai_hand_threshold: FloatProperty(
        name="AI手閾値",
        description="手の検出感度",
        default=0.1,
        min=0.0,
        max=1.0,
        precision=2,
    )

    ai_bra_threshold: FloatProperty(
        name="AIブラ閾値",
        description="胸部の検出感度",
        default=0.1,
        min=0.0,
        max=1.0,
        precision=2,
    )

    ai_tshirt_threshold: FloatProperty(
        name="AITシャツ閾値",
        description="上半身の検出感度",
        default=0.1,
        min=0.0,
        max=1.0,
        precision=2,
    )

    ai_sock_multiplier: FloatProperty(
        name="AI靴下倍率",
        description="靴下生成の調整倍率",
        default=1.0,
        min=0.1,
        max=3.0,
        precision=2,
    )

    ai_tight_offset: FloatProperty(
        name="AI密着オフセット",
        description="密着時のオフセット距離",
        default=0.001,
        min=0.0,
        max=0.1,
        precision=4,
    )

    ai_offset_multiplier: FloatProperty(
        name="AIオフセット倍率",
        description="オフセット距離の調整倍率",
        default=0.5,
        min=0.0,
        max=2.0,
        precision=2,
    )

    auto_rigging: BoolProperty(
        name="自動リギング",
        description="生成した衣装に自動でリギングを適用",
        default=True,
    )

    def get_ai_settings(self) -> dict:
        return {
            "quality_mode": self.ai_quality_mode,
            "threshold": self.ai_threshold,
            "subdivision": self.ai_subdivision,
            "thickness_multiplier": self.ai_thickness_multiplier,
            "hand_threshold": self.ai_hand_threshold,
            "bra_threshold": self.ai_bra_threshold,
            "tshirt_threshold": self.ai_tshirt_threshold,
            "sock_multiplier": self.ai_sock_multiplier,
            "tight_offset": self.ai_tight_offset,
            "offset_multiplier": self.ai_offset_multiplier,
        }

    def validate_settings(self) -> tuple[bool, list[str]]:
        errors = []
        if not self.base_body:
            errors.append("素体メッシュが選択されていません")
        elif self.base_body.type != "MESH":
            errors.append("選択されたオブジェクトはメッシュではありません")
        if self.wear_type == "NONE":
            errors.append("衣装タイプが選択されていません")
        if self.thickness < 0.001 or self.thickness > 0.1:
            errors.append("厚みは0.001から0.1の範囲で設定してください")
        if self.wear_type == "SKIRT":
            if self.pleat_count < 6 or self.pleat_count > 24:
                errors.append("プリーツ数は6から24の範囲で設定してください")
            if self.pleat_depth < 0.01 or self.pleat_depth > 0.2:
                errors.append("プリーツ深さは0.01から0.2の範囲で設定してください")
        return len(errors) == 0, errors
