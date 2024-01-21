"""Legacy API support for cvmfsscraper."""

from typing import Any, Dict, List

import structlog

from cvmfsscraper import scrape as scrape_proper
from cvmfsscraper import scrape_server as scrape_server_proper
from cvmfsscraper.server import CVMFSServer
from cvmfsscraper.tools import deprecated

deplog = structlog.getLogger("deprecation")


def scrape(*args: Any, **kwargs: Dict[str, Any]) -> List[CVMFSServer]:
    """Legacy API support for cvmfsscraper."""
    deprecated(
        "cvmfsserver.main.scrape",
        "cvmfsserver.scrape",
    )
    deplog.warning(
        "Deprecated API used",
        deprecated="cvmfsserver.main.scrape",
        replacement="cvmfsserver.scrape",
        message=(
            "cvmfsserver.main.scrape is deprecated and will be removed in a future release."
            "Please use cvmfsserver.scrape instead."
        ),
    )
    return scrape_proper(*args, **kwargs)


def scrape_server(*args: Any, **kwargs: Dict[str, Any]) -> CVMFSServer:
    """Legacy API support for cvmfsscraper."""
    deprecated(
        "cvmfsserver.main.scrape_server",
        "cvmfsserver.scrape_server",
    )
    deplog.warning(
        "Deprecated API used",
        deprecated="cvmfsserver.main.scrape_server",
        replacement="cvmfsserver.scrape_server",
        message=(
            "cvmfsserver.main.scrape_server is deprecated and will be removed in a future release."
            "Please use cvmfsserver.scrape_server instead."
        ),
    )
    return scrape_server_proper(*args, **kwargs)
