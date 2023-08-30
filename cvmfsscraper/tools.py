"""Tools for the cvmfsscraper package.

This package is not allowed to import any other packages from cvmfsscraper.
"""
import sys
import urllib.request
from typing import Any


def warn(msg: str, *args: Any, **kwargs: Any) -> None:
    """Print a warning message to stderr."""
    print("WARNING: " + msg, *args, **kwargs, file=sys.stderr)


def deprecated(old: str, new: str) -> None:
    """Print a deprecation warning."""
    warn(old + " is deprecated, please use " + new)


def fetch_absolute(obj: object, url: str) -> str:
    """Fetch an absolute URL, handle exceptions."""
    timeout_seconds = 5
    try:
        content = urllib.request.urlopen(url, timeout=timeout_seconds).read()
        # This is horrific, can we check content-type instead?
        if "json" in url:
            content = content.decode("UTF-8")

        return content
    except Exception as e:
        warn(url, e)
        obj.fetch_errors.append({"path": url, "error": e})

    return


def fetch(obj: object, server: str, path: str) -> str:
    """Fetch a path from a server, handle exceptions."""
    if path.startswith("/"):
        path = path[len("/") :]

    url = "http://" + server + "/" + path
    return fetch_absolute(obj, url)
