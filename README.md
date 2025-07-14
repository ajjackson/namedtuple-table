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

- To index on a different column, produce a new table with
  `.index_by("new_index")`. Values of the new index must be unique in
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
