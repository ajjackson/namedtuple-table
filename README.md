# namedtuple-table

### Problem
- You want to make a "sample table" config file (e.g. for Snakemake), so that various system-specific attributes can be accessed via an index.
- You want to store it as a human-readable tab-separated text file.
- You don't want to install Pandas.

### Solution
- NamedTupleTable represents tabular data as a mapping between some index column and rows of some NamedTuple.

  ```
  my_table["label_1"] -> ThisTableNamedTuple
  ```

- To index on a different column, produce a new table by calling
  `.with_index("new_index")`. Values of the new index must be unique in
  every row.

- Tables are immutable and hashable, so should play nicely with
  caching, filters etc.  We could add a "select" method etc. but it
  should be straightforward to do this stuff with Python's
  functional programming features.

### Drawbacks

- This is not designed to scale; in the intended use-case the table
  size is modest and you are doing somewhat expensive things with the
  data. If you need performance/scale, consider Pandas or a database
  interface like [dataset](https://pypi.org/project/dataset/).


## Usage example

Store data in a tab-separated variable file. The first non-comment line must be a set of column headers.
Other lines can be commented out with `#` or `!`

```
# dogs.tsv
ref	name		collar	age
1	Bertie		red	4
2	Geoff		blue	2
!3	Bandit		none	40
4	Gertrude	blue	5

```

and load with

```
>>> from namedtuple_table import NamedTupleTable
>>> from pathlib import Path

>>> dogs = NamedTupleTable.from_tsv(Path("dogs.tsv"))

```

Now you have a dict-like Mapping of data rows represented as NamedTuple objects.
All data is loaded as strings, so you might need to cast back and forth to int.

```
>>> print(dogs)
NamedTupleTable (3 items, index = ref)

>>> for i in range(5):
...     if str(i) in dogs:
...         print(dogs[str(i)])
...
TableRow(ref='1', name='Bertie', collar='red', age='4')
TableRow(ref='2', name='Geoff', collar='blue', age='2')
TableRow(ref='4', name='Gertrude', collar='blue', age='5')

>>> dogs['4'].collar
'blue'
```

To use a different index column, get a new table with the `.index_by` method.

```
>>> dogs_by_name = dogs.with_index("name")
>>> dogs_by_name["Geoff"]
TableRow(ref='2', name='Geoff', collar='blue', age='2')
```
