# Discord音楽リンク収集Bot

YouTubeとSoundCloudのリンクを自動でプレイリストに追加するDiscord Bot

## 🎯 機能

- **自動リンク検出**: Discordの特定チャンネルでYouTubeとSoundCloudのURLを自動検出
- **プレイリスト追加**: 検出したURLを指定したYouTubeプレイリストに自動追加（SoundCloudは設定した場合のみ）
- **重複チェック**: 既に追加済みの動画・トラックは再度追加しない
- **スラッシュコマンド**: `/setting`, `/backlog`, `/help` コマンドで簡単設定
- **過去ログ処理**: 過去のメッセージを遡ってURLを一括処理
- **柔軟な設定**: SoundCloud APIなしでもYouTubeのみで動作可能

## 📋 必要な準備

### 1. Discord Bot トークンの取得

1. [Discord Developer Portal](https://discord.com/developers/applications) にアクセス
2. 「New Application」をクリックしてアプリケーションを作成
3. 左メニューの「Bot」をクリック
4. 「Reset Token」をクリックしてトークンを生成・コピー
5. Bot Permissions: `Send Messages`, `Use Slash Commands`, `Read Message History` を有効化

### 2. YouTube API 設定

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成または既存のプロジェクトを選択
3. YouTube Data API v3 を有効化
4. 認証情報を作成:
   - **APIキー**: YouTube Data API v3 用
   - **OAuth 2.0 クライアントID**: デスクトップアプリケーション用
5. OAuth 2.0 クライアントIDの認証情報JSONファイルをダウンロード

### 3. YouTube プレイリスト ID の取得

1. YouTubeでプレイリストを作成または既存のプレイリストを開く
2. URLから `list=` の後の文字列をコピー
   - 例: `https://www.youtube.com/playlist?list=PLxxxxxxxxxxxxxxxxxxxxxx`
   - プレイリストID: `PLxxxxxxxxxxxxxxxxxxxxxx`

### 4. SoundCloud API 設定（オプション）

**注意**: SoundCloud APIの設定は必須ではありません。設定しない場合、YouTubeのみで動作します。

1. [SoundCloud Developer](https://developers.soundcloud.com/) にアクセス
2. 「Register a new application」をクリック
3. アプリケーション情報を入力:
   - **Redirect URI**: `http://localhost:8888/callback`
4. **Client ID** と **Client Secret** をコピー

### 5. SoundCloud プレイリスト ID の取得（オプション）

1. SoundCloudでプレイリストを作成
2. ブラウザの開発者ツールを使用してプレイリストIDを取得
   - 詳細は `SOUNDCLOUD_API.md` を参照

## 🚀 セットアップ

### 1. リポジトリのクローン

```bash
git clone <this-repository>
cd discord_playlistbot
```

### 2. 依存関係のインストール

```bash
uv sync
```

### 3. 環境変数の設定

1. `env_template.txt` を `.env` にコピー
2. 必要な値を設定:

```env
# 必須設定
DISCORD_BOT_TOKEN=your_actual_discord_bot_token
YOUTUBE_API_KEY=your_actual_youtube_api_key
YOUTUBE_PLAYLIST_ID=your_actual_youtube_playlist_id

# オプション設定（SoundCloudを使用する場合のみ）
SOUNDCLOUD_CLIENT_ID=your_actual_soundcloud_client_id
SOUNDCLOUD_CLIENT_SECRET=your_actual_soundcloud_client_secret
SOUNDCLOUD_PLAYLIST_ID=your_actual_soundcloud_playlist_id
```

### 4. YouTube OAuth 認証情報の配置

1. Google Cloud Consoleからダウンロードした認証情報JSONファイルを
   `./data/youtube_oauth_credentials.json` として保存

### 5. Bot の起動

```bash
uv run python start.py
```

初回起動時に、ブラウザでYouTubeとSoundCloudの認証画面が開きます。
認証を完了すると、以降は自動でアクセストークンが更新されます。

## 📱 Discord での使用方法

### 1. Bot をサーバーに招待

Discord Developer Portal で生成した招待URLを使用して、BotをDiscordサーバーに招待してください。

### 2. 基本設定

```sh
/setting monitor #music-links
```

音楽リンクを監視するチャンネルを設定

```sh
/setting notification #bot-notifications
```

処理結果を通知するチャンネルを設定

### 3. 設定確認

```sh
/setting show
```

現在の設定を表示

### 4. 過去ログ処理

```sh
/backlog 50
```

過去50件のメッセージからURLを抽出して処理

### 5. ヘルプ

```sh
/help
```

コマンド一覧と使い方を表示

## 🎵 対応URL形式

### YouTube

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://music.youtube.com/watch?v=VIDEO_ID`

### SoundCloud（設定した場合のみ）

- `https://soundcloud.com/user/track`
- `https://soundcloud.com/user/sets/playlist`

**注意**: SoundCloud APIが設定されていない場合、SoundCloudのURLは処理されません。

## 🔧 トラブルシューティング

### Bot が応答しない

- Discordサーバーで適切な権限が設定されているか確認
- ログファイル `bot.log` を確認

### YouTube 認証エラー

- OAuth認証情報ファイルが正しい場所に配置されているか確認
- Google Cloud Console でAPIが有効化されているか確認

### SoundCloud 認証エラー

- Client ID/Secret が正しいか確認
- Redirect URIが `http://localhost:8888/callback` になっているか確認
- 詳細は `docs/SOUNDCLOUD_API.md` を参照

### プレイリスト追加エラー

- プレイリストIDが正しいか確認
- プレイリストが適切な権限で設定されているか確認

## 📁 ファイル構成

```
discord_playlistbot/
├── src/
│   ├── main.py              # メインBotファイル
│   ├── config.py            # 設定管理
│   ├── database.py          # データベース管理
│   ├── url_extractor.py     # URL抽出・解析
│   ├── music_services.py    # YouTube API連携
│   ├── soundcloud_service.py # SoundCloud API連携
│   └── commands.py          # スラッシュコマンド定義
├── data/                    # データ・認証情報ディレクトリ
├── docs/                    # ドキュメント
│   ├── DEVELOPMENT.md       # 開発者向けドキュメント
│   └── SOUNDCLOUD_API.md    # SoundCloud API実装詳細
├── env_template.txt         # 環境変数テンプレート
├── pyproject.toml           # Pythonプロジェクト設定
├── start.py                 # Bot起動スクリプト
├── uv.lock                  # 依存関係ロックファイル
├── LICENSE                  # ライセンスファイル
├── README.md                # このファイル
├── .env                     # 環境変数設定（実行時作成）
└── bot.log                  # ログファイル（実行時作成）
```

## 🔗 関連ドキュメント

- **[SOUNDCLOUD_API.md](docs/SOUNDCLOUD_API.md)**: SoundCloud API実装の詳細
- **[DEVELOPMENT.md](docs/DEVELOPMENT.md)**: 開発者向けドキュメント
- **[SoundCloud API Guide](https://developers.soundcloud.com/docs/api/guide)**: 公式APIドキュメント

## 📝 ライセンス

このプロジェクトはMITライセンスの下で公開されています。
