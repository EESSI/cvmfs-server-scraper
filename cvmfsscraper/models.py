"""Pydantic models for CVMFS HTTP responses."""
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from cvmfsscraper.exceptions import CVMFSValidationError


def hex_field(min_length: int, max_length: int, alias: str):
    """Create a Field for hexadecimal strings with a specified length range.

    :param min_length: Minimum length of the hex string.
    :param max_length: Maximum length of the hex string.
    :param alias: Alias for the field.

    :returns: A Pydantic Field object.
    """
    return Field(..., alias=alias, min_length=min_length, max_length=max_length)


class CVMFSBaseModel(BaseModel):
    """Base model for CVMFS models."""


class RepositoryOrReplica(BaseModel):
    """Model for a repository or replica."""

    name: str = Field(..., description="The name of the repository or replica")
    url: str = Field(..., description="The local URL part of the repository or replica")


class GetGeoAPI(CVMFSBaseModel):
    """Model for the GeoAPI host ordering."""

    host_indices: List[int] = Field(..., description="Ordering received from API")
    host_names_input: List[str] = Field(..., description="Host names provided as input")

    @model_validator(mode="after")
    def validate_and_set_host_names(self) -> "GetGeoAPI":
        """Validate the input and set the host_names_ordered field."""
        host_names_input = self.host_names_input

        if len(host_names_input) != len(self.host_indices):
            raise ValueError(
                "host_indices and host_names_input must be of the same length."
            )

    def host_names_ordered(self) -> List[str]:
        """Return the host names in the order specified by the GeoAPI."""
        return [self.host_names_input[i - 1] for i in self.host_indices]


class GetCVMFSStatusJSON(CVMFSBaseModel):
    """Model for the CVMFS status JSON structure."""

    last_snapshot: Optional[datetime] = Field(
        None,
        description="The last snapshot time",
        json_schema_extra={"format": "%a %b %d %H:%M:%S %Z %Y"},
    )

    last_gc: datetime = Field(
        ...,
        description="The last garbage collection time",
        json_schema_extra={"format": "%a %b %d %H:%M:%S %Z %Y"},
    )

    @field_validator("last_snapshot", "last_gc", mode="before")
    def convert_cvmfs_date_to_datetime(cls, value: str) -> datetime:
        """Convert a string to a datetime object.

        :param value: The string to be converted.

        :raises: ValueError if the conversion fails.

        :returns: The converted datetime object.
        """
        return datetime.strptime(value, "%a %b %d %H:%M:%S %Z %Y")


class GetCVMFSRepositoriesJSON(CVMFSBaseModel):
    """Model for the repositories JSON structure."""

    model_config = {
        "populate_by_name": True,
    }

    schema_version: int = Field(
        ..., alias="schema", description="The schema version", gt=0
    )
    # Stratum0 does not have a last_geodb_update field.
    last_geodb_update: Optional[datetime] = Field(
        None,
        json_schema_extra={"format": "%a %b %d %H:%M:%S %Z %Y"},
        description="The last GeoDB update time",
    )
    cvmfs_version: str = Field(..., description="The CVMFS version")
    os_id: str = Field(..., description="The OS ID")
    os_version_id: str = Field(..., description="The OS version ID")
    os_pretty_name: str = Field(..., description="The pretty name of the OS")
    repositories: Optional[List[RepositoryOrReplica]] = Field(
        None, description="List of repositories"
    )

    replicas: Optional[List[RepositoryOrReplica]] = Field(
        None, description="List of replicas"
    )

    @field_validator("last_geodb_update", mode="before")
    def convert_cvmfs_date_to_datetime(cls, value: str) -> datetime:
        """Convert a string to a datetime object.

        :param value: The string to be converted.

        :raises: ValueError if the conversion fails.

        :returns: The converted datetime object.
        """
        return datetime.strptime(value, "%a %b %d %H:%M:%S %Z %Y")

    @model_validator(mode="after")
    def check_only_one_is_set(self) -> "GetCVMFSRepositoriesJSON":
        """Ensure that only one of repositories or replicas is set."""
        replicas = self.replicas
        repositories = self.repositories
        if repositories and replicas:
            raise ValueError("Only one of repositories or replicas should be set.")
        if not repositories and not replicas:
            raise ValueError("At least one of repositories or replicas should be set.")
        return repositories


