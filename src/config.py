"""Bot設定管理モジュール
"""

import os
from pathlib import Path


class BotConfig:
    """Bot設定クラス"""

    def __init__(self) -> None:
        """設定を環境変数から読み込み"""
        # Discord設定
        self.discord_token: str | None = os.getenv("DISCORD_BOT_TOKEN")

        # YouTube API設定
        self.youtube_api_key: str | None = os.getenv("YOUTUBE_API_KEY")
        self.youtube_client_id: str | None = os.getenv("YOUTUBE_CLIENT_ID")
        self.youtube_client_secret: str | None = os.getenv("YOUTUBE_CLIENT_SECRET")
        self.youtube_playlist_id: str | None = os.getenv("YOUTUBE_PLAYLIST_ID")

        # SoundCloud API設定
        self.soundcloud_client_id: str | None = os.getenv("SOUNDCLOUD_CLIENT_ID")
        self.soundcloud_client_secret: str | None = os.getenv("SOUNDCLOUD_CLIENT_SECRET")
        self.soundcloud_playlist_id: str | None = os.getenv("SOUNDCLOUD_PLAYLIST_ID")

        # その他設定
        self.database_path: Path = Path(os.getenv("DATABASE_PATH", "./data/bot_data.db"))
        self.log_level: str = os.getenv("LOG_LEVEL", "INFO")

    def validate_required_settings(self) -> list[str]:
        """必須設定の検証"""
        missing = []

        if not self.discord_token:
            missing.append("DISCORD_BOT_TOKEN")

        if not self.youtube_api_key:
            missing.append("YOUTUBE_API_KEY")

        if not self.youtube_playlist_id:
            missing.append("YOUTUBE_PLAYLIST_ID")

        return missing

    @property
    def is_soundcloud_available(self) -> bool:
        """SoundCloudサービスが利用可能かどうか"""
        return bool(
            self.soundcloud_client_id
            and self.soundcloud_client_secret
            and self.soundcloud_playlist_id,
        )

    @property
    def oauth_credentials_file(self) -> Path:
        """OAuth認証情報ファイルのパス"""
        return Path("./data/youtube_oauth_credentials.json")

    @property
    def oauth_token_file(self) -> Path:
        """OAuthトークンファイルのパス"""
        return Path("./data/youtube_oauth_token.json")

    @property
    def soundcloud_token_file(self) -> Path:
        """SoundCloudトークンファイルのパス"""
        return Path("./data/soundcloud_oauth_token.json")
