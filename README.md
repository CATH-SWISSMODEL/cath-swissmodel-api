# CATH / SWISS-MODEL API

This repository is here to help development relating to the CATH / SWISS-MODEL API
(2018/19 ELIXIR Implementation Study).

The CATH-SM pipeline effectively glues together APIs from two Bioinformatics
resources ([CATH](https://www.cathdb.info) and [SWISS-MODEL](https://swissmodel.expasy.org/))
to predict 3D structures from protein sequences. The resulting models are then
made available in other ELIXIR resources: first [Genome3D](https://www.genome3d.eu),
then on to [InterPro](https://www.ebi.ac.uk/interpro/) and
[PDBe](https://www.ebi.ac.uk/pdbe/).

## Overview

The main output of this project is to provide a pipeline that models 3D structures from protein sequence.

Jobs can be submitted to this pipeline via [web pages](https://api01.cathdb.info).

Alternatively, jobs can also be submitted via CLI tools (and libraries):

* [`cathsm-client`](https://github.com/CATH-SWISSMODEL/cathsm-client)

Note: the backend code for the pipeline and web pages is available here:

* [`cathsm-server`](https://github.com/CATH-SWISSMODEL/cathsm-server)

## API Overview

The pipeline outlined above depends on the following APIs:

**API 1: Get3DTemplate (UCL)** -- For a given query protein sequence, identify the most appropriate known structural domain to use for the 3D structural modelling.

| Input | Output |
|---|---|
| protein sequence (FASTA) | <ul><li>template structure (PDB ID)</li><li>alignment (FASTA)</li></ul> |

**API 2: Get3DModel (SWISSMODEL)** -- For a given sequence, alignment and template identify the most appropriate known structural domain to use for the 3D structural modelling.

| Input | Output |
|---|---|
| <ul><li>protein sequence (FASTA)</li><li>template structure (PDB ID)</li><li> alignment (FASTA)</li></ul> | 3D coords (PDB) |

**API 3: GetFunData (CATH)** -- Provide access to functional terms and functional site data for the respective functional families (to provide additional annotations for query sequences).

| Input | Output |
|---|---|
| protein sequence (FASTA) | JSON |

**API 4: GetPutativeModelSequences (CATH)** -- Provide information on the number of potential models that can be built by a query structure (used by PDBe).

| Input | Output |
|---|---|
| protein sequence (FASTA) | UniProtKB accessions |


## Useful Links

### OpenAPI

* http://openapi.tools/ -- List of tools, libraries
* https://editor.swagger.io/ -- Live code editor
* https://github.com/openapitools/openapi-generator -- Generate backend code based on OpenAPI document

### OAuth2

* Specification docs - https://oauth.net/2/

There are a few different flows according to what particular type of authentication system is required, but typical authentication flow might look like:
1. client logs in, server generates token, server sends token back to client
1. client adds token to the header of all subsequent requests
1. server uses token to validate who is making the request
1. server checks that this user is authorised for this endpoint (eg. using OpenAPI spec)
1. client logs out

