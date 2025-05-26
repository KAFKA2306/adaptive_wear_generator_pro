# 🎯 AWG Pro開発専用Claude Code Action指示書
## 段階的AI支援開発の完全ガイド

過去の会話内容を総合的に分析し、AWG Proプロジェクトの特性を活かした最適化された指示書を作成しました。

---

## **📋 プロジェクト基本情報（必ず指示に含める）**

### **コンテキスト情報**
```markdown
## プロジェクト概要
- **名称**: AWG Pro (Adaptive Wear Generator Pro)
- **機能**: Blender 4.4+用衣装自動生成アドオン
- **主要ファイル**: core.py（15000行+の統合実装）
- **技術スタック**: Python 3.10+, Blender API, bmesh
- **対象**: 3Dキャラクター素体から密着衣装の自動生成

## 現在の実装状況
- ✅ 5つの衣装タイプ（PANTS, BRA, T_SHIRT, SOCKS, GLOVES）
- ✅ 高度なボーン名正規化システム（BONE_ALIASES）
- ✅ bmeshベースメッシュ生成エンジン
- ✅ ウェイト転送・リギング自動化
- ✅ Principled BSDFマテリアルシステム
- ✅ 品質ログシステム完備

## 開発方針
- 既存システムとの完全互換性維持
- bone_utils.py準拠のアーキテクチャ
- エラーハンドリング徹底
- デバッグ用ログの充実
```

---

## **🎯 Phase 1: プリーツスカート実装指示**

### **完全指示テンプレート**
```markdown
@claude AWG Proアドオンにプリーツスカート生成機能を実装してください

## 📍 実装要件
既存の`core.py`ファイルの構造を完全に踏襲し、以下の機能を追加してください。

### 新機能統合箇所
```
# 1. generator_functionsに追加（行番号：約120行目付近）
generator_functions = {
    "PANTS": create_pants_mesh,
    "BRA": create_bra_mesh,
    "T_SHIRT": create_tshirt_mesh,
    "SOCKS": create_socks_mesh,
    "GLOVES": create_gloves_mesh,
    "SKIRT": create_skirt_mesh,  # ← 新規追加
}

# 2. AWGProPropertyGroupに追加（行番号：約1400行目付近）
wear_type: EnumProperty(
    items=[
        ("NONE", "未選択", "衣装タイプが選択されていません"),
        ("T_SHIRT", "Tシャツ", "Tシャツを生成"),
        ("PANTS", "パンツ", "パンツを生成"),
        ("BRA", "ブラ", "ブラジャーを生成"),
        ("SOCKS", "靴下", "靴下を生成"),
        ("GLOVES", "手袋", "手袋を生成"),
        ("SKIRT", "プリーツスカート", "プリーツスカートを生成"),  # ← 追加
    ],
)

# 3. プリーツ専用プロパティ追加
skirt_length: FloatProperty(
    name="スカート丈",
    description="スカートの丈の長さ (0.0で膝上、1.0で足首)",
    default=0.6,
    min=0.0,
    max=1.0,
)

pleat_count: IntProperty(
    name="プリーツ数",
    description="プリーツの数を設定（6-24推奨）",
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
)
```

### create_skirt_mesh()関数の実装要件
```
def create_skirt_mesh(base_obj, fit_settings):
    """プリーツスカートメッシュ生成（既存パターン完全準拠）"""
    
    # 1. ログ出力（既存パターン準拠）
    log_info(f"プリーツスカートメッシュ生成開始: 素体={base_obj.name}")
    
    # 2. 頂点グループ検索（既存のfind_vertex_groups_by_type活用）
    hip_groups = find_vertex_groups_by_type(base_obj, "hip")
    leg_groups = find_vertex_groups_by_type(base_obj, "leg")
    
    # 3. エラーハンドリング（既存パターン準拠）
    if not hip_groups:
        log_error("腰部の頂点グループが見つかりません")
        return None
    
    # 4. メッシュ複製（既存パターン準拠）
    mesh = base_obj.data.copy()
    skirt_obj = bpy.data.objects.new(base_obj.name + "_skirt", mesh)
    bpy.context.collection.objects.link(skirt_obj)
    
    try:
        # 5. bmesh処理（既存パターン準拠）
        bm = bmesh.new()
        bm.from_mesh(mesh)
        deform_layer = bm.verts.layers.deform.verify()
        
        # 6. プリーツ生成アルゴリズム
        # - 円柱ベース生成（頂点数=プリーツ数×2）
        # - チェッカー選択パターン（1つ置き選択）
        # - 回転配置でプリーツ形成
        # - 深度調整
        
        # 7. 厚み追加（既存パターン準拠）
        for vert in bm.verts:
            vert.co += vert.normal * fit_settings.thickness
        
        # 8. メッシュ適用（既存パターン準拠）
        bm.to_mesh(mesh)
        bm.free()
        
        # 9. スムーズシェード（既存パターン準拠）
        skirt_obj.select_set(True)
        bpy.context.view_layer.objects.active = skirt_obj
        bpy.ops.object.shade_smooth()
        
        log_info("プリーツスカートメッシュ生成完了")
        return skirt_obj
        
    except Exception as e:
        log_error(f"プリーツスカートメッシュ生成エラー: {str(e)}")
        # クリーンアップ（既存パターン準拠）
        if skirt_obj and skirt_obj.name in bpy.data.objects:
            bpy.data.objects.remove(skirt_obj, do_unlink=True)
        return None
