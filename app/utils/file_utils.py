from pathlib import Path

from app.core.errors import TemporaryFileCleanupError


def cleanup_temp_files(paths: list[str | Path]) -> None:
    """処理中に生成した一時ファイルを削除し、失敗したパスをまとめて報告する。"""

    failures: list[str] = []

    for path in paths:
        file_path = Path(path)
        if not file_path.exists():
            continue
        try:
            # 現状の呼び出し元はファイルだけを渡すため、ディレクトリは削除対象にしない。
            if file_path.is_file():
                file_path.unlink()
        except OSError as exc:
            failures.append(f"{file_path}: {exc}")

    if failures:
        raise TemporaryFileCleanupError(
            "一時ファイルの削除に失敗しました: " + "; ".join(failures)
        )
