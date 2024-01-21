"""Core of the cvmfsscraper package."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from cvmfsscraper.server import CVMFSServer, Stratum0Server, Stratum1Server


def scrape_server(
    dns_name: str,
    repos: List[str],
    ignore_repos: List[str],
    is_stratum0: bool = False,
) -> CVMFSServer:
    """Scrape a specific server.

    :param dns_name: The fully qualified DNS name of the server.
    :param repos: List of repositories to scrape.
    :param ignore_repos: List of repositories to ignore.
    :param is_stratum0: Whether the server is a stratum0 server.
    """
    if is_stratum0:
        return Stratum0Server(dns_name, repos, ignore_repos)

    return Stratum1Server(dns_name, repos, ignore_repos)


def scrape(
    stratum0_servers: List[str],
    stratum1_servers: List[str],
    repos: List[str],
    ignore_repos: List[str],
) -> List[CVMFSServer]:
    """Scrape a set of servers.

    :param stratum0_servers: List of stratum0 servers, DNS names.
    :param stratum1_servers: List of stratum1 servers, DNS names.
    :param repos: List of repositories to scrape.
    :param ignore_repos: List of repositories to ignore.
    """
    server_objects = []
    processes = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        for server in stratum1_servers:
            processes.append(
                executor.submit(
                    scrape_server, server, repos, ignore_repos, is_stratum0=False
                )
            )
        for server in stratum0_servers:
            processes.append(
                executor.submit(
                    scrape_server, server, repos, ignore_repos, is_stratum0=True
                )
            )

    for task in as_completed(processes):
        server_objects.append(task.result())

    return server_objects
