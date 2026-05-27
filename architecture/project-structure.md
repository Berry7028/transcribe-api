# Project Structure

最初は以下の構成で作る想定です。

```text
transcribe-api/
  app/
    main.py
    api/
      routers/
        transcription.py
    core/
      config.py
      errors.py
    schemas/
      transcription.py
    services/
      media_service.py
      chunk_service.py
      openai_service.py
      merge_service.py
      transcription_service.py
    utils/
      file_utils.py
      time_utils.py
  architecture/
    README.md
    project-structure.md
    api-design.md
    processing-flow.md
    file-responsibilities.md
    chunking-design.md
    implementation-steps.md
  tests/
    services/
    api/
  tmp/
    uploads/
    normalized/
    chunks/
  .env.example
  .gitignore
  README.md
  pyproject.toml
```

## app/

実際のアプリケーションコードを置く場所です。

FastAPI の起動、API ルーティング、リクエスト受け取り、音声処理、OpenAI API 呼び出しなどをここにまとめます。

## app/api/routers/

HTTP API のエンドポイントを置きます。

ここではリクエストを受け取り、細かい処理は `services/` に渡します。API 層では、音声変換やチャンク分割などの重いロジックを書かない方針です。

## app/core/

アプリ全体で使う設定やエラー定義を置きます。

OpenAI API キー、アップロードサイズ制限、チャンクサイズ、無音検出のしきい値などはここから読めるようにします。

## app/schemas/

API の request / response の形を定義します。

FastAPI では Pydantic モデルを使う想定です。

## app/services/

実際の処理ロジックを置きます。

このプロジェクトでは一番重要な層です。ファイルの正規化、チャンク分割、OpenAI API 呼び出し、結果結合などを役割ごとに分けます。

## app/utils/

汎用的な小さい関数を置きます。

ファイルサイズ取得、拡張子判定、秒数フォーマットなど、特定のサービスに強く依存しない処理だけを置きます。

## tmp/

アップロードされたファイルや変換後ファイル、チャンクファイルを一時的に置く場所です。

本番運用ではローカルディスクではなく、S3 などのオブジェクトストレージを使う可能性があります。最初の練習実装ではローカル保存で十分です。
