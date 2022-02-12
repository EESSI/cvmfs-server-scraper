"""Prometheus exporter for CVMFS Server Scraper"""

import os
import time
from prometheus_client import start_http_server, Gauge, Counter
from cvmfsscraper.main import scrape
import requests

class EESSIMetrics:
    """
    Representation of Prometheus metrics for EESSI infrastructure
    """

    def __init__(self, servers=[], ignore_repos=[]):
        # Prometheus metrics to collet
        servermap = {}

        for server in servers:
            servermap[server] = ".".join(server.split('.')[:2]); #.replace('-', '_')

        self.servermap = servermap

        self.server_geoapi_status = Gauge("server_geoapi_status", "Status for the GeoAPI (0=OK, 1=Wrong answer, 2=Not responding, 9=No repos on server, testing impossible)", ["server"])
        self.server_type = Gauge("server_type", "Server type (0=stratum0, 1=stratum1)", ["server"] )

        self.repo_revision = Gauge("repo_revision", "Revision for a given repository", ["server", "repository"])
        self.repo_revision_timestamp = Gauge("repo_revision_timestamp", "The timestamp of the current revision of the repository", ["server", "repository"])
        self.repo_revision_difference = Gauge("repo_revision_difference", "The difference between the current repository's revision relative to the same repository on stratum0", ["server", "repository"])

        self.repo_last_snapshot = Gauge("repo_snapshot", "Last snapshot for a given repository", ["server", "repository"])
        self.repo_last_gc = Gauge("repo_last_gc", "The last time the repository on a specific server ran garbage collection", ["server", "repository"])
        self.repo_root_size = Gauge("repo_root_size", "Size of the root catalogue of the repository", ["server", "repository"])
        self.repo_root_catalogue_ttl = Gauge("repo_root_catalogue_ttl", "TTL of the root catalogue of the repository", ["server", "repository"])

        self.servers = servers
        self.ignore_repos = ignore_repos

    def run_metrics_loop(self):
        """Metrics fetching loop"""

        while True:
            servers = scrape(
                servers = self.servers,
                ignore_repos = self.ignore_repos,
            )

            current_repo_stratum0_revisions = {}
            for server in servers:
                if server.server_type == 0:
                    for repo in server.repositories:
                        current_repo_stratum0_revisions[repo.name] = repo.revision

            for server in servers:
                nodename=self.servermap[server.name]
                self.server_geoapi_status.labels(server=nodename).set(server.geoapi_status)
                self.server_type.labels(server=nodename).set(server.server_type)

                for repo in server.repositories:
                    self.repo_revision.labels(server=nodename,repository=repo.name).set(repo.revision)
                    self.repo_revision_timestamp.labels(server=nodename,repository=repo.name).set(repo.revision_timestamp)
                    self.repo_revision_difference.labels(server=nodename,repository=repo.name).set(int(current_repo_stratum0_revisions[repo.name]) - int(repo.revision))
                    self.repo_last_gc.labels(server=nodename,repository=repo.name).set(repo.last_gc)
                    self.repo_root_size.labels(server=nodename,repository=repo.name).set(repo.root_size)
                    self.repo_root_catalogue_ttl.labels(server=nodename,repository=repo.name).set(repo.root_catalogue_ttl)


                    if server.server_type == 1:
                        self.repo_last_snapshot.labels(server=nodename,repository=repo.name).set(repo.last_snapshot)
                
            
            time.sleep(60)

def main():
    """Main entry point"""

    exporter_port = int(os.getenv("EXPORTER_PORT", "9877"))

    metrics = EESSIMetrics(
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
            "cvmfs-config.eessi-hpc.org",
        ],
    )
    start_http_server(exporter_port)
    metrics.run_metrics_loop()

if __name__ == "__main__":
    main()
