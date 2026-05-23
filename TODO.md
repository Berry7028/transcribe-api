# transcribe-api 実装状況と次のタスク

設計ドキュメント（`architecture/*.md`、`README.md`）と現在のコードを突き合わせたメモです。  
**参照行番号**は、該当指示が書かれている Markdown 内の行です（ファイルを開いてジャンプできます）。

---

## サマリー：何が終わっていて、何がまだか

### 完了しているもの（コードベース上）

| 内容 | 根拠 |
|------|------|
| プロジェクト初期化（`pyproject.toml`、依存関係、`.env.example`、`.gitignore`） | `architecture/implementation-steps.md` **L5–L13** と実ファイルの存在 |
| FastAPI 最小起動、`GET /health` | `app/main.py`、`architecture/implementation-steps.md` **L16–L23** |
| `POST /api/transcriptions` でファイルアップロード → 一時保存、拡張子チェック | `app/api/routers/transcription.py`、`architecture/implementation-steps.md` **L26–L35** |
| **`media_service`**（ffmpeg 確認、動画から音声抽出、mp3 正規化、サイズ取得、`prepare_audio`） | `app/services/media_service.py`、`architecture/implementation-steps.md` **L37–L46** |
| アップロード後に `prepare_audio` を呼び、`normalized_path` / `size_bytes` を返す | `app/api/routers/transcription.py` |
| 一時ディレクトリ `app/tmp/uploads/`、`app/tmp/extracted/`、`app/tmp/normalized/` | ルーター・`media_service` のパス解決 |
| **`app/core/config.py`**（`.env` / `.env.local` 読み込み、OpenAI API キー、文字起こしモデル設定） | `app/core/config.py` |
| **`openai_service`**（OpenAI Speech to Text API 呼び出し、`whisper-1` で文字起こし） | `app/services/openai_service.py` |
| アップロード後に `prepare_audio` → OpenAI 文字起こしを実行し、`text` を返す | `app/api/routers/transcription.py` |
| **`errors.py`（一部）** — `TranscribeAPIError` と ffmpeg / 変換失敗用例外 | `app/core/errors.py` |
| **`TranscribeAPIError` のグローバル例外ハンドラー**（設計どおりの `{ "error": { "code", "message" } }` 形式） | `app/main.py` |
| **`chunk_service`**（サイズ判定、無音検出、チャンク書き出し、開始/終了秒メタデータ） | `app/services/chunk_service.py`、`architecture/implementation-steps.md` **L58–L67** |
| 一時ディレクトリ `app/tmp/chunks/` | `chunk_service` のパス解決 |

**現状の到達点:** Step 6 まで完了。25MB 以下は単発文字起こし、超過ファイルは `chunk_service` で分割可能（ルーター統合は未実施）。

### 未完了・未着手（設計どおりまだないもの）

- `merge_service` / `transcription_service`
- `app/schemas/transcription.py`、`app/utils/*`  
- 設計どおりの成功レスポンス（`text` は返却済み。`language` / `duration_seconds` / `chunks` などは未実装）  
- Step 8 相当の**エラー処理の完全統一**（拡張子エラー等はまだ `HTTPException` の plain `detail`）  
- 一時ファイルの削除処理  
- テスト、`tests/`  

### 部分的にできているもの（Step 8 前の暫定）

| 内容 | 状態 |
|------|------|
| `app/core/errors.py` | ffmpeg / 変換失敗 / OpenAI / chunking 関連。全エラーコードは未網羅 |
| API エラーレスポンス | `TranscribeAPIError` 経由のみ統一。400 系は未統一 |
| ルーターの責務 | 保存・拡張子チェックに加え `prepare_audio` / `transcribe_audio` 呼び出しまで実装（本来は `transcription_service` へ移す想定） |

### ドキュメントとコードのずれ（把握用）

- ルーター配置: 設計は `app/api/routes/transcription.py`（`architecture/file-responsibilities.md` **L24**、`architecture/project-structure.md` **L9–L11**）だが、実装は `app/api/routers/transcription.py`。  
- エンドポイント URL: `app/main.py` で `prefix="/api"` のため、現状は **`/api/transcriptions`**。設計文面は多くが **`POST /transcriptions`**（`architecture/api-design.md` **L5** など）— プレフィックスの方針をどちらかに揃える必要あり。  
- 許可拡張子: `architecture/processing-flow.md` **L31–L39** のリストより、ルーター側は追加形式あり（要: 設計との整合または設計更新）。  
- `architecture/implementation-steps.md` **L35** の「ここまでやった」は Step 3 のまま — **Step 4 完了に合わせて更新推奨**。  
- ルート `README.md` **L35–L38** は「実装前」とあるが、Step 4 まで実装済みなので**要更新**。

---

## 次にやるべきこと（優先順）

設計上の推奨順は `architecture/implementation-steps.md` **L69 以降**（Step 6 は完了）。

1. **Step 7: `merge_service`** — `architecture/implementation-steps.md` **L69–L77**、`architecture/file-responsibilities.md` **L128–L137**
2. **`transcription_service` で全体オーケストレーション** — `architecture/file-responsibilities.md` **L75–L88**、フロー全体 `architecture/processing-flow.md` **L5–L19**、**L82–L92**
   - ルーターから `prepare_audio` 直呼びを service 層へ移す
   - `needs_chunking` / `create_chunks` を組み込む
3. **Step 8: エラー処理・レスポンス形式の統一** — `architecture/implementation-steps.md` **L79–L88**、エラー一覧 `architecture/api-design.md` **L41–L61**、エラー定義の置き場 `architecture/file-responsibilities.md` **L55–L63**
4. **Step 9: テスト** — `architecture/implementation-steps.md` **L90–L100**
5. **Step 10: 非同期ジョブは将来検討** — `architecture/implementation-steps.md` **L102–L113**、`architecture/api-design.md` **L63–L76**

