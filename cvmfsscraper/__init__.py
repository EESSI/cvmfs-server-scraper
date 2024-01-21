"""Core of the cvmfsscraper package."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

import structlog

from cvmfsscraper.server import CVMFSServer, Stratum0Server, Stratum1Server

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),  # Ensure compatibility
    cache_logger_on_first_use=True,
)


def set_log_level(level: int) -> None:  # pragma: no cover
    """Set the log level for the library.

    This function allows the consumer of the library to set the desired log level.

    :param level: The log level to set. This should be a value from the logging module,
                  such as logging.INFO, logging.DEBUG, etc.
    """
    logging.basicConfig(level=level, format="%(message)s")
    structlog.configure(
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


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
                executor.submit(scrape_server, server, repos, ignore_repos, is_stratum0=False)
            )
        for server in stratum0_servers:
            processes.append(
                executor.submit(scrape_server, server, repos, ignore_repos, is_stratum0=True)
            )

    for task in as_completed(processes):
        server_objects.append(task.result())

    return server_objects
