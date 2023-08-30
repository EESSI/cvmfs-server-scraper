#!/usr/bin/env python3
"""Proof of concept EESSI test script."""

from cvmfsscraper import scrape

# server = scrape_server("aws-eu-west1.stratum1.cvmfs.eessi-infra.org")

servers = scrape(
    stratum0_servers=[
        "rug-nl.stratum0.cvmfs.eessi-infra.org",
    ],
    stratum1_servers=[
        "aws-eu-west1.stratum1.cvmfs.eessi-infra.org",
        "azure-us-east1.stratum1.cvmfs.eessi-infra.org",
        "bgo-no.stratum1.cvmfs.eessi-infra.org",
        "rug-nl.stratum1.cvmfs.eessi-infra.org",
    ],
    repos=[],
    ignore_repos=[
        "bla.eessi-hpc.org",
        "bob.eessi-hpc.org",
        "ci.eessi-hpc.org",
    ],
)

print("Servers:")
for server in servers:
    print(server.name)
    print("  GeoAPI status: " + str(server.geoapi_status))
    print("  Metadata:")
    for key, value in sorted(server.metadata.items(), key=lambda x: x[1]):
        print("   - " + key + ": " + value)
    print("  Repositories: ")
    for repo in server.repositories:
        print("   - " + repo.name)
        print("    : Root size: " + repo.root_size)
        print("    : Revision: " + repo.revision)
        print("    : Revision timestamp: " + repo.revision_timestamp)
        print("    : Last snapshot: " + str(repo.last_snapshot))
        print("    ---")
        for key, attr in sorted(repo.attribute_mapping().items(), key=lambda x: x[1]):
            print("    : (" + key + ") " + attr + ": " + repo.attribute(key))

    print()
