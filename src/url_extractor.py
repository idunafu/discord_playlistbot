"""URL抽出・解析モジュール
"""

import re
from typing import List, Optional
from urllib.parse import parse_qs, urlparse


class URLExtractor:
    """URL抽出・解析クラス"""

    def __init__(self) -> None:
        """URL抽出器を初期化"""
        # YouTube URL パターン
        self.youtube_patterns = [
            r"https?://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
            r"https?://youtu\.be/([a-zA-Z0-9_-]{11})",
            r"https?://(?:music\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
            r"https?://(?:m\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
        ]

        # SoundCloud URL パターン
        self.soundcloud_patterns = [
            r"https?://(?:www\.)?soundcloud\.com/[a-zA-Z0-9\-_]+/[a-zA-Z0-9\-_]+",
            r"https?://(?:m\.)?soundcloud\.com/[a-zA-Z0-9\-_]+/[a-zA-Z0-9\-_]+",
        ]

    def extract_urls(self, text: str) -> List[str]:
        """テキストから音楽サービスのURLを抽出"""
        urls = []

        # YouTube URLを抽出
        for pattern in self.youtube_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                urls.append(match.group(0))

        # SoundCloud URLを抽出
        for pattern in self.soundcloud_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                urls.append(match.group(0))

        # 重複を除去して返す
        return list(set(urls))

    def identify_service(self, url: str) -> Optional[str]:
        """URLからサービスタイプを特定"""
        url_lower = url.lower()

        if "youtube.com" in url_lower or "youtu.be" in url_lower:
            return "youtube"
        if "soundcloud.com" in url_lower:
            return "soundcloud"
        return None

    def extract_youtube_video_id(self, url: str) -> Optional[str]:
        """YouTube URLから動画IDを抽出"""
        for pattern in self.youtube_patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)

        # youtu.be形式の場合の追加処理
        parsed = urlparse(url)
        if "youtu.be" in parsed.netloc:
            return parsed.path.lstrip("/")

        # youtube.com形式でクエリパラメータから抽出
        if "youtube.com" in parsed.netloc:
            query_params = parse_qs(parsed.query)
            if "v" in query_params:
                return query_params["v"][0]

        return None

    def extract_soundcloud_track_info(self, url: str) -> Optional[dict]:
        """SoundCloud URLからトラック情報を抽出"""
        # SoundCloud APIが現在利用困難なため、基本的な情報のみ
        parsed = urlparse(url)
        if "soundcloud.com" in parsed.netloc:
            path_parts = parsed.path.strip("/").split("/")
            if len(path_parts) >= 2:
                return {
                    "user": path_parts[0],
                    "track": path_parts[1],
                    "url": url,
                }
        return None

    def validate_youtube_url(self, url: str) -> bool:
        """YouTube URLの有効性を検証"""
        video_id = self.extract_youtube_video_id(url)
        if not video_id:
            return False

        # 動画IDは11文字の英数字とハイフン・アンダースコア
        return len(video_id) == 11 and re.match(r"^[a-zA-Z0-9_-]+$", video_id) is not None

    def validate_soundcloud_url(self, url: str) -> bool:
        """SoundCloud URLの有効性を検証"""
        track_info = self.extract_soundcloud_track_info(url)
        return track_info is not None

    def normalize_youtube_url(self, url: str) -> Optional[str]:
        """YouTube URLを正規化"""
        video_id = self.extract_youtube_video_id(url)
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"
        return None

    def is_youtube_playlist(self, url: str) -> bool:
        """YouTube プレイリストURLかどうか判定"""
        parsed = urlparse(url)
        if "youtube.com" in parsed.netloc:
            query_params = parse_qs(parsed.query)
            return "list" in query_params
        return False

    def is_youtube_shorts(self, url: str) -> bool:
        """YouTube Shorts URLかどうか判定"""
        return "/shorts/" in url.lower()
