# AdaptiveWear Generator Pro

AdaptiveWear Generator Pro は、Blender 用のアドオンであり、アバター向けの衣服を自動的に生成し、素体にフィットさせることを目的としています。

## 開発者向け情報

このセクションでは、AdaptiveWear Generator Pro の開発に貢献したい方向けの情報を提供します。

### プロジェクトの目的と開発プロセス

このプロジェクトは、ユーザーが簡単にアバター用の衣服を生成し、既存の素体にフィットさせることができるツールを提供することを目指しています。開発は、以下の原則に基づいています。

-   **小さなタスク**: 各タスクは小さく、テスト可能であること。
-   **明確な開始と終了**: 各タスクには明確な開始点と終了点があること。
-   **単一の関心事**: 各タスクは単一の関心事に焦点を当てること。

### コーディングプロトコル

コードを書く際は、以下のプロトコルに従ってください。

-   必要最低限のコードのみを書く。
-   広範囲にわたる変更を行わない。
-   現在のタスクにのみ焦点を当て、無関係な編集は避ける。
-   コードは正確で、モジュール化されており、テスト可能であること。
-   既存の機能を壊さない。
-   ユーザー側での設定が必要な場合 (例: Supabase/AWS 設定)、明確に指示する。

### テスト実行

Blender 環境でテストを実行するには、以下の点に注意してください。

-   **テストフレームワーク**: Blender の標準 Python 環境には `pytest` が含まれていないため、[`unittest`](https://docs.python.org/ja/3/library/unittest.html) を使用してください。
-   **Blender 実行ファイルの指定**: テストをバックグラウンドで実行する場合、Blender の実行ファイルをフルパスで指定する必要があります。例: `"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe"`
-   **外部モジュールのインポートと `sys.path`**: テストスクリプト内でプロジェクトのルートディレクトリにあるモジュールをインポートするためには、テストスクリプトの実行時に `sys.path` にプロジェクトルートを追加する必要があります。

```python
import os
import sys

# 現在のスクリプトのディレクトリを取得
script_dir = os.path.dirname(os.path.abspath(__file__))

# プロジェクトルートディレクトリを計算 (例: scripts/AdaptiveWearGeneratorPro)
# testsディレクトリから見て2階層上のディレクトリ
project_root = os.path.join(script_dir, os.pardir, os.pardir)

# プロジェクトルートをsys.pathに追加
sys.path.append(project_root)

# これでプロジェクトルート以下のモジュールをインポートできるようになります
# 例: from adaptive_wear_generator_pro.core import fit_engine
```

-   **テスト実行コマンド例**: `sys.path` の修正を行った後の Blender でのテスト実行コマンド例です。
```bash
"C:\Program Files\Blender Foundation\Blender 4.1\blender.exe" --background --python "M:\Data\Blender\scripts\AdaptiveWearGeneratorPro\adaptive_wear_generator_pro\tests\test_fit_engine.py"
```

### テスト失敗時のエラー確認

テストが失敗した場合、以下の方法でエラーの詳細を確認できます。

1.  **テスト実行スクリプトの出力**:
    テストをコマンドラインから実行した場合、エラーメッセージやトレースバックは標準出力に表示されます。テスト実行に使用したターミナルまたはコンソールの出力を確認してください。

2.  **Blender のコンソール出力**:
    Blender のバックグラウンド実行 (`--background` オプション) でテストを実行した場合でも、エラー情報は Blender のコンソールに出力されることがあります。Blender を GUI モードで起動し、`ウィンドウ > トグルシステムコンソール` (Windows) またはターミナル (macOS/Linux) から起動した場合はそのターミナルを確認してください。エラーメッセージや Python のトレースバックが表示されている可能性があります。

これらの情報を元に、テスト失敗の原因を特定し、コードの修正を行ってください。

### ファイル構造


プロジェクトの主要なディレクトリとファイルは以下の通りです。

-   `adaptive_wear_generator_pro/`: アドオンのルートディレクトリ
    -   `__init__.py`: Blender アドオンとして認識されるためのファイル
    -   `core/`: アドオンの主要なロジックが含まれます
        -   `blendshape_manager.py`: ブレンドシェイプの管理
        -   `bone_rigging.py`: ボーンのリギング
        -   `export_tools.py`: エクスポート関連ツール
        -   `fit_engine.py`: フィットエンジンのロジック
        -   `material_manager.py`: マテリアルの管理
        -   `mesh_generator.py`: メッシュ生成
        -   `operators.py`: Blender オペレーター
        -   `properties.py`: カスタムプロパティ
        -   `uv_tools.py`: UV 関連ツール
        -   `weight_transfer.py`: ウェイト転送
    -   `presets/`: プリセットデータが含まれます
        -   `blendshape_maps.json`: ブレンドシェイプマップのプリセット
        -   `fit_profiles.json`: フィットプロファイルのプリセット
        -   `materials.json`: マテリアルのプリセット
        -   `wear_types.json`: ウェアタイプのプリセット
    -   `services/`: サービスレイヤー
        -   `asset_manager.py`: アセット管理
        -   `logging_service.py`: ロギングサービス
        -   `vrc_utils.py`: VRChat 関連ユーティリティ
    -   `tests/`: テストコード
        -   `run_tests.py`: テスト実行スクリプト
        -   その他の `test_*.py`: 各モジュールのテストファイル
    -   `ui/`: ユーザーインターフェース関連
        -   `panel_*.py`: 各パネルの UI 定義
        -   `ui_utils.py`: UI ユーティリティ関数
-   `docs/`: ドキュメント
    -   `basic_prompts.md`: 基本的なプロンプト例
    -   `blender_testing_notes.md`: Blender テストに関するノート
    -   `config.txt`: 設定ファイル例
    -   `商品名.md`: 製品名決定に関する議事録
    -   `失敗した知見1.txt`: 失敗した知見の記録
    -   `要件定義書.txt`: 要件定義書
-   `package.bat`, `package.sh`: アドオンをパッケージ化するためのスクリプト