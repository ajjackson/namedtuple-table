"""Simple indexable tables based on NamedTuple"""

from __future__ import annotations

from collections import namedtuple
from collections.abc import Iterable, Iterator, Mapping
from functools import cached_property, lru_cache
from itertools import tee
from re import split as re_split
from types import MappingProxyType
from typing import TYPE_CHECKING, NamedTuple, TypeVar

if TYPE_CHECKING:
    from io import TextIOBase
    from pathlib import Path


NT = TypeVar("NT", bound=NamedTuple)


class NamedTupleTable(Mapping[str | int, NT]):
    """An immutable collection of NamedTuple using one attribute as an index

    Args:
        rows:  Input data as a consistent set of NamedTuple
        index: Name of index column. This must be a field in the NamedTuple class

    """

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
        """Get string representation"""
        return f"NamedTupleTable ({len(self._rows)} items, index = {self._index})"

    @cached_property
    def _map(self) -> MappingProxyType:
        return MappingProxyType({getattr(row, self._index): row for row in self._rows})

    def __getitem__(self, key: int | str) -> NT:
        """Get item at key in index column"""
        return self._map[key]

    def __hash__(self) -> int:
        """Get hash of table index and data"""
        return hash((self._index, self._rows))

    def __iter__(self) -> Iterator[str | int]:
        """Get iterator over keys in index column"""
        return iter(self._map)

    @cached_property
    def _len(self) -> int:
        return len(self._map)

    def __len__(self) -> int:
        """Get number of rows in table"""
        return self._len

    def with_index(self, index: str | None) -> NamedTupleTable:
        """Get a new table using a different index column

        Note that the underlying NamedTuple collection is identical

        e.g. from TSV data::

          name  ref  colour
          Bob   1    blue
          Rob   2    red

        >> table["Bob"]
        blue

        >> table.with_index("ref")["2"]
        red

        Args:
            index:  Indexed column of new table

        """
        return _create_with_new_index(type(self), self._rows, index)

    @classmethod
    def from_tsv(cls, path: Path, index: str | None = None) -> NamedTupleTable:
        """Get a NamedTupleTable from Path to .tsv file

        The first row of the tab-separated-variables (TSV) file will be
        interpreted as column headers, e.g.::

          name⇥number⇥cake
          Winnifred⇥1⇥carrot
          Dom⇥⇥2⇥berry

        Where ⇥ represents a TAB whitespace character. Note that multiple TAB
        can be used for visual alignment purposes; they will be merged when
        determining columns. Fields may not be left empty.

        Lines may be "commented out" by starting with the character # or !

        Args:
            path: .tsv file to import
            index: Column name used to access table items

        """
        with path.open() as fd:
            header, *content = list(_strip_comments(fd))

        field_names = re_split(r"\t+", header)

        TableRow = namedtuple("TableRow", field_names)  # type: ignore[misc]  # noqa: PYI024

        table_rows: set[TableRow] = set()
        for line in content:
            try:
                row = TableRow(*re_split(r"\t+", line))
            except TypeError as err:
                msg = (f"Could not populate columns {TableRow.__dict__['_fields']} "
                       f"from line '{line}'")
                raise TypeError(msg) from err
            table_rows = table_rows | {row}

        return NamedTupleTable(table_rows, index=index)


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


def _strip_comments(fd: TextIOBase) -> Iterator[str]:
    for line in fd:
        if (stripped_line := line.strip())[0] in "#!":
            continue
        yield stripped_line
