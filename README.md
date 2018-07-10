# CATH / SWISS-MODEL API

[![Build Status](https://travis-ci.com/CATH-SWISSMODEL/cath-swissmodel-api.svg?branch=master)](https://travis-ci.com/CATH-SWISSMODEL/cath-swissmodel-api)

This repository is here to help development relating to the CATH / SWISS-MODEL (2018 ELIXIR Implementation Study).

General layout:

```
├── api      OpenAPI specification docs
├── docs     general project admin
└── perl5    Perl code (tests)
```

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


