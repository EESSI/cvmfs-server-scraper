# CVMFS server scraper and prometheus exporter

This tool scrapes the public metadata sources from set of stratum0 and stratum1 servers. It grabs:

    - cvmfs/info/v1/repositories.json 

And then for every repo it finds (that it's not told to ignore), it grabs:

    - cvmfs/<repo>/.cvmfs_status.json
    - cvmfs/<repo>/.cvmfspublished

## Installation

`pip install cvmfs-server-scraper`

## Usage

````python
#!/usr/bin/env python3

import logging
from cvmfsscraper import scrape, scrape_server, set_log_level

# server = scrape_server("aws-eu-west1.stratum1.cvmfs.eessi-infra.org")

set_log_level(logging.DEBUG)

servers = scrape(
    stratum0_servers=[
        "stratum0.tld",
    ],
    stratum1_servers=[
        "stratum1-no.tld",
        "stratum1-au.tld",
    ],
    repos=[],
    ignore_repos=[],
)

# Note that the order of servers is undefined.
print(servers[0])

for repo in servers[0].repositories:
    print("Repo: " + repo.name )
    print("Root size: " + repo.root_size)
    print("Revision: " + repo.revision)
    print("Revision timestamp: " + repo.revision_timestamp)
    print("Last snapshot: " + str(repo.last_snapshot))
````

Note that if you are using a Stratum1 server with S3 as its backend, you need to set repos explicitly.
This is because the S3 backend does not have a `cvmfs/info/v1/repositories.json` file. Also, the GeoAPI
status will be `NOT_FOUND` for these servers.

````python

# Data structure

## Server

A server object, representing a specific server that has been scraped.

````python
servers = scrape(...)
server_one = servers[0]
````

### Name

#### Type: Attribute

`server.name`

#### Returns

The name of the server, usually its fully qualified domain name.

### GeoApi status

#### Type: Attribute

`server.geoapi_status`

#### Returns

A GeoAPIstatus enum object. Defined in `constants.py`. The possible values are:

- OK (0: OK)
- LOCATION_ERROR (1: GeoApi gives wrong location)
- NO_RESPONSE (2: No response)
- NOT_FOUND (9: The server has no repository available so the GeoApi cannot be tested)
- NOT_YET_TESTED (99: The server has not yet been tested)

### Repositories

#### Type: attribute

`server.repositories`

#### Returns

A list of repository objects, sorted by name. Empty if no repositores are scraped on the server.

### Ignored repositories

#### Type: Attribute

`server.ignored_repositories`

#### Returns

List of repositories names that are to be ignored by the scraper.

### Forced repositories

#### Type: Attribute

`server.forced_repositories`

#### Returns

A list of repository names that the server is forced to scrape. If a repo name exists in both ignored_repositories and forced_repositories, it will be scraped.

## Repository

A repository object, representing a single repository on a scraped server.

````python
servers = scrape(...)
repo_one = servers[0].repositories[0]
````

### Name

#### Type: Attribute

`repo_one.name`

#### Returns

The fully qualified name of the repository.

### Server

#### Type: Attribute

`repo_one.server`

#### Returns

The server object to which the repository belongs.

### Path

#### Type: Attribute

`repo_one.path`

#### Returns

The path for the repository on the server. May differ from the name. To get a complete URL, one can do:

`url = "http://" + repo_one.server.name + repo_one.path`

### Status attributes

These attributes are populated from `cvmfs_status.json`:

| Attribute | Value |
| --- | --- |
| last_gc | Timestamp of last garbage collection |
| last_snapshot | Timestamp of the last snapshot |

Information from `.cvmfspublished` is also provided. For explanations for these keys, please see CVMFS' [official documentation](https://cvmfs.readthedocs.io/en/stable/cpt-details.html). The field value in the table is the field key from `.cvmfspublished`.

| Attribute | Field |
| --- | --- |
| alternative_name | A |
| full_name | N |
| is_garbage_collectable | G |
| metadata_cryptographic_hash | M |
| micro_cataogues | L |
| reflog_checksum_cryptographic_hash | Y |
| revision_timestamp | T |
| root_catalogue_ttl | D |
| root_cryptographic_hash | C |
| root_size | B |
| root_path_hash | R |
| signature | The end signature blob |
| signing_certificate_cryptographic_hash | X |
| tag_history_cryptographic_hash | H |
