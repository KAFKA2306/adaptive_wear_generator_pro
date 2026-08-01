# AdaptiveWear Generator Pro — Blender密着衣装生成アドオン

**リポジトリ:** https://github.com/KAFKA2306/adaptive_wear_generator_pro

Blender上の素体メッシュから、Tシャツ、パンツ、ブラ、靴下、手袋などの密着衣装候補を生成するアドオンです。

`bl_info`上のアドオンバージョンは`4.1.0`、最低Blenderバージョンは`4.1.0`です。生成物は編集・検証用の候補であり、VRChat向けの販売品質、貫通のなさ、完全なウェイト・シェイプキー互換性を自動保証するものではありません。

## 主な機能

- 素体メッシュを入力とした衣装候補生成
- Tシャツ、パンツ、ブラ、靴下、手袋の生成設定
- Shrinkwrap系処理による形状追従
- 厚み・密着度の調整
- アーマチュアとウェイト転送の補助
- マテリアルプリセット
- ボーン診断オペレーター
- メッシュ整合性、プリーツ品質、性能、見た目のテストスクリプト

## 対応環境

```text
Blender 4.1以上
推奨確認環境: Blender 4.4系
```

BlenderのPython APIは版によって変わるため、異なる版では必ずインストール・生成・保存・再読込を確認してください。

## インストール

1. このリポジトリをZIP化する、またはアドオン用ディレクトリへ配置する
2. Blenderを開く
3. `編集 > プリファレンス > アドオン`を開く
4. ディスクからインストールする
5. `AdaptiveWear Generator Pro`を有効化する

有効化後の場所:

```text
3D Viewport > Sidebar（Nキー）> AdaptiveWear
```

## 基本操作

1. 対象となる素体メッシュを選ぶ
2. 素体のアーマチュア、頂点グループ、スケールを確認する
3. `AdaptiveWear`パネルで素体を指定する
4. 衣装タイプを選ぶ
5. 厚み、密着度、衣装固有設定を調整する
6. `Generate Wear`を実行する
7. 生成後にメッシュ、法線、UV、ウェイト、貫通を確認する

## 推奨される頂点グループ

| 衣装 | 例 |
| --- | --- |
| パンツ | `hip`, `pelvis`, `腰` |
| Tシャツ | `chest`, `spine`, `shoulder`, `upper_arm` |
| ブラ | `chest`, `breast`, `bust` |
| 靴下 | `foot`, `leg`, `calf`, `ankle` |
| 手袋 | `hand`, `finger`, `thumb` |

名称だけでなく、実際のウェイト分布と対象ボーンを確認してください。

## マテリアル設定

`presets/materials.json`で衣装タイプ別の基本マテリアルを管理します。

```json
{
  "wear_type": "CUSTOM_WEAR",
  "name": "Custom_Material",
  "color": [1.0, 0.5, 0.2, 1.0],
  "alpha": 1.0,
  "specular": 0.6,
  "roughness": 0.4
}
```

Blender 4.xのPrincipled BSDF仕様に合わせ、プロパティ名と値域を確認してください。

## Pythonから実行

```python
import bpy

props = bpy.context.scene.adaptive_wear_generator_pro
base_obj = props.base_body
wear_type = props.wear_type
thickness = props.thickness

bpy.ops.awg.generate_wear()
```

実際のオペレーターIDとプロパティは、`core_operators.py`と`core_properties.py`を正としてください。

## 主な構成

```text
adaptive_wear_generator_pro/
├── __init__.py
├── core_properties.py
├── core_operators.py
├── core_generators.py
├── core_utils.py
├── ui_panels.py
├── presets/
├── tests/
├── test-results/
└── docs/
```

詳細:

- [操作手順](docs/操作手順.md)
- [アーキテクチャ](docs/ARCHITECTURE.md)
- [Blender Python APIメモ](docs/bpy_docs.md)
- [旧README](docs/README.md)

## テスト

リポジトリには次の検証スクリプトがあります。

- 基本機能
- メッシュ整合性
- 見た目の回帰比較
- プリーツ品質
- 性能
- 参照画像生成

テスト結果は、使用したBlender版、入力素体、設定、実行環境に依存します。既存の`test-results/`は過去の記録であり、現在の環境での合格を意味しません。

## VRChat向けに追加で必要な確認

- 対象アバターの利用規約
- Unity対応バージョン
- ボーン・ウェイト・BlendShape
- ポーズ時の身体貫通
- 法線、UV、マテリアル
- Modular Avatarなどの統合方法
- PhysBone・Collider
- パフォーマンスランク
- VRChatクライアント内の実動作

## 注意

- 「AI駆動」「高品質」「完全継承」といった表現は、実装やテストだけでは品質保証になりません
- 生成後の人間による修正とレビューを前提にしてください
- 購入アバターや第三者モデルをリポジトリへ含めないでください
- 衣装販売へ進める場合は、別途ライセンス、品質、納品物、サポート範囲を確定してください

**README最終監査:** 2026-08-01
