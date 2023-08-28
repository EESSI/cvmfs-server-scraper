import urllib.request
import sys


def warn(msg: str) -> None:
    """Print a warning message to stderr"""
    print("WARNING: " + msg, file=sys.stderr)


def deprecated(old: str, new: str) -> None:
    """Print a deprecation warning"""
    warn(old + " is deprecated, please use " + new)


def fetch(obj: object, server: str, path: str) -> str:
    """Fetch a path from a server, handle exceptions"""

    timeout_seconds = 5

    if path.startswith("/"):
        path = path[len("/") :]

    url = "http://" + server + "/" + path
    try:
        content = urllib.request.urlopen(url, timeout=timeout_seconds).read()
        if "json" in path:
            content = content.decode("UTF-8")
        return content
    except Exception as e:
        print(url, e)
        obj.fetch_errors.append({"path", path, "error", e})

    return
