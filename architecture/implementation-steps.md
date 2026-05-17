# Implementation Steps

コードを書くときは、以下の順番で進めると迷いにくいです。

## Step 1: プロジェクト初期化

やること:

- `pyproject.toml` を作る
- FastAPI, uvicorn, openai, pydantic-settings などを入れる
- `.env.example` を作る
- `.gitignore` を作る

この時点では API はまだ最小でよいです。

## Step 2: FastAPI の最小起動

やること:

- `app/main.py` を作る
- `GET /health` を作る
- ローカルで uvicorn 起動できることを確認する

目的は、まず API サーバーとして動く状態を作ることです。

## Step 3: アップロード API

やること:

- `POST /transcriptions` を作る
- `UploadFile` を受け取る
- 一時ディレクトリに保存する
- 対応拡張子だけ許可する

この段階では、まだ OpenAI API を呼ばなくてもよいです。

## Step 4: media_service

やること:

- ファイルサイズを取得する
- ffmpeg が使えるか確認する
- 動画から音声を抽出する
- 音声を送信用形式に正規化する

まずは手元の短い mp3 と mp4 で動作確認します。

## Step 5: openai_service

やること:

- OpenAI クライアントを作る
- 小さい音声ファイルを送って文字起こしする
- 結果を API レスポンスで返す

この段階で、25MB 以下のファイルは文字起こしできる状態になります。

## Step 6: chunk_service

やること:

- サイズ制限を超えるか判定する
- 無音区間を検出する
- チャンクファイルを書き出す
- チャンクの開始秒・終了秒を管理する

ここがこのプロジェクトの一番重要な実装です。

## Step 7: merge_service

やること:

- チャンクごとの文字起こし結果を受け取る
- 順番に結合する
- レスポンス用の `chunks` 情報を作る

最初は単純結合でよいです。

## Step 8: エラー処理

やること:

- 対応していないファイル形式のエラー
- ffmpeg 失敗時のエラー
- OpenAI API 失敗時のエラー
- 一時ファイル削除失敗時の扱い

エラーコードを決めて、API レスポンスを揃えます。

## Step 9: テスト

やること:

- ファイル形式判定のテスト
- サイズ判定のテスト
- チャンク分割ロジックのテスト
- merge_service のテスト
- API の簡単なテスト

OpenAI API を直接呼ぶテストは最初は避け、モックにします。

## Step 10: 非同期ジョブ化の検討

長時間ファイルで HTTP リクエストが長くなりすぎる場合は、ジョブ方式に変更します。

将来の形:

```text
POST /transcription-jobs
GET /transcription-jobs/{job_id}
```

ただし、最初の練習実装ではここまでやらなくてよいです。
