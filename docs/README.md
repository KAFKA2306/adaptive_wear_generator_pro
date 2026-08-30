# Documentation

このディレクトリは、現在の`main`実装を説明する最小限の文書だけを置きます。

## 正本

- [USAGE.md](USAGE.md): インストール、操作、失敗時の見方
- [ARCHITECTURE.md](ARCHITECTURE.md): 現在のモジュール構成と実行フロー
- [VALIDATION.md](VALIDATION.md): CI、自動テスト、完成衣装とみなすための追加検証
- [../README.md](../README.md): リポジトリ全体の位置づけと既知の品質境界
- [GitHub Issues](https://github.com/KAFKA2306/adaptive_wear_generator_pro/issues): 未解決事項と開発予定

Blender Python APIそのものはこのリポジトリへ複製しません。公式文書を参照してください。

https://docs.blender.org/api/current/

## 文書を増やさないためのルール

- 開発予定はGitHub Issuesへ置く
- Blender APIの一般解説をコピーしない
- 個人PCのパス、一回限りの実行メモを`docs/`へ置かない
- 実装されていない構成、クラス、API、品質保証を書かない
- 過去のテスト結果を現在の任意入力に対する合格証拠として扱わない
- コードと文書が矛盾した場合は、実装と再現可能なテストを確認して文書を直す

## 変更時の確認

1. `src/adaptive_wear_generator_pro/__init__.py`の`bl_info`
2. `src/adaptive_wear_generator_pro/core_properties.py`の設定項目
3. `src/adaptive_wear_generator_pro/core_operators.py`の生成成功条件
4. `src/adaptive_wear_generator_pro/ui_panels.py`の表示項目
5. `.github/workflows/`と`tests/`の実際の検証範囲

文書だけに存在する将来設計は作らず、必要ならIssueへ移します。
