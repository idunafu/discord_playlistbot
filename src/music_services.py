"""音楽サービス連携モジュール

YouTube APIとSoundCloud API（将来実装）
"""

import json
import logging
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import BotConfig
from url_extractor import URLExtractor


class YouTubeService:
    """YouTube API サービスクラス"""

    SCOPES: list[str] = ["https://www.googleapis.com/auth/youtube"]

    def __init__(self) -> None:
        """YouTube サービスを初期化"""
        self.config = BotConfig()
        self.url_extractor = URLExtractor()
        self.service = None
        self.credentials = None

    async def initialize(self) -> None:
        """YouTube API サービスを初期化"""
        try:
            self.credentials = await self._get_credentials()
            if self.credentials:
                self.service = build("youtube", "v3", credentials=self.credentials)
                logging.info("YouTube API サービスを初期化しました")
            else:
                logging.warning("YouTube API の認証情報が見つかりません")
        except Exception as e:
            logging.exception(f"YouTube API 初期化エラー: {e}")

    async def _get_credentials(self) -> Any:
        """OAuth認証情報を取得"""
        creds = None
        token_file = self.config.oauth_token_file

        # 保存されたトークンがあるかチェック
        if token_file.exists():
            creds = Credentials.from_authorized_user_file(str(token_file), self.SCOPES)

        # 認証情報が無効または期限切れの場合
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logging.exception(f"トークンのリフレッシュに失敗: {e}")
                    creds = None

            if not creds:
                credentials_file = self.config.oauth_credentials_file
                if not credentials_file.exists():
                    logging.error(
                        f"OAuth認証情報ファイルが見つかりません: {credentials_file}\n"
                        "Google Cloud Consoleから認証情報をダウンロードして配置してください。",
                    )
                    return None

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(credentials_file),
                        self.SCOPES,
                    )
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    logging.exception(f"OAuth認証に失敗: {e}")
                    return None

            # トークンを保存
            if creds:
                token_file.parent.mkdir(parents=True, exist_ok=True)
                with open(token_file, "w", encoding="utf-8") as token:
                    token.write(creds.to_json())

        return creds

    async def add_to_playlist(self, url: str) -> bool:
        """YouTube プレイリストに動画を追加"""
        if not self.service:
            logging.error("YouTube API サービスが初期化されていません")
            return False

        if not self.config.youtube_playlist_id:
            logging.error("YouTube プレイリストIDが設定されていません")
            return False

        # 動画IDを抽出
        video_id = self.url_extractor.extract_youtube_video_id(url)
        if not video_id:
            logging.error(f"YouTubeの動画IDを抽出できませんでした: {url}")
            return False

        try:
            # 重複チェック
            if await self._is_video_in_playlist(video_id):
                logging.info(f"動画は既にプレイリストに存在します: {video_id}")
                return True

            # プレイリストに追加
            request = self.service.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": self.config.youtube_playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id,
                        },
                    },
                },
            )

            response = request.execute()
            logging.info(f"YouTube プレイリストに動画を追加しました: {video_id}")
            return True

        except HttpError as e:
            error_details = json.loads(e.content.decode("utf-8"))
            error_message = error_details.get("error", {}).get("message", str(e))

            if "videoNotFound" in str(e):
                logging.warning(
                    f"動画が見つかりません（削除済みまたは非公開）: {video_id}",
                )
            elif "playlistNotFound" in str(e):
                logging.exception(
                    f"プレイリストが見つかりません: {self.config.youtube_playlist_id}",
                )
            else:
                logging.exception(f"YouTube API エラー: {error_message}")

            return False

        except Exception as e:
            logging.exception(f"予期しないエラーが発生しました: {e}")
            return False

    async def _is_video_in_playlist(self, video_id: str) -> bool:
        """動画がプレイリストに既に存在するかチェック"""
        if not self.service:
            logging.error("YouTube API サービスが初期化されていません")
            return False

        try:
            request = self.service.playlistItems().list(
                part="snippet",
                playlistId=self.config.youtube_playlist_id,
                maxResults=50,  # 最大50件ずつチェック
            )

            while request is not None:
                response = request.execute()

                for item in response.get("items", []):
                    if item["snippet"]["resourceId"]["videoId"] == video_id:
                        return True

                request = self.service.playlistItems().list_next(request, response)

            return False

        except HttpError as e:
            logging.exception(f"プレイリスト重複チェック中にエラー: {e}")
            return False

    async def get_video_title(self, video_id: str) -> str | None:
        """動画のタイトルを取得"""
        if not self.service:
            return None

        try:
            request = self.service.videos().list(
                part="snippet",
                id=video_id,
            )
            response = request.execute()

            items = response.get("items", [])
            if items:
                return items[0]["snippet"]["title"]

            return None

        except HttpError as e:
            logging.exception(f"動画情報取得エラー: {e}")
            return None


# SoundCloudServiceは soundcloud_service.py で実装されています
# 使用する場合は以下をインポート:
# from soundcloud_service import SoundCloudService
