# 実装構造

この文書は`main`の現行ファイル構成だけを説明します。将来構想はGitHub Issuesへ置きます。

## 構成

```text
adaptive_wear_generator_pro/
├── __init__.py
├── core_generators.py
├── core_materials.py
├── core_mesh_utils.py
├── core_operators.py
├── core_properties.py
├── core_safety.py
├── core_utils.py
├── ui_panels.py
├── presets/
│   ├── materials.json
│   └── wear_types.json
├── tests/
├── test-results/
├── .github/workflows/
└── docs/
```

`core/`, `ui/`, `services/`というPython packageは現在存在しません。コードはルート直下のモジュールへ分割されています。

## 登録フロー

`__init__.py`の`register()`がエントリーポイントです。

```text
register()
  ├─ core_operators / core_properties / core_safety / ui_panels をimport
  ├─ core_safety.install_strict_generation_contract(core_operators)
  ├─ PropertyGroup / Operator / Panel を登録
  └─ Scene.adaptive_wear_generator_pro をPointerPropertyとして登録
```

重要なのは`core_safety.install_strict_generation_contract()`です。`core_operators.AWGP_OT_GenerateWear._apply_post_processing`を、例外を握りつぶさない実装へ登録前に差し替えます。

このため、`core_operators.py`内に残る旧`_apply_post_processing()`単体の実装だけを読んでruntimeの成功条件を判断しないでください。登録後の実行契約は`core_safety.py`が正です。

## 生成フロー

```text
AWG_PT_MainPanel
  ↓
AWGP_OT_GenerateWear.execute()
  ├─ AWGProPropertyGroup.validate_settings()
  ├─ _generate_garment()
  │   ├─ SKIRT → generate_pleated_skirt()
  │   └─ その他 → OptimizedAIWearGenerator.generate()
  ├─ strict_apply_post_processing()
  │   ├─ material
  │   ├─ pleat evaluation (SKIRT)
  │   ├─ cloth setup (有効時)
  │   └─ rigging (有効時)
  └─ select_single_object()
```

`OptimizedAIWearGenerator`などの旧名称に`AI`が含まれますが、現行リポジトリに学習済みモデルや推論ランタイムはありません。実装はBlender Python APIを使ったルールベース処理です。

## モジュールの責務

### `__init__.py`

- `bl_info`
- ロギング初期化
- Blenderクラスの登録・解除
- strict generation contractの導入

### `core_properties.py`

- `AWGProPropertyGroup`
- 素体、衣装タイプ、厚み、品質、衣装別設定などのSceneプロパティ
- 基本的な入力値検証

### `core_operators.py`

- `AWGP_OT_GenerateWear`
- `AWGP_OT_DiagnoseBones`
- その他の診断オペレーター
- 生成処理のオーケストレーション

### `core_safety.py`

- 要求された後処理をfail-closedにするruntime契約
- マテリアル、クロス、リギング等の失敗を上位へ伝播
- `auto_rigging=true`でアーマチュアが無い場合を失敗扱い

### `core_generators.py`

- 衣装候補メッシュのルールベース生成
- 通常衣装とプリーツスカートの生成処理

### `core_mesh_utils.py`

- メッシュ操作の補助処理

### `core_materials.py`

- デフォルトマテリアル
- テキスト入力に基づくルールベースのマテリアル調整

### `core_utils.py`

- オブジェクト選択
- アーマチュア探索
- リギング補助
- クロス設定
- プリーツ評価
- 頂点グループ探索等

### `ui_panels.py`

- `AdaptiveWear`サイドバー
- 基本設定、詳細設定、ヘルプ表示

### `presets/`

- マテリアル・衣装タイプの設定データ

ただし、実装がプリセットJSONを実際に参照しているかは各呼び出し箇所をコードで確認してください。ファイルが存在するだけではruntime依存を意味しません。

## テストとCI

主な自動検証は次です。

- `.github/workflows/strict-generation-contract.yml`
  - `tests/test_strict_generation_contract.py`
- `.github/workflows/awg-pro-ci.yml`
  - Blender 4.1.0
  - basic functionality
  - pleats quality
  - mesh integrity
  - visual regression

詳細と現在の検証不足は[VALIDATION.md](VALIDATION.md)に集約します。

## 現在の設計上の負債

- `AI`を含むクラス名・プロパティ名・UI表示がrule-based実装と一致しない
- `core_operators.py`の旧後処理実装を`core_safety.py`がruntimeで差し替える二重構造
- `bm.is_valid`を多様体状態として表示している
- Blender内の生成成功と、FBX / Unity / VRChatの成功が分離された自動成果物として記録されない
- Shape Keyの完全性、単位・scale、ポーズ貫通の正式ゲートがない

これらの作業計画は文書へ複製せず、GitHub Issuesを正本とします。