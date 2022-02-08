#!/usr/bin/env python3

from cvmfsscraper.main import scrape, scrape_server

# server = scrape_server("aws-eu-west1.stratum1.cvmfs.eessi-infra.org")

servers = scrape(
    servers = [
        "rug-nl.stratum0.cvmfs.eessi-infra.org",
        "aws-eu-west1.stratum1.cvmfs.eessi-infra.org",
        "azure-us-east1.stratum1.cvmfs.eessi-infra.org",
        "bgo-no.stratum1.cvmfs.eessi-infra.org",
        "rug-nl.stratum1.cvmfs.eessi-infra.org",
    ],
    ignore_repos = [
        "bla.eessi-hpc.org",
        "bob.eessi-hpc.org",
        "ci.eessi-hpc.org",
    ],
)

print(servers[0])

for repo in servers[0].repositories:
    print("Repo: " + repo.name )
    print("Root size: " + repo.root_size)
    print("Revision: " + repo.revision)
    print("Revision timestamp: " + repo.revision_timestamp)
    print("Last snapshot: " + str(repo.last_snapshot))