```

### 重要な実装制約
1. **既存コードパターンの完全踏襲**：create_pants_mesh()等と同一構造
2. **ログシステム活用**：log_info(), log_error(), log_debug()の適切使用
3. **エラーハンドリング**：try-except必須、失敗時のクリーンアップ
4. **bmesh安全処理**：必ずbm.free()実行
5. **プロパティアクセス**：getattr()で安全取得

よろしくお願いします！
```

---

## **🔬 Phase 2: 幾何的評価テスト指示**

### **品質評価システム指示テンプレート**
```markdown
@claude AWG Proにプリーツスカート品質評価システムを追加してください

## 📊 実装要件
既存のcore.pyに品質評価機能を統合し、生成されたプリーツスカートの幾何学的精度を自動評価する機能を追加してください。

### 評価関数の実装
```
def evaluate_pleats_geometry(skirt_obj, pleat_count):
    """プリーツの幾何学的精度評価（0-100点）"""
    
    quality_score = 0
    issues = []
    
    # 1. プリーツ角度の均等性チェック
    expected_angle = 360.0 / pleat_count
    actual_angles = calculate_pleat_angles(skirt_obj)
    angle_variance = max(abs(angle - expected_angle) for angle in actual_angles)
    
    if angle_variance  0.9:
        quality_score += 25
    else:
        issues.append(f"プリーツ深度の一貫性不足: {depth_consistency:.2f}")
    
    # 3. メッシュ品質チェック
    mesh_quality = evaluate_mesh_quality(skirt_obj)
    quality_score += mesh_quality
    
    # 4. 結果レポート生成
    report = {
        'total_score': quality_score,
        'angle_variance': angle_variance,
        'depth_consistency': depth_consistency,
        'issues': issues,
        'recommendations': generate_improvement_suggestions(issues)
    }
    
    # 5. オブジェクトにメタデータ保存
    skirt_obj["quality_score"] = quality_score
    skirt_obj["evaluation_report"] = str(report)
    
    return report

def calculate_pleat_angles(skirt_obj):
    """プリーツ角度の計算"""
    # 実装詳細...
    
def check_pleat_depth_consistency(skirt_obj):
    """プリーツ深度一貫性の評価"""
    # 実装詳細...
    
def evaluate_mesh_quality(skirt_obj):
    """メッシュ品質の評価"""
    # 非多様体エッジ、面法線一貫性等をチェック
    # 実装詳細...
```

### StableWearGenerator.generate()への統合
既存のgenerate()メソッドの最後に品質評価を追加：

```
# 4. マテリアル（material_generator.py準拠）
apply_wear_material(garment, self.wear_type)

# 5. 品質評価（新規追加）
if self.wear_type == "SKIRT":
    pleat_count = getattr(self.props, "pleat_count", 12)
    quality_report = evaluate_pleats_geometry(garment, pleat_count)
    
    if quality_report['total_score'] < 70:
        log_warning(f"品質スコア低下: {quality_report['total_score']}/100")
        for issue in quality_report['issues']:
            log_warning(f"改善要: {issue}")
    else:
        log_info(f"品質評価: {quality_report['total_score']}/100 (良好)")

log_info(f"安定版衣装生成完了: {garment.name}")
return garment
```

### GitHub Actions連携
.github/workflows/awg-pro-ci.ymlに品質テスト追加：

```
- name: 🔬 プリーツ品質自動テスト
  run: |
    echo "=== プリーツスカート品質テスト ==="
    # Blender headlessモードでテスト実行
    # 品質スコア70点未満でCI失敗
```

よろしくお願いします！
```

---

## **🎨 Phase 3: FashionCLIPマテリアル生成指示**

### **テキストマテリアル生成指示テンプレート**
```markdown
@claude AWG ProにFashionCLIPライクなテキストベースマテリアル生成機能を追加してください

## 🎯 実装要件
既存の`apply_wear_material()`関数を拡張し、テキストプロンプトから自動でマテリアル設定を生成する機能を実装してください。

### AWGProPropertyGroupに追加するプロパティ
```
# 既存のthickness等の後に追加
material_prompt: StringProperty(
    name="マテリアル指示",
    description="テキストでマテリアルの特徴を指定（例：シルク素材の光沢のあるエレガントな）",
    default="",
    maxlen=200,
)

