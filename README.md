# Transcribe API

このリポジトリは、バックエンドサービス構築の練習として作成するトランスクリプト API です。

音声ファイルや動画ファイルを受け取り、音声を文字起こしして JSON で返すバックエンド API を作ることを目的にしています。まずはバックエンド単体で REST API を設計・実装し、ファイルアップロード、音声変換、チャンク分割、外部 API 連携、レスポンス設計などを学ぶためのプロジェクトです。

## 使用予定の技術

- 言語: Python
- API フレームワーク: FastAPI
- スキーマ定義・バリデーション: Pydantic
- 設定管理: `.env` と Pydantic Settings
- 音声・動画処理: ffmpeg
- 無音検出・チャンク分割: pydub または librosa
- 文字起こし: OpenAI Speech to Text API
- テスト: pytest

## 作成する API

最初は、音声または動画ファイルをアップロードして文字起こし結果を返す API を作成します。

```text
POST /transcriptions
```

想定する処理の流れは以下です。

1. クライアントから音声または動画ファイルを受け取る
2. 動画ファイルの場合は音声を抽出する
3. OpenAI API に送信しやすい形式へ変換する
4. 必要に応じてファイルをチャンク分割する
5. 各チャンクを文字起こしする
6. 結果を結合して JSON で返す

## 現在の状態

現時点では、実装前の設計ドキュメントを `architecture/` にまとめています。

- `architecture/README.md`: 設計全体の概要
- `architecture/project-structure.md`: 想定するディレクトリ構成
- `architecture/api-design.md`: API エンドポイント設計
- `architecture/processing-flow.md`: 処理フロー
- `architecture/file-responsibilities.md`: 各ファイルの責務
- `architecture/chunking-design.md`: チャンク分割設計
- `architecture/implementation-steps.md`: 実装手順

## 将来的にやりたいこと

バックエンドの実装が完了したら、フロントエンドも用意する予定です。

フロントエンドから音声・動画ファイルをアップロードし、バックエンドの REST API を経由して文字起こしを実行できるようにします。これにより、バックエンド単体の API 実装だけでなく、フロントエンドとバックエンドの連携も練習できる構成にします。
