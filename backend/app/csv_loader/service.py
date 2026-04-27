from collections.abc import Iterator
from pathlib import Path

import pandas as pd


class CsvLoaderService:
    def load(self, file_path: str, chunksize: int | None = None) -> list[dict]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        if path.suffix.lower() != ".csv":
            raise ValueError("CSV is the only supported dataset input format.")

        records: list[dict] = []
        for chunk in self.iter_chunks(path, chunksize):
            records.extend(chunk.to_dict(orient="records"))
        return records

    def iter_chunks(self, path: Path, chunksize: int | None = None) -> Iterator[pd.DataFrame]:
        required_columns = {
            "asin",
            "helpful",
            "overall",
            "reviewText",
            "reviewTime",
            "unixReviewTime",
            "reviewerID",
            "reviewerName",
            "summary",
        }
        if chunksize:
            reader = pd.read_csv(path, chunksize=chunksize)
            for chunk in reader:
                self._validate_columns(chunk.columns, required_columns)
                yield chunk
            return

        dataframe = pd.read_csv(path)
        self._validate_columns(dataframe.columns, required_columns)
        yield dataframe

    @staticmethod
    def _validate_columns(columns, required_columns: set[str]) -> None:
        missing = required_columns.difference(set(columns))
        if missing:
            raise ValueError(f"CSV missing required columns: {sorted(missing)}")
