"""Unit tests for NamedTupleTable"""

from pathlib import Path
from typing import NamedTuple

import pytest

from namedtuple_table import NamedTupleTable


class CatRow(NamedTuple):
    """Row format for __init__ sample data"""

    name: str
    ref: int
    age: int
    floof: bool


@pytest.fixture
def cat_rows() -> list[CatRow]:
    """Sample data for __init__"""
    return [
        CatRow("Freddy", 25, 3, floof=True),
        CatRow("Bucket", 2, 5, floof=True),
        CatRow("Enoby", 27, 8, floof=True),
    ]


@pytest.fixture
def dogs_tsv() -> Path:
    """Good TSV file with good dogs"""
    return Path(__file__).parent / "data/dogs.tsv"


@pytest.fixture
def bad_dogs_tsv() -> Path:
    """TSV file with missing columns"""
    return Path(__file__).parent / "data/bad_dogs.tsv"


def test_methods(cat_rows):
    """Check basic features of NamedTupleTable"""
    cat_table = NamedTupleTable(cat_rows, index="name")

    assert len(cat_table) == 3

    for name in ["Freddy", "Bucket", "Enoby"]:
        assert name in cat_table

    assert "Heathcliff" not in cat_table

    for item in cat_table:
        assert isinstance(item, str)

    for item in cat_table.values():
        assert isinstance(item, CatRow)

    freddy = cat_table["Freddy"]
    assert isinstance(freddy, CatRow)
    assert freddy.age == 3


def test_index_change(cat_rows):
    """Creating a new table with different index"""
    cat_table = NamedTupleTable(cat_rows, index="name")

    cats_by_ref = cat_table.with_index("ref")
    assert cats_by_ref[27].name == "Enoby"

    assert cats_by_ref is cat_table.with_index("ref")

    with pytest.raises(ValueError, match="Cannot use 'floof' as index: "):
        cat_table.with_index("floof")


def test_from_tsv(dogs_tsv):
    """Load a good TSV file"""
    dog_table = NamedTupleTable.from_tsv(dogs_tsv)

    # Test columns are named correctly
    assert dog_table["2"].name == "Geoff"

    # Test double-tabs are joined correctly
    assert dog_table["2"].collar == "blue"

    assert "#3" not in dog_table

    # Test duplicate values are detected when re-indexing
    with pytest.raises(ValueError, match="Cannot use 'collar' as index: "):
        dog_table.with_index("collar")


def test_from_bad_tsv(bad_dogs_tsv):
    """Load TSV with empty columns"""
    with pytest.raises(TypeError, match="3	Bandit			40"):
        NamedTupleTable.from_tsv(bad_dogs_tsv)
