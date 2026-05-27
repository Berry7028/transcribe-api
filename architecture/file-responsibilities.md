# File Responsibilities

ここでは、実装ファイルごとに「何を書くか」を整理します。

## app/main.py

FastAPI アプリケーションの起動点です。

ここに書くこと:

- FastAPI インスタンスの作成
- ルーターの登録
- ヘルスチェック API の登録
- CORS 設定が必要なら追加

ここに書かないこと:

- 文字起こしの本体処理
- ffmpeg の処理
- OpenAI API 呼び出し

## app/api/routers/transcription.py

文字起こし API の HTTP エンドポイントを定義します。

ここに書くこと:

- `POST /api/transcriptions` の定義
- `UploadFile` の受け取り
- 任意パラメータの受け取り
- `transcription_service.py` への処理依頼
- レスポンスの返却

ここに書かないこと:

- チャンク分割ロジック
- ffmpeg コマンドの組み立て
- OpenAI API の細かい呼び出し

## app/core/config.py

環境変数やアプリ設定をまとめます。

ここに書くこと:

- OpenAI API キー
- デフォルトの文字起こしモデル
- 最大アップロードサイズ
- OpenAI に送る 1 チャンクあたりの最大サイズ
- 一時ファイル保存先
- 無音検出のしきい値

## app/core/errors.py

アプリ内で使うエラーを定義します。

ここに書くこと:

- 独自例外クラス
- エラーコード
- HTTP エラーへの変換方針

## app/schemas/transcription.py

文字起こし API のレスポンス形式を定義します。

ここに書くこと:

- チャンク結果の型
- 全体の文字起こし結果の型

## app/services/transcription_service.py

文字起こし処理全体をまとめる中心のサービスです。

ここに書くこと:

- ファイル受け取り後の全体制御
- media service の呼び出し
- chunk service の呼び出し
- openai service の呼び出し
- merge service の呼び出し
- 一時ファイル削除の制御

このファイルは「処理の順番」を管理します。細かい処理そのものは他の service に任せます。

## app/services/media_service.py

音声・動画ファイルを扱うサービスです。

ここに書くこと:

- ffmpeg で動画から音声を抽出
- ffmpeg で音声形式を正規化
- 音声の長さ取得
- ファイルサイズ取得

## app/services/chunk_service.py

大きい音声ファイルをチャンク分割するサービスです。

ここに書くこと:

- OpenAI API のサイズ制限を超えるか判定
- 無音区間の検出
- 分割位置の決定
- ffmpeg でチャンクファイルを書き出す
- チャンクごとの開始秒・終了秒を記録

## app/services/openai_service.py

OpenAI API との通信を担当します。

ここに書くこと:

- OpenAI クライアントの初期化
- 文字起こし API の呼び出し
- model, language, response_format などの指定
- OpenAI API エラーの扱い

ここでは `whisper_service.py` という名前にしない方がよいです。将来 `gpt-4o-transcribe` などに変えても自然に扱えるためです。

## app/services/merge_service.py

チャンクごとの文字起こし結果を結合します。

ここに書くこと:

- チャンク順にテキストを結合
- 余分な空白や改行の整理
- チャンクメタデータをレスポンス用に整形
- 全体の duration を計算

## app/utils/file_utils.py

ファイル操作の小さい補助関数を置きます。

ここに書くこと:

- 一時ファイル削除
- 必要になった小さいファイル操作

## app/utils/time_utils.py

時間関連の小さい補助関数を置きます。

ここに書くこと:

- 秒数の丸め
- ミリ秒から秒への変換
- 開始秒・終了秒の計算補助
