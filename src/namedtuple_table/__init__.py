from __future__ import annotations

from collections import namedtuple
from collections.abc import Mapping
from functools import cached_property, lru_cache
from itertools import tee
from pathlib import PurePath
from re import split as re_split
from types import MappingProxyType
from typing import TYPE_CHECKING, Iterable, Iterator, NamedTuple, Self, TypeVar

NT = TypeVar("NT", bound=NamedTuple)


class NamedTupleTable(Mapping[str | int, NT]):
    """An immutable collection of NamedTuple using one attribute as an index"""

    def __init__(self, rows: Iterable[NT], index: str | None = None) -> None:
        if index is None:
            # Buffer the iterator so we can still iterate from the beginning
            rows, rows_tee = tee(rows)

            # Grab the first field in the first item to check NamedTuple keys
            first_row: NT = next(rows_tee)
            index = first_row.__class__.__dict__["_fields"][0]
            if TYPE_CHECKING:
                assert isinstance(index, str)

        self._rows: frozenset[NT] = frozenset(rows)
        self._index: str = index

    def __str__(self) -> str:
        return f"NamedTupleTable ({len(self._rows)} items, index = {self._index})"

    @cached_property
    def _map(self) -> MappingProxyType:
        return MappingProxyType({getattr(row, self._index): row for row in self._rows})

    def __getitem__(self, key: int | str) -> NT:
        return self._map[key]

    def __hash__(self) -> int:
        return hash((self._index, self._rows))

    def __iter__(self) -> Iterator[str | int]:
        return iter(self._map)

    @cached_property
    def _len(self) -> int:
        return len(self._map)

    def __len__(self) -> int:
        return self._len

    def with_index(self, index: str | None) -> NamedTupleTable:
        return _create_with_new_index(type(self), self._rows, index)

    @classmethod
    def from_tsv(cls, path: PurePath, index: str | None = None) -> Self:
        """Get a NamedTupleTable from Path to .tsv file

        The first row of the tab-separated-variables (TSV) file will be
        interpreted as column headers, e.g.::

          name⇥number⇥cake
          Winnifred⇥1⇥carrot
          Dom⇥⇥2⇥berry

        Where ⇥ represents a TAB whitespace character. Note that multiple TAB
        can be used for visual alignment purposes; they will be merged when
        determining columns. Fields may not be left empty.

        Args:
            path: .tsv file to import
            index: Column name used to access table items

        """
        with path.open() as fd:
            header = fd.readline()
            content = fd.readlines()

        field_names = re_split(r"\t+", header.strip())

        TableRow = namedtuple("TableRow", field_names=field_names)

        table_rows = set()
        for line in content:
            row = TableRow(*re_split(r"\t+", line.strip()))
            table_rows = table_rows | {row}

        return cls(table_rows, index=index)

NTT = TypeVar("NTT", bound=NamedTupleTable)


@lru_cache(maxsize=5)
def _create_with_new_index(
    cls: type[NTT], rows: frozenset[NamedTuple], index: str
) -> NTT:
    new_table = cls(rows, index=index)
    if len(new_table) != len(rows):
        msg = f"Cannot use '{index}' as index: not unique for all items"
        raise ValueError(msg)
    return new_table
