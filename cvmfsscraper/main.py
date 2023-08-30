"""Legacy API support for cvmfsscraper."""

from typing import Any, Dict

from cvmfsscraper import scrape as scrape_proper
from cvmfsscraper import scrape_server as scrape_server_proper
from cvmfsscraper.server import CVMFSServer
from cvmfsscraper.tools import deprecated


def scrape(*args: Any, **kwargs: Dict[str, Any]) -> CVMFSServer:
    """Legacy API support for cvmfsscraper."""
    deprecated(
        "cvmfsserver.main.scrape",
        "cvmfsserver.scrape",
    )
    return scrape_proper(*args, **kwargs)


def scrape_server(*args: Any, **kwargs: Dict[str, Any]) -> CVMFSServer:
    """Legacy API support for cvmfsscraper."""
    deprecated(
        "cvmfsserver.main.scrape_server",
        "cvmfsserver.scrape_server",
    )
    return scrape_server_proper(*args, **kwargs)
