# Discord音楽リンク収集Bot 開発者ガイド

## 🚀 開発環境セットアップ

### 前提条件

- Python 3.8以上
- [uv](https://docs.astral.sh/uv/) パッケージマネージャー
- Git

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd discord_playlistbot
```

### 2. 依存関係のインストール

```bash
# uvを使用した依存関係の同期
uv sync

# 開発用の追加パッケージをインストール（将来的に）
uv add --dev ruff black mypy pytest
```

### 3. 環境変数の設定

```bash
# テンプレートから環境ファイルをコピー
cp env_template.txt .env

# 必要な値を設定
# DISCORD_BOT_TOKEN, YOUTUBE_API_KEY, YOUTUBE_PLAYLIST_ID等
```

### 4. OAuth認証ファイルの配置

YouTube OAuth認証情報を `./data/youtube_oauth_credentials.json` に配置

## 📁 プロジェクト構成

### ソースコード構成

```
src/
├── main.py                   # Botのメインクラス、Discord.pyのクライアント
├── config.py                 # 環境変数・設定管理
├── database.py               # SQLiteデータベース操作
├── url_extractor.py          # URL抽出・パターンマッチング
├── music_services.py         # YouTube Data API連携
├── soundcloud_service.py     # SoundCloud API連携
└── commands.py               # Discordスラッシュコマンド定義
```

### 各モジュールの役割

#### `main.py`

- `DiscordBot`クラス: Botのメインロジック
- `on_message`: リアルタイムメッセージ監視
- `on_ready`: Bot起動時の初期化

#### `config.py`

- `Config`クラス: 環境変数の読み込み・バリデーション
- 設定値のデフォルト値管理

#### `database.py`

- `DatabaseManager`クラス: SQLite操作の抽象化
- 非同期データベース操作（aiosqlite使用）
- サーバー設定・URL履歴の管理

#### `url_extractor.py`

- `URLExtractor`クラス: URL抽出エンジン
- 正規表現パターンマッチング
- YouTube/SoundCloudの識別・パース

#### `music_services.py`

- `YouTubeService`クラス: YouTube Data API v3連携
- OAuth 2.0認証フロー
- プレイリスト操作・動画検索

#### `soundcloud_service.py`

- `SoundCloudService`クラス: SoundCloud API連携
- OAuth 2.1 (PKCE)認証フロー
- プレイリスト操作・トラック検索

#### `commands.py`

- Discordスラッシュコマンドの定義
- `/setting`, `/backlog`, `/help`の実装

## 🛠️ 開発ワークフロー

### ブランチ戦略

```bash
# 新機能開発
git checkout -b feature/new-feature
git commit -m "feat: 新機能の説明"
git push origin feature/new-feature

# バグ修正
git checkout -b fix/bug-description
git commit -m "fix: バグ修正の説明"
git push origin fix/bug-description
```

### コミットメッセージ規約

```
type: description

Types:
- feat: 新機能
- fix: バグ修正
- docs: ドキュメント更新
- style: コードスタイル修正
- refactor: リファクタリング
- test: テスト追加・修正
- chore: ビルド・設定変更
```

## 🧪 テスト・デバッグ

### ログレベル設定

```env
# .env ファイル
LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR
```

### デバッグ実行

```bash
# 詳細ログ付きで実行
uv run python start.py

# ログファイルの監視
tail -f bot.log
```

### テストBot用の設定

開発時は別のBotトークンを使用することを推奨：

```env
# 開発用Bot設定
DISCORD_BOT_TOKEN=your_test_bot_token
YOUTUBE_PLAYLIST_ID=test_playlist_id
```

## 🔧 新機能の追加

### 1. 新しい音楽サービスの追加

新サービス（例：Spotify）を追加する場合：

```python
# src/spotify_service.py
class SpotifyService:
    def __init__(self):
        # 初期化
        pass
    
    async def add_to_playlist(self, track_url: str, playlist_id: str):
        # プレイリスト追加ロジック
        pass
```

### 2. URL抽出パターンの追加

```python
# src/url_extractor.py
class URLExtractor:
    def __init__(self):
        self.patterns = {
            'youtube': [
                # 既存パターン
            ],
            'spotify': [  # 新しいサービス
                r'https?://open\.spotify\.com/track/([a-zA-Z0-9]+)',
                r'https?://spotify\.link/([a-zA-Z0-9]+)',
            ]
        }
```

### 3. 新しいスラッシュコマンドの追加

```python
# src/commands.py
@app_commands.command(name="stats", description="統計情報を表示")
async def stats_command(interaction: discord.Interaction):
    # 統計表示ロジック
    await interaction.response.send_message("統計情報")
```

## 🔍 APIの使用方法

### YouTube Data API

```python
from src.music_services import YouTubeService

# サービス初期化
youtube = YouTubeService()
await youtube.initialize()

# プレイリストに動画追加
result = await youtube.add_to_playlist("dQw4w9WgXcQ", "PLxxxxxx")
```

### SoundCloud API

```python
from src.soundcloud_service import SoundCloudService

# サービス初期化
soundcloud = SoundCloudService()
await soundcloud.initialize()

# プレイリストにトラック追加
result = await soundcloud.add_to_playlist("soundcloud-url", "playlist-id")
```

### データベース操作

```python
from src.database import DatabaseManager

# データベース初期化
db = DatabaseManager()
await db.initialize()

# サーバー設定の保存
await db.set_server_settings(guild_id, monitored_channel, notification_channel)

# URL履歴の保存
await db.add_processed_url(guild_id, url, "youtube", video_id, title)
```

## 🐛 トラブルシューティング

### よくある問題

#### 1. OAuth認証エラー

```bash
# 認証ファイルを削除して再認証
rm ./data/youtube_oauth_token.json
rm ./data/soundcloud_oauth_token.json

# Bot再起動
uv run python start.py
```

#### 2. API制限エラー

```python
# レート制限処理の確認
# src/music_services.py または src/soundcloud_service.py で
# リトライロジックを確認
```

#### 3. データベースエラー

```bash
# データベースファイルの確認
ls -la ./data/bot_data.db

# 必要に応じてデータベースを再初期化
rm ./data/bot_data.db
```

### ログ分析

```bash
# エラーログの抽出
grep "ERROR" bot.log

# 特定時間のログ
grep "2024-12-" bot.log | tail -100
```

## 📊 パフォーマンス最適化

### 非同期処理の活用

```python
# 並列処理でAPI呼び出し最適化
import asyncio

async def process_multiple_urls(urls):
    tasks = []
    for url in urls:
        task = asyncio.create_task(process_single_url(url))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### データベース最適化

```sql
-- インデックスの追加
CREATE INDEX idx_guild_url ON processed_urls(guild_id, url);
CREATE INDEX idx_processed_at ON processed_urls(processed_at);
```

## 🔐 セキュリティ考慮事項

### 1. 認証情報の管理

```bash
# 認証ファイルの権限設定
chmod 600 ./data/*.json
chmod 600 .env
```

### 2. 入力値のバリデーション

```python
# URL検証の強化
def validate_url(url: str) -> bool:
    # セキュリティチェック
    if len(url) > 2048:  # URL長制限
        return False
    # その他のバリデーション
    return True
```

## 📚 参考資料

### API仕様書

- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [YouTube Data API v3](https://developers.google.com/youtube/v3)
- [SoundCloud API Guide](https://developers.soundcloud.com/docs/api/guide)

### Python開発

- [Python 非同期プログラミング](https://docs.python.org/3/library/asyncio.html)
- [aiohttp Documentation](https://docs.aiohttp.org/)
- [aiosqlite Documentation](https://aiosqlite.omnilib.dev/)

## 🤝 コントリビューション

### Pull Request手順

1. Issueの作成（バグ報告・機能要求）
2. フォーク・ブランチ作成
3. 実装・テスト
4. Pull Request作成
5. コードレビュー
6. マージ

### コードスタイル

```bash
# フォーマット（将来的）
ruff format src/
ruff check src/

# 型チェック（将来的）
mypy src/
```

プロジェクトに貢献する際は、このガイドに従って開発を進めてください。質問があれば、Issueで気軽にお尋ねください！
