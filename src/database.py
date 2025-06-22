"""データベース管理モジュール
"""

import logging
from pathlib import Path
from typing import Optional

import aiosqlite


class DatabaseManager:
    """データベース管理クラス"""

    def __init__(self, db_path: Path = Path("./data/bot_data.db")) -> None:
        """データベースマネージャーを初期化"""
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self) -> None:
        """データベースとテーブルを初期化"""
        async with aiosqlite.connect(self.db_path) as db:
            # サーバー設定テーブル
            await db.execute("""
                CREATE TABLE IF NOT EXISTS server_settings (
                    guild_id INTEGER PRIMARY KEY,
                    monitored_channel_id INTEGER,
                    notification_channel_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 処理済みURL履歴テーブル（重複チェック用）
            await db.execute("""
                CREATE TABLE IF NOT EXISTS processed_urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    url TEXT NOT NULL,
                    service_type TEXT NOT NULL,
                    video_id TEXT,
                    title TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, url)
                )
            """)

            # インデックス作成
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_processed_urls_guild_url 
                ON processed_urls(guild_id, url)
            """)

            await db.commit()
            logging.info("データベースを初期化しました")

    async def set_monitored_channel(self, guild_id: int, channel_id: int) -> None:
        """監視対象チャンネルを設定"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO server_settings (guild_id, monitored_channel_id)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                    monitored_channel_id = excluded.monitored_channel_id,
                    updated_at = CURRENT_TIMESTAMP
            """, (guild_id, channel_id))
            await db.commit()
            logging.info(f"Guild {guild_id}: 監視チャンネル設定 -> {channel_id}")

    async def get_monitored_channel(self, guild_id: int) -> Optional[int]:
        """監視対象チャンネルを取得"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT monitored_channel_id FROM server_settings WHERE guild_id = ?
            """, (guild_id,))
            row = await cursor.fetchone()
            return row[0] if row and row[0] else None

    async def set_notification_channel(self, guild_id: int, channel_id: Optional[int]) -> None:
        """通知チャンネルを設定"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO server_settings (guild_id, notification_channel_id)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                    notification_channel_id = excluded.notification_channel_id,
                    updated_at = CURRENT_TIMESTAMP
            """, (guild_id, channel_id))
            await db.commit()
            logging.info(f"Guild {guild_id}: 通知チャンネル設定 -> {channel_id}")

    async def get_notification_channel(self, guild_id: int) -> Optional[int]:
        """通知チャンネルを取得"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT notification_channel_id FROM server_settings WHERE guild_id = ?
            """, (guild_id,))
            row = await cursor.fetchone()
            return row[0] if row and row[0] else None

    async def is_url_processed(self, guild_id: int, url: str) -> bool:
        """URLが既に処理済みかチェック"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT 1 FROM processed_urls WHERE guild_id = ? AND url = ?
            """, (guild_id, url))
            return await cursor.fetchone() is not None

    async def mark_url_processed(
        self,
        guild_id: int,
        url: str,
        service_type: str,
        video_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> None:
        """URLを処理済みとしてマーク"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO processed_urls 
                (guild_id, url, service_type, video_id, title)
                VALUES (?, ?, ?, ?, ?)
            """, (guild_id, url, service_type, video_id, title))
            await db.commit()

    async def get_server_settings(self, guild_id: int) -> dict:
        """サーバー設定を取得"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT monitored_channel_id, notification_channel_id 
                FROM server_settings WHERE guild_id = ?
            """, (guild_id,))
            row = await cursor.fetchone()

            if row:
                return {
                    "monitored_channel_id": row[0],
                    "notification_channel_id": row[1],
                }
            return {
                "monitored_channel_id": None,
                "notification_channel_id": None,
            }

    async def cleanup_old_urls(self, days: int = 30) -> None:
        """古いURL履歴をクリーンアップ"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"""
                DELETE FROM processed_urls 
                WHERE processed_at < datetime('now', '-{days} days')
            """)
            await db.commit()
            logging.info(f"{days}日以前の古いURL履歴をクリーンアップしました")
