"""A CVMFS repository."""
from typing import Dict

import structlog

from cvmfsscraper.http_get_models import (
    Endpoints,
    GetCVMFSPublished,
    GetCVMFSStatusJSON,
)

log = structlog.getLogger(__name__)


class Repository:
    """A CVMFS repository.

    :param server: The server object.
    :param name: The name of the repository.
    :param url: The URL of the repository.
    """

    KEY_TO_ATTRIBUTE_MAPPING = {
        "C": "root_cryptographic_hash",
        "B": "root_size",
        "A": "alternative_name",
        "R": "root_path_hash",
        "X": "signing_certificate_cryptographic_hash",
        "G": "is_garbage_collectable",
        "H": "tag_history_cryptographic_hash",
        "T": "revision_timestamp",
        "D": "root_catalogue_ttl",
        "S": "revision",
        "N": "full_name",
        "M": "metadata_cryptographic_hash",
        "Y": "reflog_checksum_cryptographic_hash",
        "L": "micro_catalogues",
    }

    def __init__(self, server: object, name: str, url: str):
        """Initialize the repository.

        :param server: The server object this repository belongs to.
        :param name: The name of the repository.
        :param url: The URL of the repository.
        """
        self.server = server
        self.name = name
        self.path = url

        self.last_gc = None
        self.last_snapshot = None

        self._repo_status_loaded = 0
        self._cvmfspublished_loaded = 0

        # 1. Get data per repo:
        #  a. {url}/.cvmfspublished : Overall data
        #  b. {url}/.cvmfs_status.json

        self.fetch_errors = []

        log.debug("Initalizing repository", server=server.name, name=name, url=url)

        self.scrape()

    def __str__(self) -> str:
        """Return a string representation of the repository."""
        return self.name

    def scrape(self) -> None:
        """Scrape the repository."""
        log.debug("Scraping repository", server=self.server, name=self.name, url=self.path)
        try:
            cvmfspublished = self.fetch_cvmfspublished()
            self.parse_cvmfspublished(cvmfspublished)
        except Exception as exc:
            log.warn(
                "Scrape error",
                exc=exc,
                server=self.server,
                name=self.name,
                url=self.path,
            )
            self.fetch_errors.append({"path": self.path, "error": exc})

        try:
            repo = self.fetch_repository()
            self.parse_status_json(repo)
        except Exception as exc:
            log.warn(
                "Scrape error",
                exc=exc,
                server=self.server,
                name=self.name,
                url=self.path,
            )
            self.fetch_errors.append({"path": self.path, "error": exc})

    def attribute_mapping(self) -> Dict[str, str]:
        """Return the attribute mapping."""
        return self.KEY_TO_ATTRIBUTE_MAPPING

    def attribute(self, attribute: str) -> str:
        """Return the value of an attribute from the repository manifest.

        Supports both the single character code used in .cvmfspublished and
        and the full attribute name provided by the interal mapping.

        :param attribute: The attribute to return.
        """
        if len(attribute) == 1:
            attribute = self.KEY_TO_ATTRIBUTE_MAPPING.get(attribute, attribute)
        return getattr(self, attribute, "None")

    def attributes(self) -> Dict[str, str]:
        """Return a dictionary of the attributes for the repository manifest.

        This is parsed from .cvmfspublished.
        """
        attributes = {}
        for key, attr in self.KEY_TO_ATTRIBUTE_MAPPING.items():
            attributes[key] = getattr(self, attr, "None")
        return attributes

    def parse_status_json(self, obj: GetCVMFSStatusJSON) -> None:
        """Parse the contents of a .cvmfs_status.json file.

        :param json_data: The JSON data to parse.
        """
        self._repo_status_loaded = 1

        self.last_snapshot = obj.last_snapshot
        self.last_gc = obj.last_gc

    def parse_cvmfspublished(self, obj: GetCVMFSPublished) -> None:
        """Parse a .cvmfspublished file.

        https://cvmfs.readthedocs.io/en/stable/cpt-details.html#internal-manifest-structure.
        """
        self._cvmfspublished_loaded = 1

        for key, value in obj.model_dump().items():
            attribute_name = self.KEY_TO_ATTRIBUTE_MAPPING.get(key, key)
            setattr(self, attribute_name, value)

    def fetch_cvmfspublished(self) -> GetCVMFSPublished:
        """Fetch the CVMFSPublished file for a given repo.

        raises: urlllib.error.URLError (or a subclass thereof) for URL errors.
                pydantic.ValidationError if the object creation fails.

        :returns: A GetCVMFSPublished object.
        """
        return self.server.fetch_endpoint(Endpoints.CVMFS_PUBLISHED, self.name)

    def fetch_repository(self) -> GetCVMFSStatusJSON:
        """Fetch a repository by name.

        raises: urlllib.error.URLError (or a subclass thereof) for URL errors.
                pydantic.ValidationError if the object creation fails.

        :returns: GetCVMFSStatusJSON object.
        """
        return self.server.fetch_endpoint(Endpoints.CVMFS_STATUS_JSON, self.name)
