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
| `POST` でファイルアップロード → 一時保存、拡張子チェック（OpenAI 呼び出しは未実装） | `app/api/routers/transcription.py`、`architecture/implementation-steps.md` **L26–L35**（**L35** に「ここまでやった」） |

### 未完了・未着手（設計どおりまだないもの）

- `media_service` / `openai_service` / `chunk_service` / `merge_service` / `transcription_service` の分離実装  
- `app/core/config.py`、`errors.py`、`schemas/transcription.py`、`utils/*`  
- `tmp/uploads/` などの想定ディレクトリ構成（現状はルーター近傍の `uploads_temp`）  
- 設計どおりの API レスポンス・統一エラー形式、テスト、`tests/`  

### ドキュメントとコードのずれ（把握用）

- ルーター配置: 設計は `app/api/routes/transcription.py`（`architecture/file-responsibilities.md` **L24**、`architecture/project-structure.md` **L9–L11**）だが、実装は `app/api/routers/transcription.py`。  
- エンドポイント URL: `app/main.py` で `prefix="/api"` のため、現状は **`/api/transcriptions`**。設計文面は多くが **`POST /transcriptions`**（`architecture/api-design.md` **L5** など）— プレフィックスの方針をどちらかに揃える必要あり。  
- 許可拡張子: `architecture/processing-flow.md` **L31–L39** のリストより、ルーター側は追加形式あり（要: 設計との整合または設計更新）。  
- ルート `README.md` **L35–L38** は「実装前」とあるが、Step 3 まで実装済みなので**要更新**。

---

## 次にやるべきこと（優先順）

設計上の推奨順は `architecture/implementation-steps.md` **L37 以降**。

1. **Step 4: `media_service`**（ffmpeg・正規化・サイズ取得）— **L37–L46**  
   - フロー上の配置: `architecture/processing-flow.md` **L41–L58**、責務: `architecture/file-responsibilities.md` **L90–L101**  
2. **Step 5: `openai_service`**（小さいファイルの文字起こしまで）— `architecture/implementation-steps.md` **L48–L56**  
   - 責務: `architecture/file-responsibilities.md` **L115–L124**  
3. **Step 6: `chunk_service`**（サイズ判定・無音・チャンク書き出し）— `architecture/implementation-steps.md` **L58–L67**  
   - 詳細仕様: `architecture/chunking-design.md` **L7–L16**、**L26–L35**、**L43–L59**、**L61–L72**、フォールバック **L77–L87**  
4. **Step 7: `merge_service`** — `architecture/implementation-steps.md` **L69–L77**、`architecture/file-responsibilities.md` **L128–L137**  
5. **`transcription_service` で全体オーケストレーション** — `architecture/file-responsibilities.md` **L75–L88**、フロー全体 `architecture/processing-flow.md` **L5–L19**、**L82–L92**  
6. **Step 8: エラー処理・レスポンス形式の統一** — `architecture/implementation-steps.md` **L79–L88**、エラー一覧 `architecture/api-design.md` **L41–L61**、エラー定義の置き場 `architecture/file-responsibilities.md` **L55–L63**  
7. **Step 9: テスト** — `architecture/implementation-steps.md` **L90–L100**  
8. **Step 10: 非同期ジョブは将来検討** — `architecture/implementation-steps.md` **L102–L113**、`architecture/api-design.md` **L63–L76**  

---

## タスク一覧（指示のあるファイル・行番号）

「この作業をする」ときに開く設計メモへのインデックスです。

### 実装手順（マスタ）

| タスク | 参照 |
|--------|------|
| Step 1 初期化 | `architecture/implementation-steps.md` **L5–L14** |
| Step 2 FastAPI 最小 | **L16–L24** |
| Step 3 アップロード API（現状ここまで） | **L26–L35** |
| Step 4 media_service | **L37–L46** |
| Step 5 openai_service | **L48–L56** |
| Step 6 chunk_service | **L58–L67** |
| Step 7 merge_service | **L69–L77** |
| Step 8 エラー処理 | **L79–L88** |
| Step 9 テスト | **L90–L100** |
| Step 10 ジョブ化の検討 | **L102–L113** |

### ディレクトリ・ファイル名の約束

| タスク | 参照 |
|--------|------|
| 想定ツリー全体 | `architecture/project-structure.md` **L5–L45** |
| 各レイヤの説明 | **L47–L87** |

### ファイルごとの責務（実装時のチェックリスト）

| ファイル | 参照 |
|----------|------|
| `app/main.py` | `architecture/file-responsibilities.md` **L7–L22** |
| 文字起こしルート（設計上のパス名は `routes`） | **L24–L40** |
| `app/core/config.py` | **L42–L53** |
| `app/core/errors.py` | **L55–L63** |
| `app/schemas/transcription.py` | **L65–L73** |
| `transcription_service.py` | **L75–L88** |
| `media_service.py` | **L90–L101** |
| `chunk_service.py` | **L103–L113** |
| `openai_service.py` | **L115–L124** |
| `merge_service.py` | **L128–L137** |
| `file_utils.py` / `time_utils.py` | **L139–L158** |

### 処理フロー（実装の流れと一時ディレクトリ）

| 内容 | 参照 |
|------|------|
| ステップ 1–11 全体 | `architecture/processing-flow.md` **L5–L19** |
| API 層の役割 | **L21–L25** |
| 対応拡張子 | **L27–L39** |
| `tmp/uploads/` 保存 | **L41–L45** |
| ffmpeg 正規化 | **L47–L58** |
| サイズ確認・単発 / チャンク分岐 | **L60–L74** |
| チャンク文字起こし・マージ・一時ファイル削除 | **L76–L92** |

### API 仕様（リクエスト / レスポンス / エラー）

| 内容 | 参照 |
|------|------|
| `POST /transcriptions`、multipart | `architecture/api-design.md` **L5–L18** |
| 成功レスポンス JSON | **L20–L38** |
| エラー形式・エラーコード一覧 | **L41–L61** |
| 同期優先・将来ジョブ API | **L63–L76** |

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
| 「現在の状態」が古い | `README.md` **L35–L45** |

---

## メンテナンス

- 実装が進んだら、このファイルの「完了」「未完了」や、ルート `README.md` **L35–L38** を同期して更新してください。
