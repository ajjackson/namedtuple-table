from __future__ import annotations

from collections.abc import Mapping
from functools import cache, cached_property
from itertools import tee
from types import MappingProxyType
from typing import Iterable, NamedTuple, TypeVar

NT = TypeVar("NT", bound=NamedTuple)

class NamedTupleTable(Mapping[str|int, NT]):
    """An immutable collection of NamedTuple using one attribute as an index"""

    def __init__(self, rows: Iterable[NT], index: str | None = None) -> None:
        if index is None:
            # Buffer the iterator so we can still iterate from the beginning
            rows, rows_tee = tee(rows)

            # Use the first field in the first item
            index = next(iter(next(rows_tee)._as_dict()))

        self._rows = frozenset(rows)
        self._index = index

    def __str__(self) -> str:
        print(f"NamedTupleTable ({len(self)} items, index = {self._index})")

    @cached_property
    def _map(self) -> MappingProxyType:
        return MappingProxyType(
            {getattr(row, self._index): row for row in self._rows})

    def __getitem__(self, key) -> NT:
        return self._map[key]

    def __hash__(self) -> int:
        return hash((self._index, self._rows))

    def __iter__(self) -> NT:
        return iter(self._rows)

    @cache
    def __len__(self) -> int:
        return len(self._rows)

    def items(self) -> Iterable[tuple[str | int, NT]]:
        return self._map.items()

    @cache
    def with_index(self, index: str | None) -> NamedTupleTable:
        new_table = type(self)(self, index=index)
        if len(new_table) != len(self):
            raise ValueError(
                f"Cannot use '{index}' as index: not unique for all items")
        return new_table
