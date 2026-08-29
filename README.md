# AdaptiveWear Generator Pro — Blender衣装候補生成アドオン

[![CI for AdaptiveWear Generator Pro](https://github.com/KAFKA2306/adaptive_wear_generator_pro/actions/workflows/awg-pro-ci.yml/badge.svg)](https://github.com/KAFKA2306/adaptive_wear_generator_pro/actions/workflows/awg-pro-ci.yml)
[![Strict generation contract](https://github.com/KAFKA2306/adaptive_wear_generator_pro/actions/workflows/strict-generation-contract.yml/badge.svg)](https://github.com/KAFKA2306/adaptive_wear_generator_pro/actions/workflows/strict-generation-contract.yml)

Blender上の素体メッシュから、編集開始点となる衣装メッシュ候補を生成する研究用アドオンです。

## 現在の位置づけ

**生成物を完成衣装、販売品質、Unity/VRChat対応済み成果物として扱わないでください。**

このリポジトリの価値は、自動完成衣装を主張することではなく、ルールベース処理で衣装候補を短時間で作り、生成処理の失敗と、その後に必要な検証を分離できることです。

現在の実装には学習済みモデル、推論ランタイム、学習データ、モデル版はありません。`AI`を含むプロパティ名や表示は旧来の名称であり、実装能力の根拠にはなりません。

## 現行実装

- アドオン版: `4.1.1`
- 最低Blender: `4.1.0`
- パネル: `3D Viewport > Sidebar > AdaptiveWear`
- 衣装タイプ: `T_SHIRT`, `PANTS`, `BRA`, `SOCKS`, `GLOVES`, `SKIRT`
- 生成: `core_generators.py`
- マテリアル: `core_materials.py`
- リギング・クロス・診断補助: `core_utils.py`
- UI: `ui_panels.py`
- 生成時のfail-closed契約: `core_safety.py`

登録時に`core_safety.install_strict_generation_contract()`が生成オペレーターへ厳格な後処理契約を設定します。マテリアル、クロス、要求された自動リギングなどの必須工程が失敗した場合、オペレーターは成功扱いにしません。

## 既知の品質境界

次は未解決または自動合格条件に含まれていません。

- `AI`を含む旧名称がUI・プロパティに残っている
- プリーツ品質スコア70未満は警告であり、生成失敗にはならない
- `bm.is_valid`を表示する診断は真の非多様体検査ではない
- 厚み表示とBlenderシーン単位・Object Scaleの整合を受入検査していない
- Shape Keyの意味的互換・完全転送を保証していない
- FBX、Unity、VRChatクライアントの自動ゲートがない
- 過去の`test-results/`は現在の任意アバターに対する合格証拠ではない

## ドキュメント

- [使用方法](docs/USAGE.md)
- [実装構造](docs/ARCHITECTURE.md)
- [検証と成功条件](docs/VALIDATION.md)
- [docsの管理方針](docs/README.md)

開発予定・未解決事項はGitHub Issuesを正本とします。`docs/task*.md`のような別タスクリストは作りません。

## 最小実行手順

1. リポジトリをBlenderアドオンとして配置またはZIP化する
2. Blenderで`AdaptiveWear Generator Pro`を有効化する
3. `3D Viewport > Sidebar > AdaptiveWear`を開く
4. 検証用に複製した素体メッシュを指定する
5. 衣装タイプと必要な設定を選び、`Generate Wear`を実行する
6. `FINISHED`だけで品質合格とせず、[検証と成功条件](docs/VALIDATION.md)に従って成果物を検査する

元の`.blend`、Prefab、アバター、衣装データは別途バックアップしてください。第三者の購入アセットを公開リポジトリへ含めないでください。

## 開発上の正本

| 対象 | 正本 |
| --- | --- |
| アドオンの能力 | `main`のPython実装 |
| UI設定 | `core_properties.py`, `ui_panels.py` |
| 生成時の必須工程 | `core_safety.py` |
| 自動テスト | `tests/`, `.github/workflows/` |
| 未解決事項 | GitHub Issues |
| 利用・設計・検証説明 | `docs/`の3文書 |

コードと文書が矛盾する場合はコードと実行結果を優先し、文書を修正してください。