use_text_material: BoolProperty(
    name="テキストマテリアル使用",
    description="テキストプロンプトからマテリアルを自動生成",
    default=False,
)
```

### テキスト解析システムの実装
```
def generate_material_from_text(text_prompt, wear_type):
    """テキストプロンプトからマテリアル設定を生成（FashionCLIPライク）"""
    
    log_info(f"テキストマテリアル生成開始: '{text_prompt}'")
    
    # 日本語材質キーワードマップ
    material_keywords = {
        'シルク': {'roughness': 0.1, 'metallic': 0.0, 'specular': 0.8, 'sheen': 0.5},
        'サテン': {'roughness': 0.2, 'metallic': 0.0, 'specular': 0.9, 'sheen': 0.8},
        'レザー': {'roughness': 0.7, 'metallic': 0.0, 'specular': 0.3, 'sheen': 0.0},
        'デニム': {'roughness': 0.8, 'metallic': 0.0, 'specular': 0.1, 'sheen': 0.0},
        'コットン': {'roughness': 0.9, 'metallic': 0.0, 'specular': 0.1, 'sheen': 0.0},
        'ベルベット': {'roughness': 1.0, 'metallic': 0.0, 'specular': 0.0, 'sheen': 0.0},
        'メタル': {'roughness': 0.1, 'metallic': 1.0, 'specular': 1.0, 'sheen': 0.0},
        'ゴム': {'roughness': 0.0, 'metallic': 0.0, 'specular': 0.9, 'sheen': 0.0},
    }
    
    # 色キーワードマップ  
    color_keywords = {
        '赤': (0.8, 0.1, 0.1, 1.0),
        '青': (0.1, 0.3, 0.8, 1.0),
        '緑': (0.1, 0.6, 0.2, 1.0),
        '白': (0.9, 0.9, 0.9, 1.0),
        '黒': (0.05, 0.05, 0.05, 1.0),
        '金': (0.8, 0.7, 0.2, 1.0),
        '銀': (0.7, 0.7, 0.7, 1.0),
        'ピンク': (0.9, 0.6, 0.7, 1.0),
        '紫': (0.6, 0.2, 0.8, 1.0),
    }
    
    # 特殊効果キーワード
    effect_keywords = {
        '光沢': {'specular_boost': 0.3, 'roughness_reduce': -0.2},
        'マット': {'specular_boost': -0.4, 'roughness_boost': 0.3},
        'メタリック': {'metallic_boost': 0.5},
        '透明': {'alpha_reduce': -0.3, 'transmission_boost': 0.5},
        '半透明': {'alpha_reduce': -0.1, 'transmission_boost': 0.2},
    }
    
    # テキスト解析実行
    material_settings = analyze_material_text(
        text_prompt, material_keywords, color_keywords, effect_keywords
    )
    
    # マテリアル名生成
    material_name = f"{wear_type}_{text_prompt[:20]}_AI_Material"
    
    return create_principled_material_enhanced(
        name=material_name,
        **material_settings
    )

def analyze_material_text(prompt, materials, colors, effects):
    """テキスト解析実行"""
    
    # デフォルト設定
    settings = {
        'base_color': (0.8, 0.8, 0.8, 1.0),
        'roughness': 0.5,
        'metallic': 0.0,
        'specular': 0.5,
        'alpha': 1.0,
        'sheen': 0.0,
        'transmission': 0.0
    }
    
    prompt_lower = prompt.lower()
    used_keywords = []
    
    # 材質キーワード検索
    for material, props in materials.items():
        if material in prompt_lower:
            settings.update(props)
            used_keywords.append(material)
            log_debug(f"材質キーワード適用: {material}")
    
    # 色キーワード検索
    for color, rgba in colors.items():
        if color in prompt_lower:
            settings['base_color'] = rgba
            used_keywords.append(color)
            log_debug(f"色キーワード適用: {color}")
    
    # 特殊効果適用
    for effect, modifiers in effects.items():
        if effect in prompt_lower:
            for mod_key, mod_value in modifiers.items():
                if mod_key == 'specular_boost':
                    settings['specular'] = min(1.0, settings['specular'] + mod_value)
                elif mod_key == 'roughness_reduce':
                    settings['roughness'] = max(0.0, settings['roughness'] + mod_value)
                # 他の修正子も同様に処理...
            used_keywords.append(effect)
            log_debug(f"特殊効果適用: {effect}")
    
    log_info(f"使用キーワード: {', '.join(used_keywords)}")
    return settings