class GetCVMFSPublished(CVMFSBaseModel):
    """A model for the published file catalog.

    This model includes various fields that correspond to specific keys
    within a binary blob. The keys are single-character identifiers, and
    they map to more descriptive field names within this class.
    """

    model_config = {
        "populate_by_name": True,
    }

    @classmethod
    def parse_blob(cls, blob: bytes) -> Dict[str, Any]:
        """Parse a binary blob into a CVMFSPublished instance.

        The binary blob is expected to be in a specific format where
        each line contains a key-value pair. The key is a single character,
        and the value follows, until we reach a '--' line, which indicates
        the start of the signature. See
        https://cvmfs.readthedocs.io/en/stable/cpt-details.html#repository-manifest-cvmfspublished
        for more details.

        Mapping:
        C -> root_catalog_hash
        B -> root_file_catalog_size
        A -> fetch_alternative_name
        R -> root_path_hash
        D -> ttl_of_root_catalog
        S -> published_revision
        G -> is_garbage_collectable
        N -> full_name
        X -> signing_certificate_hash
        H -> tag_history_hash
        T -> timestamp
        M -> json_metadata_hash
        Y -> reflog_checksum_hash


        :param blob: The binary blob to be parsed.

        :raises CVMFSValueError: Raised if the blob is malformed or empty.

        :returns: A dictionary that can be used to create an instance of a
                  CVMFSPublished object.
        """
        lines = blob.decode().split("\n")
        data = {}
        signature_lines = []
        parse_signing_cert = False
        for i, line in enumerate(lines):
            if line.startswith("--"):
                parse_signing_cert = True
                continue
            if parse_signing_cert:
                signature_lines.append(line.strip())
                break
            else:
                try:
                    key, value = line[0], line[1:]
                except IndexError as exc:
                    raise CVMFSValidationError(f"Line {i}: Empty line?") from exc

                if key not in "CBARDSGNXHTMY":
                    raise CVMFSValidationError(f"Line {i}: Unknown key '{key}'")

                if key in "AG":
                    if value.lower() == "yes":
                        value = True
                    elif value.lower() == "no":
                        value = False
                    else:
                        raise CVMFSValidationError(
                            f"Line {i}: '{key}' expected 'yes' or 'no', got '{value}'"
                        )
                data[key] = value

        data["signing_certificate"] = "\n".join(signature_lines)

        return data

    root_catalog_hash: str = hex_field(40, 40, "C")
    root_file_catalog_size: int = Field(..., alias="B", gt=0)
    fetch_alternative_name: bool = Field(..., alias="A")
    root_path_hash: str = hex_field(32, 32, "R")
    ttl_of_root_catalog: int = Field(..., alias="D", gt=0)
    published_revision: int = Field(..., alias="S", gt=0)
    is_garbage_collectable: bool = Field(..., alias="G")
    full_name: str = Field(..., alias="N")
    signing_certificate_hash: str = hex_field(40, 40, "X")
    tag_history_hash: str = hex_field(40, 40, "H")
    timestamp: datetime = Field(..., alias="T")
    json_metadata_hash: str = hex_field(40, 40, "M")
    reflog_checksum_hash: str = hex_field(40, 40, "Y")

    def get_catalog_entry(self, name_or_alias: str) -> Any:
        """Retrieve a catalog entry by its name or alias.

        :param name_or_alias: The name or alias of the field to retrieve.

        :raises: AttributeError if the name or alias is not recognized.

        :returns: The value of the field associated with the name or alias.
        """
        if name_or_alias in self.model_fields:
            return self.model_dump()[name_or_alias]
        else:
            try:
                return self.model_dump(by_alias=True)[name_or_alias]
            except KeyError as exc:
                raise AttributeError(
                    f"No attribute found for alias '{name_or_alias}'"
                ) from exc

    @field_validator(
        "root_catalog_hash",
        "root_path_hash",
        "signing_certificate_hash",
        "tag_history_hash",
        "json_metadata_hash",
        "reflog_checksum_hash",
    )
    def validate_hex(cls, value: str):
        """Validate if a string is a hexadecimal string.

        :param value: The string to validate.

        :raises: CVMFSValidationError if the string is not hexadecimal.

        :returns: The original string if it is valid.
        """
        if not re.fullmatch(r"[0-9a-fA-F]*", value):
            raise ValueError(f"{value} is not a valid hex string")

        return value
