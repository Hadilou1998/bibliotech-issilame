import shutil
from datetime import date
from pathlib import Path

import pytest

import bibliotech

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture
def library(tmp_path, monkeypatch):
    """Library sur une copie des données, au 21/10/2026."""

    # Il copiera les données tout en évitant de modifier les vrais fichiers CSV.
    data_dir = tmp_path / "data"
    shutil.copytree(DATA_DIR, data_dir)

    # Chaque test travaille sur sa propre copie de données.
    monkeypatch.setattr(bibliotech, "DATA", str(data_dir))

    # Fixer la date permet d'obtenir toujours les mêmes résultats.
    monkeypatch.setattr(bibliotech, "TODAY", date(2026, 10, 21))

    return bibliotech.Library()
