#!/usr/bin/env python3
"""Proof of concept EESSI test script."""

import logging

from cvmfsscraper import scrape, set_log_level

set_log_level(logging.WARNING)

# server = scrape_server("aws-eu-west1.stratum1.cvmfs.eessi-infra.org")

servers = scrape(
    stratum0_servers=["rug-nl-s0.eessi.science"],
    stratum1_servers=[
        "aws-eu-central-s1.eessi.science",
        #        "azure-us-east-s1.eessi.science",
        "aws-eu-west-s1-sync.eessi.science",
    ],
    # We need to force repos due to the sync server using S3 as its backend.
    # S3 does not support reporting the list of repositories.
    repos=["software.eessi.io", "riscv.eessi.io", "dev.eessi.io"],
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
        print("   - " + repo.name + " (" + repo.path + ")")
        print(f"    : Root size: {repo.root_size}")
        print(f"    : Revision: {repo.revision}")
        print(f"    : Revision timestamp: {repo.revision_timestamp}")
        print(f"    : Last snapshot: {repo.last_snapshot}")
        print("    ---")
        for key, attr in sorted(repo.attribute_mapping().items(), key=lambda x: x[1]):
            print(f"    : ({key}) {attr}: {repo.attribute(key)}")

    print()