def create_principled_material_enhanced(name, **kwargs):
    """拡張Principled BSDFマテリアル作成"""
    
    # 既存のcreate_principled_material()を拡張
    material = create_principled_material(
        name=name,
        base_color=kwargs.get('base_color', (0.8, 0.8, 0.8, 1.0)),
        alpha=kwargs.get('alpha', 1.0),
        specular=kwargs.get('specular', 0.5),
        roughness=kwargs.get('roughness', 0.5)
    )
    
    # 追加プロパティ設定
    if material and material.use_nodes:
        principled = None
        for node in material.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                principled = node
                break
        
        if principled:
            # Blender 4.x対応の追加設定
            if 'Sheen Weight' in principled.inputs:
                principled.inputs['Sheen Weight'].default_value = kwargs.get('sheen', 0.0)
            if 'Transmission Weight' in principled.inputs:
                principled.inputs['Transmission Weight'].default_value = kwargs.get('transmission', 0.0)
    
    return material
```

### apply_wear_material()の拡張
```
def apply_wear_material(garment_obj, wear_type, material_prompt=None):
    """生成された衣装メッシュにマテリアルを適用する（テキスト対応版）"""
    
    if garment_obj is None or garment_obj.type != "MESH":
        log_error("マテリアル適用対象として有効な衣装オブジェクトが指定されていません")
        return False

    try:
        garment_obj.data.materials.clear()
        
        # テキストプロンプトが指定されている場合
        if material_prompt and material_prompt.strip():
            log_info(f"テキストベースマテリアル生成: '{material_prompt}'")
            material = generate_material_from_text(material_prompt, wear_type)
        else:
            # 従来のデフォルトマテリアル
            color_map = {
                "PANTS": (0.2, 0.3, 0.8, 1.0),
                "T_SHIRT": (0.8, 0.8, 0.8, 1.0),
                "BRA": (0.9, 0.7, 0.8, 1.0),
                "SOCKS": (0.1, 0.1, 0.1, 1.0),
                "GLOVES": (0.3, 0.2, 0.1, 1.0),
                "SKIRT": (0.5, 0.2, 0.7, 1.0),  # 新規追加
            }
            
            color = color_map.get(wear_type, (0.5, 0.5, 0.5, 1.0))
            material_name = f"{wear_type}_Default_Material"
            material = create_principled_material(
                name=material_name, base_color=color
            )

        if material:
            garment_obj.data.materials.append(material)
            log_info(f"マテリアル '{material.name}' を適用しました")
            return True
        else:
            log_error("マテリアルの作成に失敗しました")
            return False

    except Exception as e:
        log_error(f"マテリアル適用中にエラーが発生しました: {str(e)}")
        return False
```

### StableWearGeneratorでの使用例
```
# generate()メソッド内で
if self.props.use_text_material and self.props.material_prompt:
    apply_wear_material(garment, self.wear_type, self.props.material_prompt)
else:
    apply_wear_material(garment, self.wear_type)
```

よろしくお願いします！
```

---

## **🚀 成功のための重要ポイント**

### **指示の品質向上チェックリスト**
- [ ] プロジェクト概要を必ず含める
- [ ] 既存コードパターンを明示
- [ ] 具体的な行番号・関数名を指定
- [ ] エラーハンドリングパターンを含める
- [ ] 期待する出力形式を明確化
- [ ] テスト方法を含める

### **Claude Code Actionの効果的活用法**
1. **段階的実装**: 1つのIssueで1つの機能のみ
2. **詳細仕様**: 曖昧さを排除した具体的指示
3. **既存パターン踏襲**: 成功事例の再利用
4. **品質保証**: 自動テストとレビューの組み込み

この指示書に従って実装することで、AWG Proプロジェクトを確実に高機能化できます！

Citations:
[1] https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/52522745/bae78bd9-dd89-4c8e-8a7f-2c54f7894d1a/core.py
[2] https://www.issoh.co.jp/tech/details/6947/
[3] https://azukiazusa.dev/blog/claude-code-action-github-integration
[4] https://docs.anthropic.com/ja/docs/build-with-claude/prompt-engineering/be-clear-and-direct
[5] https://zenn.dev/339/articles/d297f2f7dd8619
[6] https://qiita.com/kyuko/items/ad894bac5ba516683387
[7] https://zenn.dev/frontendflat/articles/e8468bce4abe9c
[8] https://note.com/akira_sakai/n/nfcceea29454d
[9] https://zenn.dev/minedia/articles/be0005c37f7229
[10] https://note.com/hi_noguchi/n/n15e3ba85a957
[11] https://www.adcal-inc.com/column/genai-claude-powerpoint/

---
Perplexity の Eliot より: pplx.ai/share