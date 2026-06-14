from dataclasses import dataclass, fields
from pathlib import Path

import pandas as pd

from predictor.data.contracts import REQUIRED_COLUMNS, SourcePaths


class DataValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class FileValidation:
    name: str
    path: Path
    rows: int
    missing_columns: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not self.missing_columns


def validate_sources(paths: SourcePaths) -> list[FileValidation]:
    results = []
    for field in fields(paths):
        name = field.name
        path = getattr(paths, name)
        if not path.exists():
            raise DataValidationError(f"Missing source file: {path}")

        frame = pd.read_csv(path, nrows=5)
        missing = tuple(sorted(REQUIRED_COLUMNS[name] - set(frame.columns)))
        row_count = sum(1 for _ in path.open(encoding="utf-8-sig")) - 1
        results.append(
            FileValidation(
                name=name,
                path=path,
                rows=row_count,
                missing_columns=missing,
            )
        )

    invalid = [item for item in results if not item.valid]
    if invalid:
        detail = "; ".join(f"{item.name}: {', '.join(item.missing_columns)}" for item in invalid)
        raise DataValidationError(f"Invalid source schemas: {detail}")
    return results
