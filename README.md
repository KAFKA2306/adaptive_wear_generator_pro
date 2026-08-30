# AdaptiveWear Generator Pro — Blender衣装候補生成アドオン

[![CI for AdaptiveWear Generator Pro](https://github.com/KAFKA2306/adaptive_wear_generator_pro/actions/workflows/awg-pro-ci.yml/badge.svg)](https://github.com/KAFKA2306/adaptive_wear_generator_pro/actions/workflows/awg-pro-ci.yml)

Blender上の素体メッシュから、編集開始点となる衣装メッシュ候補を生成する研究用アドオンです。

**生成物を完成衣装、販売品質、Unity/VRChat対応済み成果物として扱わないでください。** 現行実装はBlender Python APIによるルールベース処理で、学習済みモデルや推論ランタイムはありません。`AI`を含む旧名称は互換性のため残っています。

## Source

Blenderアドオン本体は `src/adaptive_wear_generator_pro/` に集約しています。

```text
src/adaptive_wear_generator_pro/
├── __init__.py
├── core_generators.py
├── core_materials.py
├── core_operators.py
├── core_properties.py
├── core_utils.py
└── ui_panels.py
```

- アドオン版: `4.1.1`
- 最低Blender: `4.1.0`
- パネル: `3D Viewport > Sidebar > AdaptiveWear`
- 衣装タイプ: `T_SHIRT`, `PANTS`, `BRA`, `SOCKS`, `GLOVES`, `SKIRT`

`core_operators.AWGP_OT_GenerateWear`が生成オーケストレーションと成功条件の正本です。マテリアル、要求されたCloth modifier、要求されたArmature modifierを処理後のBlender状態で確認し、成立しなければ`CANCELLED`を返します。runtime monkey-patchは使いません。

## Install / Use

1. `src/adaptive_wear_generator_pro/` をBlenderのaddonsディレクトリへ `adaptive_wear_generator_pro/` として配置する。ZIPの場合もこのディレクトリをトップレベルにする。
2. Blenderで `AdaptiveWear Generator Pro` を有効化する。
3. `3D Viewport > Sidebar > AdaptiveWear` を開く。
4. 検証用に複製した素体MESHを `base_body` に指定する。
5. 衣装タイプと必要な設定を選び、`Generate Wear`を実行する。
6. `FINISHED`だけで完成品質と判断せず、下記の検証を行う。

主な後処理設定は `enable_cloth_sim`, `auto_rigging`, `use_text_material` です。`preserve_shapekeys`などの設定名は、意味的互換や完全転送を保証するものではありません。

## Validation

`.github/workflows/awg-pro-ci.yml` をCIの唯一のworkflow正本とし、次を実行します。

- Python 3.12でstrict generation contractと`src/`配置を静的検査
- Blender 4.1.0へ `src/adaptive_wear_generator_pro/` を実際にアドオンとして配置
- 6衣装タイプの基本生成
- T-Shirt / Pants / Skirtのメッシュ整合性
- T-ShirtのFBX書き出し → 空シーンへ再読込

検証証拠は対象commit SHAに紐づくGitHub Actions workflow/job結果です。生成物をGitへコミットせず、artifact保存もCIの成功条件にしません。

ローカル静的テスト:

```bash
python -m unittest discover -s tests -p "test_strict_generation_contract.py" -v
```

Blender CI相当のテストは `tests/run_basic_functionality_test.py`, `tests/run_mesh_integrity_test.py`, `tests/run_fbx_roundtrip_test.py` が正本です。

### `FINISHED` の境界

`FINISHED`は要求された生成工程が完了したことを示すだけです。完成衣装として扱う前に、少なくとも実アバターでのフィット、非多様体/孤立頂点/法線、UV・マテリアル、Armature/weight、Shape Key、ポーズ貫通、保存再読込、Unity import、VRChat SDK build、VRChatクライアント表示を確認してください。

現在、Unity / VRChat SDK / VRChatクライアント、実アバターごとのフィット・ポーズ貫通、UV/Shape Keyの意味的互換は **UNVERIFIED** です。

## Repository authority

| 対象 | 正本 |
| --- | --- |
| アドオン実装 | `src/adaptive_wear_generator_pro/` |
| 生成成功条件 | `src/adaptive_wear_generator_pro/core_operators.py` |
| 自動検証 | `tests/`, `.github/workflows/awg-pro-ci.yml` |
| 未解決事項・開発予定 | GitHub Issues |
| 利用・構造・検証説明 | `README.md` |

mainへのpush時、CIはmainへ完全にmerge済みのremote branchを削除します。未merge branchは削除しません。

文書を増やして別authorityを作りません。Blender Python APIは複製せず公式文書を参照します。

https://docs.blender.org/api/current/

コード・README・過去の実行結果が矛盾する場合は、現在の`main`実装と対象commitの再現可能なテスト結果を優先します。
