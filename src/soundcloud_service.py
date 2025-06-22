"""SoundCloud API サービスモジュール
OAuth 2.1 (PKCE) 認証とプレイリスト管理機能
"""

import base64
import hashlib
import json
import logging
import secrets
import webbrowser
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlencode

import aiohttp

from config import BotConfig


class SoundCloudService:
    """SoundCloud API サービスクラス"""

    # SoundCloud API エンドポイント
    AUTH_URL = "https://secure.soundcloud.com/authorize"
    TOKEN_URL = "https://secure.soundcloud.com/oauth/token"
    API_BASE = "https://api.soundcloud.com"

    # OAuth スコープ
    SCOPES = ["non-expiring"]  # プレイリスト管理に必要

    def __init__(self) -> None:
        """SoundCloud サービスを初期化"""
        self.config = BotConfig()
        self.access_token: Optional[str] = None
        self.client_session: Optional[aiohttp.ClientSession] = None

    async def initialize(self) -> None:
        """SoundCloud API サービスを初期化"""
        try:
            self.client_session = aiohttp.ClientSession()

            # 保存されたトークンがあるかチェック
            await self._load_saved_token()

            if not self.access_token:
                # 認証が必要
                if not self.config.soundcloud_client_id or not self.config.soundcloud_client_secret:
                    logging.warning("SoundCloud API認証情報が設定されていません")
                    return

                logging.info("SoundCloud OAuth認証を開始します...")
                await self._authenticate()

            logging.info("SoundCloud API サービスを初期化しました")

        except Exception as e:
            logging.exception(f"SoundCloud API 初期化エラー: {e}")

    async def _load_saved_token(self) -> None:
        """保存されたアクセストークンを読み込み"""
        token_file = self.config.soundcloud_token_file
        if token_file.exists():
            try:
                with open(token_file, encoding="utf-8") as f:
                    token_data = json.load(f)
                self.access_token = token_data.get("access_token")

                # トークンの有効性を確認
                if await self._validate_token():
                    logging.info("保存されたSoundCloudトークンを読み込みました")
                else:
                    logging.warning("保存されたSoundCloudトークンが無効です")
                    self.access_token = None

            except Exception as e:
                logging.exception(f"SoundCloudトークン読み込みエラー: {e}")

    async def _authenticate(self) -> None:
        """OAuth 2.1 (PKCE) 認証フローを実行"""
        try:
            # PKCE パラメータ生成
            code_verifier = self._generate_code_verifier()
            code_challenge = self._generate_code_challenge(code_verifier)
            state = secrets.token_urlsafe(32)

            # 認証URL構築
            auth_params = {
                "client_id": self.config.soundcloud_client_id,
                "redirect_uri": "http://localhost:8888/callback",  # ローカルサーバー
                "response_type": "code",
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
                "state": state,
                "scope": " ".join(self.SCOPES),
            }

            auth_url = f"{self.AUTH_URL}?{urlencode(auth_params)}"

            logging.info("ブラウザでSoundCloud認証画面を開きます...")
            webbrowser.open(auth_url)

            # ローカルサーバーで認証コードを受信
            auth_code = await self._wait_for_auth_code()

            if auth_code:
                # アクセストークンを取得
                await self._exchange_code_for_token(auth_code, code_verifier)
            else:
                logging.error("SoundCloud認証コードの取得に失敗しました")

        except Exception as e:
            logging.exception(f"SoundCloud認証エラー: {e}")

    def _generate_code_verifier(self) -> str:
        """PKCE code_verifier を生成"""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("utf-8").rstrip("=")

    def _generate_code_challenge(self, code_verifier: str) -> str:
        """PKCE code_challenge を生成"""
        digest = hashlib.sha256(code_verifier.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")

    async def _wait_for_auth_code(self) -> Optional[str]:
        """ローカルサーバーで認証コードを待機"""
        import asyncio

        from aiohttp import web

        auth_code = None

        async def callback_handler(request):
            nonlocal auth_code
            query_params = parse_qs(str(request.query_string))

            if "code" in query_params:
                auth_code = query_params["code"][0]
                return web.Response(text="認証成功！このウィンドウを閉じてください。")
            return web.Response(text="認証失敗", status=400)

        app = web.Application()
        app.router.add_get("/callback", callback_handler)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", 8888)
        await site.start()

        try:
            # 最大5分間待機
            for _ in range(300):
                if auth_code:
                    break
                await asyncio.sleep(1)
        finally:
            await runner.cleanup()

        return auth_code

    async def _exchange_code_for_token(self, auth_code: str, code_verifier: str) -> None:
        """認証コードをアクセストークンに交換"""
        token_data = {
            "grant_type": "authorization_code",
            "client_id": self.config.soundcloud_client_id,
            "client_secret": self.config.soundcloud_client_secret,
            "redirect_uri": "http://localhost:8888/callback",
            "code": auth_code,
            "code_verifier": code_verifier,
        }

        async with self.client_session.post(
            self.TOKEN_URL,
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as response:
            if response.status == 200:
                token_response = await response.json()
                self.access_token = token_response.get("access_token")

                # トークンを保存
                await self._save_token(token_response)
                logging.info("SoundCloudアクセストークンを取得しました")
            else:
                error_text = await response.text()
                logging.error(f"SoundCloudトークン取得エラー: {response.status} - {error_text}")

    async def _save_token(self, token_data: Dict) -> None:
        """アクセストークンを保存"""
        token_file = self.config.soundcloud_token_file
        token_file.parent.mkdir(parents=True, exist_ok=True)

        with open(token_file, "w", encoding="utf-8") as f:
            json.dump(token_data, f, indent=2)

    async def _validate_token(self) -> bool:
        """トークンの有効性を確認"""
        if not self.access_token:
            return False

        try:
            async with self.client_session.get(
                f"{self.API_BASE}/me",
                headers={"Authorization": f"OAuth {self.access_token}"},
            ) as response:
                return response.status == 200
        except:
            return False

    async def resolve_url(self, url: str) -> Optional[Dict]:
        """SoundCloud URLからトラック情報を解決"""
        if not self.access_token:
            logging.warning("SoundCloudアクセストークンがありません")
            return None

        try:
            params = {"url": url}

            async with self.client_session.get(
                f"{self.API_BASE}/resolve",
                params=params,
                headers={"Authorization": f"OAuth {self.access_token}"},
            ) as response:
                if response.status == 200:
                    return await response.json()
                logging.error(f"SoundCloud URL解決エラー: {response.status}")
                return None

        except Exception as e:
            logging.exception(f"SoundCloud URL解決中にエラー: {e}")
            return None

    async def add_to_playlist(self, url: str) -> bool:
        """SoundCloud プレイリストにトラックを追加"""
        if not self.access_token:
            logging.warning("SoundCloudアクセストークンがありません")
            return False

        if not self.config.soundcloud_playlist_id:
            logging.error("SoundCloudプレイリストIDが設定されていません")
            return False

        try:
            # URLからトラック情報を解決
            track_info = await self.resolve_url(url)
            if not track_info:
                logging.error(f"SoundCloudトラックの解決に失敗: {url}")
                return False

            track_id = track_info.get("id")
            if not track_id:
                logging.error("SoundCloudトラックIDが見つかりません")
                return False

            # 重複チェック
            if await self._is_track_in_playlist(track_id):
                logging.info(f"トラックは既にプレイリストに存在します: {track_id}")
                return True

            # プレイリストにトラックを追加
            playlist_data = {
                "playlist": {
                    "tracks": [{"id": track_id}],
                },
            }

            async with self.client_session.put(
                f"{self.API_BASE}/playlists/{self.config.soundcloud_playlist_id}",
                json=playlist_data,
                headers={
                    "Authorization": f"OAuth {self.access_token}",
                    "Content-Type": "application/json",
                },
            ) as response:
                if response.status in [200, 201]:
                    logging.info(f"SoundCloudプレイリストにトラックを追加しました: {track_id}")
                    return True
                error_text = await response.text()
                logging.error(f"SoundCloudプレイリスト追加エラー: {response.status} - {error_text}")
                return False

        except Exception as e:
            logging.exception(f"SoundCloudプレイリスト追加中にエラー: {e}")
            return False

    async def _is_track_in_playlist(self, track_id: int) -> bool:
        """トラックがプレイリストに既に存在するかチェック"""
        try:
            async with self.client_session.get(
                f"{self.API_BASE}/playlists/{self.config.soundcloud_playlist_id}",
                headers={"Authorization": f"OAuth {self.access_token}"},
            ) as response:
                if response.status == 200:
                    playlist_data = await response.json()
                    tracks = playlist_data.get("tracks", [])

                    return any(track.get("id") == track_id for track in tracks)
                logging.error(f"プレイリスト取得エラー: {response.status}")
                return False

        except Exception as e:
            logging.exception(f"プレイリスト重複チェック中にエラー: {e}")
            return False

    async def get_track_title(self, track_id: int) -> Optional[str]:
        """トラックのタイトルを取得"""
        if not self.access_token:
            return None

        try:
            async with self.client_session.get(
                f"{self.API_BASE}/tracks/{track_id}",
                headers={"Authorization": f"OAuth {self.access_token}"},
            ) as response:
                if response.status == 200:
                    track_data = await response.json()
                    return track_data.get("title")
                return None

        except Exception as e:
            logging.exception(f"SoundCloudトラック情報取得エラー: {e}")
            return None

    async def search_tracks(self, query: str, limit: int = 10) -> List[Dict]:
        """トラックを検索"""
        if not self.access_token:
            return []

        try:
            params = {
                "q": query,
                "limit": limit,
                "linked_partitioning": "true",
            }

            async with self.client_session.get(
                f"{self.API_BASE}/tracks",
                params=params,
                headers={"Authorization": f"OAuth {self.access_token}"},
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("collection", [])
                return []

        except Exception as e:
            logging.exception(f"SoundCloud検索エラー: {e}")
            return []

    async def close(self) -> None:
        """リソースをクリーンアップ"""
        if self.client_session:
            await self.client_session.close()
