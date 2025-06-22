# SoundCloud API 実装ドキュメント

[SoundCloud API Developer Guide](https://developers.soundcloud.com/docs/api/guide)に基づいた実装詳細

## 📋 API仕様まとめ

### 🔐 認証方式
- **OAuth 2.1** (PKCE必須)
- **Authorization Code Flow**: ユーザー代理でプレイリスト編集
- **Client Credentials Flow**: 公開リソースアクセス（検索等）

### 🌐 エンドポイント
```
Authorization: https://secure.soundcloud.com/authorize
Token:        https://secure.soundcloud.com/oauth/token
API Base:     https://api.soundcloud.com
```

### 🔑 必要なスコープ
- `non-expiring`: プレイリスト管理に必要

## 🛠️ 実装機能

### ✅ 実装済み機能

#### 1. OAuth 2.1 (PKCE) 認証
- **code_verifier** と **code_challenge** の自動生成
- ローカルサーバー (`localhost:8888`) での認証コード受信
- アクセストークンの自動取得・保存・検証

#### 2. URL解決
```python
await soundcloud_service.resolve_url(url)
```
- SoundCloud URLからトラック情報を取得
- `/resolve` エンドポイント使用

#### 3. プレイリスト管理
```python
await soundcloud_service.add_to_playlist(url)
```
- トラックのプレイリスト追加
- 重複チェック機能
- `/playlists/{id}` エンドポイント使用

#### 4. トラック検索
```python
await soundcloud_service.search_tracks(query, limit)
```
- キーワードによるトラック検索
- `/tracks` エンドポイント使用

### 🔧 技術実装詳細

#### PKCE認証フロー
1. **code_verifier** 生成 (32バイトランダム + Base64URL)
2. **code_challenge** 生成 (SHA256 + Base64URL)
3. 認証URL構築・ブラウザ起動
4. ローカルサーバーで認証コード受信
5. アクセストークン交換・保存

#### エラーハンドリング
- **400 Bad Request**: パラメータエラー
- **401 Unauthorized**: 認証エラー
- **403 Forbidden**: アクセス権限エラー
- **404 Not Found**: リソース未発見
- **429 Too Many Requests**: レート制限
- **500+ Server Error**: サーバーエラー

## 📁 実装ファイル

### `src/soundcloud_service.py`
メインのSoundCloud API実装
- `SoundCloudService` クラス
- OAuth 2.1認証
- プレイリスト管理
- URL解決・検索

### `src/config.py`
設定管理（追加項目）
```python
@property
def soundcloud_token_file(self) -> Path:
    return Path("./data/soundcloud_oauth_token.json")
```

### `src/main.py`
Botメイン処理（統合部分）
```python
from soundcloud_service import SoundCloudService
self.soundcloud_service = SoundCloudService()
```

## 🚀 セットアップ手順

### 1. SoundCloud API アプリケーション登録
1. [SoundCloud Developer](https://developers.soundcloud.com/)にアクセス
2. "Register a new application" をクリック
3. アプリケーション情報を入力:
   - **Name**: Botの名前
   - **Description**: Botの説明
   - **Website**: Botのウェブサイト（任意）
   - **Redirect URI**: `http://localhost:8888/callback`
4. **Client ID** と **Client Secret** をコピー

### 2. プレイリスト ID 取得
1. SoundCloudでプレイリストを作成
2. プレイリストURLから数値IDを取得
   - 例: `https://soundcloud.com/user/sets/playlist-name`
   - ブラウザの開発者ツールでAPIレスポンスからIDを確認

### 3. 環境変数設定
```env
SOUNDCLOUD_CLIENT_ID=your_client_id_here
SOUNDCLOUD_CLIENT_SECRET=your_client_secret_here
SOUNDCLOUD_PLAYLIST_ID=your_playlist_id_here
```

### 4. 初回認証
Bot起動時に自動でブラウザが開き、SoundCloud認証画面が表示されます。
認証完了後、トークンは `./data/soundcloud_oauth_token.json` に保存されます。

## 🎯 使用例

### Discord内での使用
```
# SoundCloudリンクを投稿
https://soundcloud.com/artist/track-name

# Botが自動で検出・プレイリスト追加
✅ SoundCloudプレイリストに追加しました: https://soundcloud.com/artist/track-name
```

### 過去ログ処理
```
/backlog 50
```
SoundCloudリンクも含めて過去50件のメッセージを処理

## 🔍 API制限・注意事項

### レート制限
- SoundCloud APIにはレート制限があります
- 429エラー時は一定時間待機後に再試行

### プレイリスト権限
- プレイリストの所有者である必要があります
- 他のユーザーのプレイリストは編集できません

### トークン管理
- アクセストークンは `non-expiring` スコープで永続化
- トークンファイルは機密情報のため適切に管理

## 🐛 トラブルシューティング

### 認証エラー
- Client ID/Secret が正しいか確認
- Redirect URIが `http://localhost:8888/callback` になっているか確認

### プレイリスト追加エラー
- プレイリストIDが正しいか確認
- プレイリストの権限があるか確認

### URL解決エラー
- SoundCloudのURLが有効か確認
- トラックが削除されていないか確認

## 📚 参考資料

- [SoundCloud API Guide](https://developers.soundcloud.com/docs/api/guide)
- [OAuth 2.1 RFC](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1)
- [PKCE RFC](https://datatracker.ietf.org/doc/html/rfc7636) 