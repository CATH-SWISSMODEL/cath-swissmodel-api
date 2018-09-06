# CATH / SWISS-MODEL API

[![Build Status](https://travis-ci.com/CATH-SWISSMODEL/cath-swissmodel-api.svg?branch=master)](https://travis-ci.com/CATH-SWISSMODEL/cath-swissmodel-api)

This repository is here to help development relating to the CATH / SWISS-MODEL API (2018 ELIXIR Implementation Study).

General layout:

```
├── spec     latest OpenAPI specification docs for each API (1-4)
├── cathapi  Backend code for CATH API (1, 3, 4) [Python/Django]
├── docs     general project admin
└── perl5    Tests and backend API (latter now deprecated in favour of Python/Django)
```

The project has four individual APIs, each with its own set of operations / endpoints. The table below provides a general summary, more details can be found in the admin directory.

## API

**API 1: Get3DTemplate (UCL)** -- For a given query protein sequence, identify the most appropriate known structural domain to use for the 3D structural modelling.

**API 2: Get3DModel (SWISSMODEL)** -- For a given sequence, alignment and template identify the most appropriate known structural domain to use for the 3D structural modelling.

**API 3: GetFunData (CATH)** -- Provide access to functional terms and functional site data for the respective functional families (to provide additional annotations for query sequences).

**API 4: GetPutativeModelSequences (CATH)** -- Provide information on the number of potential models that can be built by a query structure (used by PDBe).

|   | Name | Resource | Input | Output |
|---|---|---|---|---|
| 1 | Get3DTemplate | CATH | protein sequence (FASTA) | <ul><li>template structure (PDB ID)</li><li>alignment (FASTA)</li></ul> |
| 2 | Get3DModel | SWISS-MODEL | <ul><li>protein sequence (FASTA)</li><li>template structure (PDB ID)</li><li> alignment (FASTA)</li></ul> | 3D coords (PDB) |
| 3 | GetFunData | CATH | protein sequence (FASTA) | JSON 
| 4 | GetPutativeModelSequences | CATH | protein sequence (FASTA) | UniProtKB accessions |


### Getting started

Setup a local python virtual environment; install dependencies.

```sh
$ cd cath-swissmodel-api
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements.txt
```

### Starting a local server

```sh
$ source ./venv/bin/activate
$ cd cathapi/
$ ./manage.py runserver
```

http://127.0.0.1:8000/
