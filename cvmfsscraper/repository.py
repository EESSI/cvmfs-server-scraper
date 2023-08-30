"""A CVMFS repository."""
import datetime
import json
import sys
from typing import Dict

from cvmfsscraper.tools import fetch


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

        :param server: The server object.
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

        content = fetch(self, self.server.name, self.path + "/.cvmfspublished")
        self.parse_cvmfspublished(content)

        content = fetch(self, self.server.name, self.path + "/.cvmfs_status.json")
        self.parse_status_json(content)

    def __str__(self) -> str:
        """Return a string representation of the repository."""
        return self.name

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
            attribute = self.KEY_TO_ATTRIBUTE_MAPPING.get(attribute)

        return getattr(self, attribute, "None")

    def attributes(self) -> Dict[str, str]:
        """Return a dictionary of the attributes for the repository manifest.

        This is parsed from .cvmfspublished.
        """
        attributes = {}
        for key, attr in self.KEY_TO_ATTRIBUTE_MAPPING.items():
            attributes[key] = getattr(self, attr, "None")
        return attributes

    def parse_status_json(self, json_data: str) -> None:
        """Parse the contents of a .cvmfs_status.json file.

        :param json_data: The JSON data to parse.
        """
        if not json_data:
            return

        try:
            repo_status = json.loads(json_data)
            self._repo_status_loaded = 1
        except Exception as exc:  # pragma: no cover (probably should exit)
            print("Error parsing JSON: " + str(exc))
            sys.exit(1)

        timeformat = "%a %b %d %H:%M:%S %Z %Y"

        if "last_snapshot" in repo_status:
            self.last_snapshot = datetime.datetime.strptime(
                repo_status["last_snapshot"], timeformat
            ).timestamp()

        if "last_gc" in repo_status:
            self.last_gc = datetime.datetime.strptime(
                repo_status["last_gc"], timeformat
            ).timestamp()

    def parse_cvmfspublished(self, content: str) -> None:
        """Parse a .cvmfspublished file.

        https://cvmfs.readthedocs.io/en/stable/cpt-details.html#internal-manifest-structure.
        """
        if not content:
            return

        self._cvmfspublished_loaded = 1

        signature_inc = False
        self.signature = bytes()
        for line in content.splitlines():
            if signature_inc:
                self.signature = self.signature + line
            else:
                if chr(line[0]) == "-":
                    signature_inc = True
                else:
                    line = line.decode("iso-8859-1")
                    (key, value) = (line[0], line[1:])
                    self.process_cvmfspublished_key_value(key, value)

        return

    def process_cvmfspublished_key_value(self, key: str, value: str) -> None:
        """Process a key/value pair from the .cvmfspublished file.

        :param key: The key from the .cvmfspublished file.
        :param value: The value associated with the key.

        :raises: AttributeError if the attribute doesn't exist in the class.
        """
        attribute_name = self.KEY_TO_ATTRIBUTE_MAPPING.get(key)

        if attribute_name:
            setattr(self, attribute_name, value)
