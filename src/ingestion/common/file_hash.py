import hashlib
from pathlib import Path


def calculate_file_hash(
    file_path: str,
) -> str:
    """
    Calculate SHA-256 hash for a file.

    Args:
        file_path:
            Path to file.

    Returns:
        Hexadecimal SHA-256 hash string.
    """

    path = Path(file_path)

    if not path.exists():

        raise FileNotFoundError(
            f"File not found: {file_path}"
        )

    sha256 = hashlib.sha256()

    with open(
        path,
        "rb",
    ) as file:

        while chunk := file.read(8192):

            sha256.update(chunk)

    return sha256.hexdigest()