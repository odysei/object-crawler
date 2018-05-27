# Symbol search utility

The actual binary to digest library contents can be specified by `binary` in the
config (default: `nm -D`).

For options and capabilities, take a look into `config/example.yml`.


## Prerequisites

* Python 2.7
* PyYAML

If a custom installation of PyYAML is used, add it to your PYTHONPATH, example:
```
export PYTHONPATH=/full/path/to/YAML/lib:${PYTHONPATH}
```

## Troubleshooting

If you run into python parsing error, most likely it is the yaml config that is
in trouble.
