
# API Clients

This area contains scripts and libraries to simplify interaction with APIs from [CATH](http://www.cathdb.info) (protein structure classification database) and [SWISS-MODEL](https://swissmodel.expasy.org/) (protein structure homology-modelling server).

### Layout

* `scripts/` -- command line scripts
* `apiclient/` -- python libraries
* `example_data/` -- example data
* `tests/` -- tests

### Examples

**Build a 3D model from template alignment data with the SWISS-MODEL API**

```bash
$ ./scripts/api2.py --in example_data/A0PJE2__35-316.json --out tmp.pdb
```

input (ie `example_data/A0PJE2__35-316.json`):

```json
{
    "auth_asym_id": "A",
    "pdb_id": "3rd5",
    "target_sequence": "---------E--VQIPGRVFLVTGGNSGI...",
    "template_seqres_offset": 0,
    "template_sequence": "GSMTGWTAADLP-SFAQRTVVITGANSGL..."
}
```

log:

```
2019-01-28 19:10:27,047    INFO | DATA:  example_data/A0PJE2__35-316.json
2019-01-28 19:10:27,047    INFO | MODEL: tmp.pdb
2019-01-28 19:10:27,047    INFO | Authenticating ... 
2019-01-28 19:10:27,211    INFO | Loading data from file 'example_data/A0PJE2__35-316.json' ...
2019-01-28 19:10:27,215    INFO | Submitting data ... 
2019-01-28 19:10:27,360    INFO | Checking status of project <f2T3CY> ...
2019-01-28 19:10:27,485    INFO |    status: COMPLETED
2019-01-28 19:10:27,485    INFO | Retrieving results ... 
2019-01-28 19:10:27,738    INFO | Writing coordinates to tmp.pdb
```

Note: add `--verbose` option for more details

