import hashlib

import pytest

from ingestion.common.file_hash import calculate_file_hash


def test_calculate_file_hash(tmp_path):

    file_path = tmp_path / "test.txt"

    content = b"hello world"

    file_path.write_bytes(content)

    expected_hash = hashlib.sha256(
        content
    ).hexdigest()

    actual_hash = calculate_file_hash(
        str(file_path)
    )

    assert actual_hash == expected_hash


def test_calculate_file_hash_empty_file(
    tmp_path,
):

    file_path = tmp_path / "empty.txt"

    file_path.write_text("")

    expected_hash = hashlib.sha256(
        b""
    ).hexdigest()

    actual_hash = calculate_file_hash(
        str(file_path)
    )

    assert actual_hash == expected_hash


def test_calculate_file_hash_file_not_found():

    with pytest.raises(
        FileNotFoundError,
        match="File not found",
    ):
        calculate_file_hash(
            "does_not_exist.csv"
        )