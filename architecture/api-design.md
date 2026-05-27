# API Design

最初に作る API は、文字起こしを実行する `POST /api/transcriptions` だけで十分です。

## POST /api/transcriptions

音声または動画ファイルを受け取り、文字起こし結果を返します。

## Request

Content-Type は `multipart/form-data` を想定します。

```text
file: 必須。mp3, mp4, m4a, wav, webm など
language: 任意。ja, en など。未指定なら自動判定
model: 任意。デフォルトは設定ファイル側で決める
response_format: 任意。最初は json 固定でもよい
```

## Response

最初は以下の形を目指します。

```json
{
  "text": "文字起こし全文",
  "language": null,
  "duration_seconds": 1234.5,
  "model": "whisper-1",
  "chunks": [
    {
      "index": 0,
      "start_seconds": 0.0,
      "end_seconds": 300.0,
      "text": "チャンク1の文字起こし"
    }
  ]
}
```

## Error Response

エラー時は以下のような形にします。

```json
{
  "error": {
    "code": "unsupported_file_type",
    "message": "対応していないファイル形式です"
  }
}
```

## 想定するエラー

- `unsupported_file_type`: 対応していない拡張子
- `file_too_large_for_local_processing`: ローカルで扱う上限を超えた
- `media_conversion_failed`: ffmpeg での変換失敗
- `chunking_failed`: チャンク分割失敗
- `transcription_failed`: OpenAI API での文字起こし失敗
- `invalid_request`: リクエスト形式が不正

## 同期処理か非同期処理か

最初は同期処理で作ります。

つまり、`POST /api/transcriptions` にファイルを送ると、文字起こしが完了するまで HTTP レスポンスを待つ方式です。

ただし長時間ファイルでは処理に時間がかかるので、将来的には以下の形に拡張する可能性があります。

```text
POST /transcription-jobs
GET /transcription-jobs/{job_id}
```

最初からジョブ方式にすると設計が大きくなるため、練習実装では同期 API から始めます。