---

## タスク一覧（指示のあるファイル・行番号）

「この作業をする」ときに開く設計メモへのインデックスです。

### 実装手順（マスタ）

| タスク | 状態 | 参照 |
|--------|------|------|
| Step 1 初期化 | ✅ 完了 | `architecture/implementation-steps.md` **L5–L14** |
| Step 2 FastAPI 最小 | ✅ 完了 | **L16–L24** |
| Step 3 アップロード API | ✅ 完了 | **L26–L35** |
| Step 4 media_service | ✅ 完了 | **L37–L46** |
| Step 5 openai_service | ✅ 完了 | **L48–L56** |
| Step 6 chunk_service | ✅ 完了 | **L58–L67** |
| Step 7 merge_service | ⬜ 未着手 | **L69–L77** |
| Step 8 エラー処理 | 🔶 一部（変換失敗 / OpenAI 関連のみ） | **L79–L88** |
| Step 9 テスト | ⬜ 未着手 | **L90–L100** |
| Step 10 ジョブ化の検討 | ⬜ 将来 | **L102–L113** |

### ディレクトリ・ファイル名の約束

| タスク | 状態 | 参照 |
|--------|------|------|
| 想定ツリー全体 | 🔶 主要 service / tmp のみ | `architecture/project-structure.md` **L5–L45** |
| 各レイヤの説明 | — | **L47–L87** |

### ファイルごとの責務（実装時のチェックリスト）

| ファイル | 状態 | 参照 |
|----------|------|------|
| `app/main.py` | ✅ 最小 + 例外ハンドラー | `architecture/file-responsibilities.md` **L7–L22** |
| 文字起こしルート（設計上のパス名は `routes`） | 🔶 Step 5 まで | **L24–L40** |
| `app/core/config.py` | ✅ OpenAI + chunk 設定まで | **L42–L53** |
| `app/core/errors.py` | 🔶 ffmpeg / 変換失敗 / OpenAI / chunking 関連 | **L55–L63** |
| `app/schemas/transcription.py` | ⬜ 未着手 | **L65–L73** |
| `transcription_service.py` | ⬜ 未着手 | **L75–L88** |
| `media_service.py` | ✅ 完了 | **L90–L101** |
| `chunk_service.py` | ✅ 完了 | **L103–L113** |
| `openai_service.py` | ✅ 小さいファイルの単発文字起こしまで | **L115–L124** |
| `merge_service.py` | ⬜ 未着手 | **L128–L137** |
| `file_utils.py` / `time_utils.py` | ⬜ 未着手 | **L139–L158** |

### 処理フロー（実装の流れと一時ディレクトリ）

| 内容 | 状態 | 参照 |
|------|------|------|
| ステップ 1–11 全体 | 🔶 1–6 相当まで | `architecture/processing-flow.md` **L5–L19** |
| API 層の役割 | 🔶 ファイル受け取り + 暫定で media / OpenAI 呼び出し | **L21–L25** |
| 対応拡張子 | ✅ ルーター側でチェック | **L27–L39** |
| `tmp/uploads/` 保存 | ✅ | **L41–L45** |
| ffmpeg 正規化 | ✅ | **L47–L58** |
| サイズ確認・単発 / チャンク分岐 | 🔶 `needs_chunking` 実装済み（ルーター統合は未） | **L60–L74** |
| 単発文字起こし | ✅ `whisper-1` で実動作確認済み | **L76–L81** |
| チャンク分割 | ✅ `create_chunks` 実装済み | **L82–L87** |
| チャンク文字起こし・マージ・一時ファイル削除 | ⬜ 未着手 | **L82–L92** |

### API 仕様（リクエスト / レスポンス / エラー）

| 内容 | 状態 | 参照 |
|------|------|------|
| `POST /transcriptions`、multipart | ✅（URL は `/api/transcriptions`） | `architecture/api-design.md` **L5–L18** |
| 成功レスポンス JSON | 🔶 `text` は返却済み。まだデバッグ用フィールド（`saved_path` / `normalized_path` 等）あり | **L20–L38** |
| エラー形式・エラーコード一覧 | 🔶 変換失敗 / OpenAI 関連のみ統一形式 | **L41–L61** |
| 同期優先・将来ジョブ API | — | **L63–L76** |

### チャンク分割の詳細

| 内容 | 参照 |
|------|------|
| 基本アルゴリズム | `architecture/chunking-design.md` **L7–L16** |
| 時間分割を避ける理由 | **L18–L23** |
| 目標チャンクサイズ（上限との余裕） | **L26–L41** |
| 無音検出パラメータ・仮値 | **L43–L59** |
| チャンクが持つメタデータ | **L61–L72** |
| 無音が見つからないときのフォールバック | **L77–L87** |
| オーバーラップ・並列は後回し可 | **L89–L111** |

### プロダクト全体の前提

| 内容 | 参照 |
|------|------|
| 技術スタック・サービスがやること 8 項目 | `architecture/README.md` **L9–L28** |
| 設計で大事にすること | **L30–L36** |
| 各 `.md` の役割リンク | **L38–L45** |

### ルート README（要メンテ）

| 内容 | 参照 |
|------|------|
| 「現在の状態」が古い（Step 5 完了に未反映） | `README.md` **L35–L45** |

---

## メンテナンス

- 実装が進んだら、このファイルの「完了」「未完了」や、ルート `README.md` **L35–L38**、`architecture/implementation-steps.md` **L35** を同期して更新してください。
