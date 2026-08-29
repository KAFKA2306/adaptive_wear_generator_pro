# 実装構造

この文書は`main`の現行ファイル構成だけを説明します。将来構想はGitHub Issuesへ置きます。

## 構成

```text
adaptive_wear_generator_pro/
├── __init__.py
├── core_generators.py
├── core_materials.py
├── core_operators.py
├── core_properties.py
├── core_utils.py
├── ui_panels.py
├── tests/
├── .github/workflows/
└── docs/
```

生成された`test-results/`、Python bytecode、個人環境用ファイルはGit管理しません。Node.js依存、weekly research、未参照preset JSONもありません。

## 登録フロー

`__init__.py`の`register()`が、PropertyGroup、2つのOperator、3つのPanelを直接登録します。runtimeでメソッドを差し替えるmonkey-patchはありません。

## 生成フロー

```text
AWG_PT_MainPanel
  ↓
AWGP_OT_GenerateWear.execute()
  ├─ AWGProPropertyGroup.validate_settings()
  ├─ _generate_garment()
  │   ├─ SKIRT → generate_pleated_skirt()
  │   └─ その他 → UltimateAIWearGenerator.generate()
  ├─ _apply_post_processing()
  │   ├─ material適用後のmaterial slotを確認
  │   ├─ Cloth要求時はCLOTH modifierを確認
  │   └─ auto rigging要求時は対象Armature modifierを確認
  └─ select_single_object()
```

`UltimateAIWearGenerator`などの旧名称に`AI`が含まれますが、学習済みモデルや推論ランタイムはありません。

## モジュールの責務

- `__init__.py`: `bl_info`、ロギング、Blenderクラス登録・解除
- `core_properties.py`: Sceneプロパティと入力値検証
- `core_operators.py`: 生成・診断Operator、生成成功条件
- `core_generators.py`: 衣装候補メッシュのルールベース生成
- `core_materials.py`: デフォルト/テキスト入力ベースのマテリアル処理
- `core_utils.py`: 選択、アーマチュア探索、リギング、クロス等の補助
- `ui_panels.py`: `AdaptiveWear`サイドバー

## 診断

`AWGP_OT_DiagnoseBones`は、頂点・面・頂点グループ・ボーン数に加え、BMeshの`edge.is_manifold`を使ってnon-manifold edge数、孤立頂点、ngon数を記録します。`bmesh.is_valid`を多様体性の代理として扱いません。

## テストとCI

- `.github/workflows/strict-generation-contract.yml`
  - `tests/test_strict_generation_contract.py`
- `.github/workflows/awg-pro-ci.yml`
  - Blender 4.1.0
  - 6衣装タイプの基本生成
  - T-Shirt / Pants / Skirtのメッシュ整合性
  - T-ShirtのFBX round-trip

詳細は[VALIDATION.md](VALIDATION.md)へ集約します。

## 現在の設計上の負債

- `AI`を含むクラス名・プロパティ名・UI表示がrule-based実装と一致しない
- 実アバターのポーズ貫通、UV、Shape Key、単位/scaleの正式ゲートがない
- Unity / VRChat SDK / VRChatクライアントの検証がない

作業計画は文書へ複製せず、GitHub Issuesを正本とします。
