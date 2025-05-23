# services/logging_service.py

import logging
import os
import bpy

# アドオンのルート名
ADDON_NAME = "AdaptiveWearGeneratorPro"

# グローバルなロガーインスタンス
_logger = None


def get_addon_logger():
    """アドオン用の設定済みロガーインスタンスを返します。"""
    global _logger
    if _logger is None:
        print(
            f"警告: {ADDON_NAME} のロガーが初期化されていません。基本的なロガーを使用します。"
        )
        return logging.getLogger(ADDON_NAME)
    return _logger


def initialize_logging(
    log_level=logging.DEBUG, log_to_file=True, log_filename="addon.log"
):
    """アドオンのロギングシステムを初期化します。"""
    global _logger
    _logger = logging.getLogger(ADDON_NAME)
    _logger.setLevel(log_level)

    # 既存のハンドラをすべて削除
    while _logger.hasHandlers():
        _logger.removeHandler(_logger.handlers[0])

    # フォーマッターの作成
    formatter = logging.Formatter(
        fmt="[%(asctime)s.%(msecs)03d] [%(levelname)s] [%(name)s:%(module)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # コンソールハンドラの作成と設定
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)

    # ファイルハンドラの作成と設定
    if log_to_file:
        try:
            addon_prefs_dir = bpy.utils.user_resource("SCRIPTS", path="addons")
            log_dir = os.path.join(addon_prefs_dir, ADDON_NAME, "logs")
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            log_file_path = os.path.join(log_dir, log_filename)

            file_handler = logging.FileHandler(
                log_file_path, mode="a", encoding="utf-8"
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            _logger.addHandler(file_handler)
            _logger.info(f"ログファイルへの出力を開始しました: {log_file_path}")
        except Exception as e:
            _logger.error(
                f"ログファイルハンドラの初期化に失敗しました: {e}", exc_info=True
            )

    _logger.info(
        f"'{ADDON_NAME}' のロギングサービスが初期化されました。ログレベル: {logging.getLevelName(log_level)}"
    )


def shutdown_logging():
    """ロギングシステムをシャットダウンします。"""
    global _logger
    if _logger and _logger.hasHandlers():
        _logger.info(f"'{ADDON_NAME}' のロギングサービスをシャットダウンします。")
        for handler in _logger.handlers[:]:
            try:
                handler.flush()
                handler.close()
            except Exception as e:
                print(f"エラー: ハンドラのクローズに失敗 - {handler}: {e}")
            _logger.removeHandler(handler)
    _logger = None


# --- 便利関数（既存コードとの互換性のため） ---


def log_debug(message):
    """デバッグレベルのログを出力"""
    logger = get_addon_logger()
    logger.debug(message)


def log_info(message):
    """情報レベルのログを出力"""
    logger = get_addon_logger()
    logger.info(message)


def log_warning(message):
    """警告レベルのログを出力"""
    logger = get_addon_logger()
    logger.warning(message)


def log_error(message):
    """エラーレベルのログを出力"""
    logger = get_addon_logger()
    logger.error(message)


def log_critical(message):
    """クリティカルレベルのログを出力"""
    logger = get_addon_logger()
    logger.critical(message)


# 登録用のクラスリスト（空のタプル - このモジュールには登録するクラスはない）
classes = ()
