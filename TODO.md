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
| アップロード後に `transcription_service` で単発 / チャンク文字起こしを実行し、成功レスポンスを返す | `app/api/routers/transcription.py`、`app/services/transcription_service.py` |
| 一時ディレクトリ `app/tmp/uploads/`、`app/tmp/extracted/`、`app/tmp/normalized/` | ルーター・`media_service` のパス解決 |
| **`app/core/config.py`**（`.env` / `.env.local` 読み込み、OpenAI API キー、文字起こしモデル設定） | `app/core/config.py` |
| **`openai_service`**（OpenAI Speech to Text API 呼び出し、`whisper-1` で文字起こし） | `app/services/openai_service.py` |
| `transcription_service` から OpenAI 文字起こしを実行し、単発 / チャンクの結果を返す | `app/services/transcription_service.py`、`app/services/openai_service.py` |
| **`errors.py`** — Step 8 の主要エラーコード（未対応形式 / 不正リクエスト / 変換失敗 / OpenAI 失敗 / チャンク失敗 / ローカル上限超過 / 一時ファイル削除失敗）を定義 | `app/core/errors.py` |
| **エラー用グローバル例外ハンドラー**（`TranscribeAPIError` / FastAPI バリデーション / HTTP 例外を `{ "error": { "code", "message" } }` 形式へ統一） | `app/main.py` |
| **`chunk_service`**（サイズ判定、無音検出、チャンク書き出し、開始/終了秒メタデータ） | `app/services/chunk_service.py`、`architecture/implementation-steps.md` **L58–L67** |
| 一時ディレクトリ `app/tmp/chunks/` | `chunk_service` のパス解決 |
| 未対応拡張子エラーを統一形式で返却 | `app/api/routers/transcription.py` |
| **`merge_service`**（チャンク文字起こし結果の順次結合、空白整理、レスポンス用 `chunks` / `duration_seconds`） | `app/services/merge_service.py`、`architecture/implementation-steps.md` **L69–L77** |
| **Step 9 テスト**（`media_service` / `chunk_service` / `merge_service` / API の pytest。OpenAI API と ffmpeg 実処理はモック） | `tests/`、`pyproject.toml`、`architecture/implementation-steps.md` **L90–L100** |

**現状の到達点:** Step 9 まで完了。25MB 以下は単発文字起こし、超過ファイルは `chunk_service` で分割し、`transcription_service` でチャンクごとの文字起こしと `merge_service` による結合まで実行可能。テストは OpenAI API を直接呼ばず、重い外部処理をモックして実行可能。

### 将来検討

- Step 10 の非同期ジョブ化は将来検討。現時点の練習実装では同期 API のままでよい。

### 部分的にできているもの

| 内容 | 状態 |
|------|------|
| 一時ファイル削除失敗 | エラーコードと削除処理を実装済み。成功後の削除失敗は統一エラー形式で返す |
| ルーターの責務 | 保存・拡張子チェックまでに整理し、文字起こし全体制御は `transcription_service` へ移動済み |

### ドキュメントとコードのずれ（把握用）

- 現時点で把握している主要なずれは解消済み。

---

## 次にやるべきこと（優先順）

現時点の同期 API として必要な実装タスクは完了。

将来、長時間ファイルで HTTP リクエストが長くなりすぎる場合は、Step 10 の非同期ジョブ化を検討する。

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
| Step 7 merge_service | ✅ 完了 | **L69–L77** |
| Step 8 エラー処理 | ✅ 完了 | **L79–L88** |
| Step 9 テスト | ✅ 完了 | **L90–L100** |
| Step 10 ジョブ化の検討 | 将来検討 | **L102–L113** |

### ディレクトリ・ファイル名の約束

| タスク | 状態 | 参照 |
|--------|------|------|
| 想定ツリー全体 | ✅ 実装済み | `architecture/project-structure.md` **L5–L45** |
| 各レイヤの説明 | — | **L47–L87** |

### ファイルごとの責務（実装時のチェックリスト）

| ファイル | 状態 | 参照 |
|----------|------|------|
| `app/main.py` | ✅ 最小 + 統一例外ハンドラー | `architecture/file-responsibilities.md` **L7–L22** |
| 文字起こしルート | ✅ 保存・拡張子チェック・service 呼び出し | **L24–L40** |
| `app/core/config.py` | ✅ OpenAI + chunk 設定まで | **L42–L53** |
| `app/core/errors.py` | ✅ Step 8 のエラーコード定義まで | **L55–L63** |
| `app/schemas/transcription.py` | ✅ 完了 | **L65–L73** |
| `transcription_service.py` | ✅ 完了 | **L75–L88** |
| `media_service.py` | ✅ 完了 | **L90–L101** |
| `chunk_service.py` | ✅ 完了 | **L103–L113** |
| `openai_service.py` | ✅ 単発・チャンク両方から利用 | **L115–L124** |
| `merge_service.py` | ✅ 完了 | **L128–L137** |
| `file_utils.py` / `time_utils.py` | ✅ 一時ファイル削除・秒数丸めを実装 | **L139–L158** |

### 処理フロー（実装の流れと一時ディレクトリ）

| 内容 | 状態 | 参照 |
|------|------|------|
| ステップ 1–11 全体 | ✅ 同期 API として完了 | `architecture/processing-flow.md` **L5–L19** |
| API 層の役割 | ✅ ファイル受け取り + service 呼び出し | **L21–L25** |
| 対応拡張子 | ✅ ルーター側でチェック | **L27–L39** |
| `tmp/uploads/` 保存 | ✅ | **L41–L45** |
| ffmpeg 正規化 | ✅ | **L47–L58** |
| サイズ確認・単発 / チャンク分岐 | ✅ `transcription_service` に統合済み | **L60–L74** |
| 単発文字起こし | ✅ `whisper-1` で実装済み | **L76–L81** |
| チャンク分割 | ✅ `create_chunks` 実装済み | **L82–L87** |
| チャンク文字起こし | ✅ 完了 | **L82–L87** |
| チャンク結果マージ | ✅ `transcription_service` に統合済み | **L82–L87** |
| 一時ファイル削除 | ✅ 完了 | **L88–L92** |

### API 仕様（リクエスト / レスポンス / エラー）

| 内容 | 状態 | 参照 |
|------|------|------|
| `POST /api/transcriptions`、multipart | ✅ | `architecture/api-design.md` **L5–L18** |
| 成功レスポンス JSON | ✅ `text` / `language` / `duration_seconds` / `model` / `chunks` を返却。デバッグ用パスは削除済み | **L20–L38** |
| エラー形式・エラーコード一覧 | ✅ 統一形式に対応 | **L41–L61** |
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

### ルート README

| 内容 | 参照 |
|------|------|
| 「現在の状態」 | 更新済み |

---

## メンテナンス

- 実装が進んだら、このファイルの「完了」「未完了」や、ルート `README.md`、`architecture/implementation-steps.md` を同期して更新してください。
