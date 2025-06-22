#!/usr/bin/env python3
"""Discord音楽リンク収集Bot 起動スクリプト
設定確認と起動を行います
"""

import os
import sys
from pathlib import Path


def check_env_file():
    """環境変数ファイルの存在確認"""
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env ファイルが見つかりません")
        print("📋 env_template.txt を .env にコピーして、必要な値を設定してください")
        return False
    print("✅ .env ファイルが見つかりました")
    return True


def check_oauth_credentials():
    """OAuth認証情報ファイルの存在確認"""
    oauth_file = Path("./data/youtube_oauth_credentials.json")
    if not oauth_file.exists():
        print("❌ YouTube OAuth認証情報ファイルが見つかりません")
        print("📋 Google Cloud Consoleから認証情報をダウンロードして")
        print("   ./data/youtube_oauth_credentials.json として保存してください")
        return False
    print("✅ YouTube OAuth認証情報ファイルが見つかりました")
    return True


def check_required_env_vars():
    """必須環境変数の確認"""
    from dotenv import load_dotenv

    load_dotenv()

    required_vars = [
        "DISCORD_BOT_TOKEN",
        "YOUTUBE_API_KEY",
        "YOUTUBE_PLAYLIST_ID",
    ]

    optional_vars = [
        "SOUNDCLOUD_CLIENT_ID",
        "SOUNDCLOUD_CLIENT_SECRET",
        "SOUNDCLOUD_PLAYLIST_ID",
    ]

    missing_required = []
    missing_optional = []

    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)

    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)

    if missing_required:
        print(f"❌ 必須環境変数が設定されていません: {', '.join(missing_required)}")
        print("📋 .env ファイルで以下の値を設定してください:")
        for var in missing_required:
            print(f"   {var}=your_actual_value")
        return False

    print("✅ 必須環境変数が設定されています")

    if missing_optional:
        print(f"⚠️  SoundCloud機能用の環境変数が未設定: {', '.join(missing_optional)}")
        print("�� SoundCloud機能を使用する場合は以下も設定してください:")
        for var in missing_optional:
            print(f"   {var}=your_actual_value")
        print("💡 SoundCloud設定の詳細は SOUNDCLOUD_API.md を参照してください")
    else:
        print("✅ SoundCloud環境変数も設定されています")

    return True


def main():
    """メイン関数"""
    print("🎵 Discord音楽リンク収集Bot 起動スクリプト")
    print("=" * 50)

    # 設定確認
    print("📋 設定確認中...")

    checks = [
        check_env_file(),
        check_required_env_vars(),
        check_oauth_credentials(),
    ]

    if not all(checks):
        print("\n❌ 設定が不完全です。上記の問題を解決してから再度実行してください。")
        print("📖 詳細はREADME.mdを参照してください。")
        sys.exit(1)

    print("\n✅ 基本設定が完了しています")
    print("🚀 Botを起動します...\n")

    # dataディレクトリの作成
    Path("./data").mkdir(exist_ok=True)

    # Bot起動
    try:
        import asyncio

        sys.path.append("src")
        from main import main as bot_main

        asyncio.run(bot_main())
    except KeyboardInterrupt:
        print("\n⏹️ Bot停止が要求されました")
    except Exception as e:
        print(f"\n❌ Bot実行中にエラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
