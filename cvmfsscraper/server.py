"""Server class for cvmfs-server-metadata."""

import json
from typing import Dict, List
from urllib import error, request

import structlog

from cvmfsscraper.constants import GeoAPIStatus
from cvmfsscraper.http_get_models import (
    EndpointClassesType,
    Endpoints,
    GetCVMFSPublished,
    GetCVMFSRepositoriesJSON,
    GetGeoAPI,
    RepositoryOrReplica,
)
from cvmfsscraper.repository import Repository
from cvmfsscraper.tools import GEOAPI_SERVERS

log = structlog.getLogger(__name__)


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

        log.info(
            "Initializing server",
            server=server,
            repos=repos,
            ignore_repos=ignore_repos,
            scrape_on_init=scrape_on_init,
        )

        if scrape_on_init:
            self.scrape()

    def __str__(self) -> str:
        """Return a string representation of the server."""
        return self.name

    def url(self) -> str:
        """Return the URL of the server."""
        return "http://" + self.name

    def scrape(self) -> None:
        """Scrape the server."""
        log.info("Scraping server", server=self.name)

        self.populate_repositories()

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

    def is_down(self) -> bool:
        """Return whether the server is down or not."""
        return self._is_down

    def is_stratum0(self) -> bool:
        """Return whether the server is a stratum0 server or not."""
        return self.server_type == 0

    def is_stratum1(self) -> bool:
        """Return whether the server is a stratum1 server or not."""
        return self.server_type == 1

    def populate_repositories(self) -> None:
        """Populate the repositories list.

        If the server is down, the list will be empty.
        """
        log.info("Populating repositories", server=self.name)
        try:
            repodata = self.fetch_repositories_json()

            if repodata:
                self.process_repositories_json(repodata)

            if self.fetch_errors:  # pragma: no cover
                self._is_down = True
                return []

            self._is_down = False
        except Exception as e:  # pragma: no cover
            log.error(
                "Populate repository failure",
                exc=e,
                server=self.name,
            )
            self.fetch_errors.append({"path": self.name, "error": e})

    def process_repositories_json(self, repodata: GetCVMFSRepositoriesJSON) -> List[Repository]:
        """Process the repositories.json file.

        Sets self.repos and self.metadata.

        :param repodata: The object of the repositories.json file.
        """
        repos_on_server: List[RepositoryOrReplica] = []
        repos: List[Repository] = []

        if repodata.replicas:
            self.server_type = 1
            repos_on_server = repodata.replicas
        else:
            self.server_type = 0
            repos_on_server = repodata.repositories

        for repo in repos_on_server:
            if repo.name in self.ignored_repositories:
                continue
            repos.append(Repository(self, repo.name, repo.url))

        self.repositories = sorted(repos, key=lambda repo: repo.name)

        for key, value in repodata.model_dump().items():
            if key in ["replicas", "repositories"]:
                continue

            self.metadata[key] = str(value)

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

        try:
            geoapi_obj = self.fetch_geoapi(self.repositories[0])
            if geoapi_obj.has_order(self.geoapi_order):
                return GeoAPIStatus.OK
            else:
                return GeoAPIStatus.LOCATION_ERROR
        except Exception as e:  # pragma: no cover
            log.error(
                "GeoAPI failure",
                exc=e,
                name=self.name,
            )
            return GeoAPIStatus.NO_RESPONSE

    def fetch_repositories_json(self) -> GetCVMFSRepositoriesJSON:
        """Fetch the repositories JSON file.

        raises: urlllib.error.URLError (or a subclass thereof) for URL errors.
                pydantic.ValidationError if the object creation fails.

        returns: A GetCVMFSRepositoriesJSON object.
        """
        return self.fetch_endpoint(Endpoints.REPOSITORIES_JSON)

    def fetch_geoapi(self, repo: Repository) -> GetGeoAPI:
        """Fetch the GeoAPI host ordering.

        raises: urlllib.error.URLError (or a subclass thereof) for URL errors.
                pydantic.ValidationError if the object creation fails.

        :returns: A GetGeoAPI object.
        """
        return self.fetch_endpoint(Endpoints.GEOAPI, repo=repo.name)

    def fetch_endpoint(
        self,
        endpoint: Endpoints,
        repo: str = "data",
        geoapi_servers: str = GEOAPI_SERVERS,
    ) -> EndpointClassesType:
        """Fetch and process a specified URL endpoint.

        This function reads the content of a specified URL and ether returns a validated
        CVMFS pydantic model representing the data from the endpoint, or throws an
        exception.

        Note: We are deducing the content type from the URL itself. This is due to cvmfs
        files always returns application/x-cvmfs no matter its content.

        :param endpoint: The endpoint to fetch, as an Endpoints enum value.
        :param repo: The repository used for the endpoint, if relevant. Required for
                 all but Endpoints.REPOSITORIES_JSON. Defaults to "data".
        :param geoapi_servers: Specify the list of DNS names of geoapi servers to use for
                 the geoapi endpoint. Defaults to GEOAPI_SERVERS.

        :raises: PydanticValidationError: If the object creation fails.
                 CVMFSFetchError: If the endpoint is unknown.
                 urllib.error.URLError (or a subclass thereof): If the URL fetch fails.
                 TypeError: If the endpoint is not an Endpoints enum value.

        :returns: An endpoint-specific pydantic model, one of:
                 GetCVMFSPublished (Endpoints.CVMFS_PUBLISHED)
                 GetCVMFSRepositoriesJSON (Endpoints.REPOSITORIES_JSON)
                 GetCVMFSStatusJSON (Endpoints.CVMFS_STATUS_JSON)
                 GetGeoAPI (Endpoints.GEOAPI)
        """
        # We do this validation in case someone passes a string instead of an enum value
        if not isinstance(endpoint, Endpoints):  # type: ignore
            raise TypeError("endpoint must be an Endpoints enum value")

        log.debug("Fetching endpoint", server=self.name, endpoint=endpoint.name, repo=repo)

        geoapi_str = ",".join(geoapi_servers)
        formatted_path = endpoint.path.format(repo=repo, geoapi_str=geoapi_str)
        url = f"{self.url()}/cvmfs/{formatted_path}"

        timeout_seconds = 5
        try:
            log.info("Fetching url", url=url)
            content = request.urlopen(url, timeout=timeout_seconds)

            if endpoint in [Endpoints.REPOSITORIES_JSON, Endpoints.CVMFS_STATUS_JSON]:
                log.debug(
                    "Fetched JSON endpoint",
                    server=self.name,
                    endpoint=endpoint.name,
                    repo=repo,
                )
                content = json.loads(content.read())
            elif endpoint == Endpoints.CVMFS_PUBLISHED:
                log.debug(
                    "Fetched .cvmfspublished",
                    server=self.name,
                    endpoint=endpoint.name,
                    repo=repo,
                )
                content = GetCVMFSPublished.parse_blob(content.read())
            elif endpoint == Endpoints.GEOAPI:
                log.debug(
                    "Fetched geoapi",
                    server=self.name,
                    endpoint=endpoint.name,
                    repo=repo,
                )
                indices = [int(x) for x in content.read().decode().split(",")]
                content = {
                    "host_indices": indices,
                    "host_names_input": geoapi_servers,
                }

            return endpoint.model_class(**content)

        except error.URLError as e:
            log.error(
                "Fetch endpoint failure",
                exc=e,
                name=self.name,
                endpoint=endpoint.name,
                repo=repo,
                url=url,
            )
            raise e from e


class Stratum0Server(CVMFSServer):
    """Class for stratum0 servers."""


class Stratum1Server(CVMFSServer):
    """Class for stratum1 servers."""
