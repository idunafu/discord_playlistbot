"""Discord音楽リンク収集Bot
YouTubeとSoundCloudのリンクを自動でプレイリストに追加するBot
"""

import asyncio
import logging
import os
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

from config import BotConfig
from database import DatabaseManager
from music_services import YouTubeService
from soundcloud_service import SoundCloudService
from url_extractor import URLExtractor


class MusicPlaylistBot(commands.Bot):
    """音楽プレイリスト収集Bot"""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        super().__init__(
            command_prefix="!",  # スラッシュコマンド使用のため、プレフィックスは使用しない
            intents=intents,
            help_command=None,
        )

        self.config = BotConfig()
        self.db_manager = DatabaseManager()
        self.youtube_service = YouTubeService()

        # SoundCloudサービスは設定がある場合のみ初期化
        if self.config.is_soundcloud_available:
            self.soundcloud_service = SoundCloudService()
            logging.info("SoundCloud設定を検出しました")
        else:
            self.soundcloud_service = None
            logging.info("SoundCloud設定が見つかりません。YouTubeのみで動作します")

        self.url_extractor = URLExtractor()

    async def setup_hook(self) -> None:
        """Bot起動時の初期設定"""
        await self.db_manager.initialize()
        await self.youtube_service.initialize()

        # SoundCloudサービスがある場合のみ初期化
        if self.soundcloud_service:
            await self.soundcloud_service.initialize()

        # スラッシュコマンドを同期
        try:
            synced = await self.tree.sync()
            logging.info(f"同期されたスラッシュコマンド: {len(synced)}個")
        except Exception as e:
            logging.exception(f"スラッシュコマンドの同期に失敗: {e}")

    async def on_ready(self) -> None:
        """Bot起動完了時の処理"""
        logging.info(f"{self.user} としてログインしました")
        logging.info(f"Bot ID: {self.user.id}")
        services = ["YouTube"]
        if self.soundcloud_service:
            services.append("SoundCloud")
        logging.info(f"音楽リンク収集Botが起動しました（対応サービス: {', '.join(services)}）")

    async def on_message(self, message: discord.Message) -> None:
        """メッセージ受信時の処理"""
        # Bot自身またはその他のBotのメッセージは無視
        if message.author.bot:
            return

        # 監視対象チャンネルかチェック
        monitored_channel_id = await self.db_manager.get_monitored_channel(message.guild.id)
        if not monitored_channel_id or message.channel.id != monitored_channel_id:
            return

        # URLを抽出
        urls = self.url_extractor.extract_urls(message.content)
        if not urls:
            return

        # 各URLを処理
        for url in urls:
            await self._process_music_url(url, message)

    async def _process_music_url(self, url: str, message: discord.Message) -> None:
        """音楽URLの処理"""
        try:
            service_type = self.url_extractor.identify_service(url)

            if service_type == "youtube":
                success = await self.youtube_service.add_to_playlist(url)
                if success:
                    await self._send_notification(
                        message.guild.id,
                        f"✅ YouTubeプレイリストに追加しました: {url}",
                    )
                else:
                    await self._send_notification(
                        message.guild.id,
                        f"❌ YouTubeプレイリストへの追加に失敗しました: {url}",
                    )

            elif service_type == "soundcloud":
                if self.soundcloud_service:
                    success = await self.soundcloud_service.add_to_playlist(url)
                    if success:
                        await self._send_notification(
                            message.guild.id,
                            f"✅ SoundCloudプレイリストに追加しました: {url}",
                        )
                    else:
                        await self._send_notification(
                            message.guild.id,
                            f"❌ SoundCloudプレイリストへの追加に失敗しました: {url}",
                        )
                # SoundCloudが設定されていない場合は何もしない（サイレントスキップ）

        except Exception as e:
            logging.exception(f"URL処理中にエラーが発生: {e}")
            await self._send_notification(
                message.guild.id,
                f"❌ URL処理中にエラーが発生しました: {url}",
            )

    async def _send_notification(self, guild_id: int, message: str) -> None:
        """通知メッセージの送信"""
        notification_channel_id = await self.db_manager.get_notification_channel(guild_id)
        if not notification_channel_id:
            return

        channel = self.get_channel(notification_channel_id)
        if channel:
            try:
                await channel.send(message)
            except discord.Forbidden:
                logging.warning(f"通知チャンネルへの送信権限がありません: {notification_channel_id}")
            except Exception as e:
                logging.exception(f"通知送信中にエラーが発生: {e}")

    async def close(self) -> None:
        """Botを終了"""
        if self.soundcloud_service and hasattr(self.soundcloud_service, "close"):
            await self.soundcloud_service.close()
        await super().close()


async def main() -> None:
    """メイン関数"""
    # 環境変数の読み込み
    load_dotenv()

    # ログ設定
    logging.basicConfig(
        level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("bot.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    # Botトークンの確認
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        logging.error("DISCORD_BOT_TOKENが設定されていません")
        return

    # データディレクトリの作成
    data_dir = Path("./data")
    data_dir.mkdir(exist_ok=True)

    # Bot起動
    bot = MusicPlaylistBot()

    # スラッシュコマンドをロード
    from commands import setup_commands
    await setup_commands(bot)

    try:
        await bot.start(token)
    except KeyboardInterrupt:
        logging.info("Bot停止が要求されました")
    except Exception as e:
        logging.exception(f"Bot実行中にエラーが発生: {e}")
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
