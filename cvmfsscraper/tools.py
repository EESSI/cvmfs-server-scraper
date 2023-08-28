import urllib.request


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
