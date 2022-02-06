import urllib.request

def fetch(object, server, path):
    """ Fetch a path from a server, handle exceptions """

    url = "http://" + server + "/" + path
    try: 
        content = urllib.request.urlopen(url).read()
        if "json" in path:
            content = content.decode("UTF-8")
        return content
    except Exception as e:
        print(e)
        object.fetch_errors.append({
            "path", path,
            "error", e
        })

    return
