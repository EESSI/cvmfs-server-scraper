"""Server class for cvmfs-server-metadata."""

import json
from typing import Any, Dict, List

from cvmfsscraper.constants import GeoAPIStatus
from cvmfsscraper.repository import Repository
from cvmfsscraper.tools import fetch, fetch_absolute


class CVMFSServer:
    """Base class for CVMFS servers."""

    def __init__(
        self,
        server: str,
        repos: List[str],
        ignore_repos: List[str],
        scrape_on_init: bool = True,
    ):
        """Create a CVMFS server object.

        :param server: The fully qualified DNS name of the server.
        :param repos: List of repositories to always scrape. DEPRECATED, unused.
        :param ignore_repos: List of repositories to ignore.
        :param is_stratum0: Whether the server is a stratum0 server.
        """
        # 1. Get repos from server:
        # /cvmfs/info/v1/repositories.json

        self.name = server

        self.repositories: List[Repository] = []

        self.server_type = None

        if isinstance(self, Stratum0Server):
            self.server_type = 0
        elif isinstance(self, Stratum1Server):
            self.server_type = 1

        self.geoapi_status = GeoAPIStatus.NOT_YET_TESTED
        self.forced_repositories = repos
        self.ignored_repositories = ignore_repos

        self.geoapi_order = [2, 1, 3]

        self._is_down = True

        self.metadata: Dict[str, str] = {}

        self.fetch_errors = []

        if scrape_on_init:
            self.scrape()

    def __str__(self) -> str:
        """Return a string representation of the server."""
        return self.name

    def scrape(self) -> None:
        """Scrape the server."""
        self.repositories = self.populate_repositories()

        if not self.fetch_errors:
            self.geoapi_status = self.check_geoapi_status()

    def show(self) -> str:
        """Show a detailed overview of the server."""
        content = "Server: " + self.name + "\n"
        content += "Metadata:\n"
        for key, value in self.metadata.items():
            content += "  - " + key + ": " + value + "\n"
        content += "Repositories: " + str(len(self.repositories)) + "\n"
        for repo in self.repositories:
            content += "  - " + repo.name + "\n"
        return content

    @staticmethod
    def get_geoapi_url(name: str, repository_name: str) -> str:
        """Generate a GeoAPI URL based on the given parameters.

        Constructs a URL using the provided `name` and `repository_name`.

        :param name: The name used in the URL.
        :param repository_name: The name of the repository used in the URL.

        :returns: The fully formed GeoAPI URL as a string.
        """
        # Note: As a feature, instead of providing an UUID or a proxy, we ca
        # simply pass "x" as the UUID, and the GeoAPI will... work.
        base_url = "http://"
        endpoint = "api/v1.0/geo/x"
        stratum_ones = (
            "cvmfs-s1fnal.opensciencegrid.org,"
            "cvmfs-stratum-one.cern.ch,"
            "cvmfs-stratum-one.ihep.ac.cn"
        )

        full_url = f"{base_url}{name}/cvmfs/{repository_name}/{endpoint}/{stratum_ones}"

        return full_url

    def is_down(self) -> bool:
        """Return whether the server is down or not."""
        return self._is_down

    def is_stratum0(self) -> bool:
        """Return whether the server is a stratum0 server or not."""
        return self.server_type == 0

    def is_stratum1(self) -> bool:
        """Return whether the server is a stratum1 server or not."""
        return self.server_type == 1

    def populate_repositories(self) -> List[Repository]:
        """Populate the repositories list.

        If the server is down, the list will be empty.

        :return: List of repositories.
        """
        content = fetch(self, self.name, "cvmfs/info/v1/repositories.json")

        # This needs to check the error available and probably pop it from the list
        if self.fetch_errors:  # pragma: no cover
            self._is_down = True
            return []

        self._is_down = False

        if content:
            return self.process_repositories_json(content)
        else:  # pragma: no cover
            return []

    def process_repositories_json(self, json_data: str) -> List[Repository]:
        """Process the repositories.json file.

        Note that this file also contains metadata about the server.

        :param json_data: The content of the repositories.json file.

        :return: An alphabetically sorted list of repositories.
        """
        repos_info = json.loads(json_data)
        repos = []

        for key, value in repos_info.items():
            if key == "replicas":
                for repo_info in repos_info["replicas"]:
                    self.server_type = 1
                    if self.process_repo(repo_info):
                        # use "str" to convert from unicode to string
                        repos.append(
                            Repository(self, repo_info["name"], str(repo_info["url"]))
                        )
            elif key == "repositories":
                for repo_info in repos_info["repositories"]:
                    self.server_type = 0
                    if self.process_repo(repo_info):
                        repos.append(
                            Repository(self, repo_info["name"], str(repo_info["url"]))
                        )
            else:
                self.metadata[key] = str(value)

        return sorted(repos, key=lambda repo: repo.name)

    def process_repo(self, repo_info: Dict[str, Any]) -> bool:
        """Check to see if a repository should be processed.

        :param repo_info: The repository information.

        :return: True if the repository should be processed, False otherwise.
        """
        repo_name = repo_info["name"]

        if repo_name in self.ignored_repositories:
            return False

        if "pass-through" in repo_info:  # pragma: no cover
            return False

        return True

    def check_geoapi_status(self) -> GeoAPIStatus:
        """Check the geoapi for the server with the first repo available.

        Checks against the following servers:
            cvmfs-s1fnal.opensciencegrid.org
            cvmfs-stratum-one.cern.ch
            cvmfs-stratum-one.ihep.ac.cn

        The code uses self.geoapi_order to determine the expected order (from closest to
        most distant) for the servers. This defaults to [2, 1, 3], which works for
        bits of northern Europe.

        Returns a GeoAPIStatus enum, which can be one of the following values:
            0 if everything is OK
            1 if the geoapi respons, but with the wrong data
            2 if the geoapi fails to respond
            9 if there is no repository to use for testing.
        """
        # GEOAPI only applies to stratum1s
        if self.server_type == 0:
            return GeoAPIStatus.OK

        if not self.repositories:  # pragma: no cover
            return GeoAPIStatus.NOT_FOUND

        url = self.get_geoapi_url(self.name, self.repositories[0].name)

        try:
            output = fetch_absolute(self, url).decode().strip()
            if output == ",".join(str(item) for item in self.geoapi_order):
                return GeoAPIStatus.OK
            else:
                return GeoAPIStatus.LOCATION_ERROR
        except Exception:  # pragma: no cover
            return GeoAPIStatus.NO_RESPONSE


class Stratum0Server(CVMFSServer):
    """Class for stratum0 servers."""


class Stratum1Server(CVMFSServer):
    """Class for stratum1 servers."""
