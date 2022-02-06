#!/usr/bin/env python3

from cvmfsscraper.main import scrape, scrape_server

server = scrape_server("aws-eu-west1.stratum1.cvmfs.eessi-infra.org")

print(server)

for repo in server.repositories:
    print("Repo: " + repo.name )
    print("Root size: " + repo.root_size)
    print("Revision: " + repo.revision)
    print("Revision timestamp: " + repo.revision_timestamp)
    print("Last snapshot: " + str(repo.last_snapshot))