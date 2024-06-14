"""Test the pydantic models in cvmfsscraper/models.py."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Union
from unittest import TestCase

from pydantic import ValidationError as PydanticValidationError

from cvmfsscraper.exceptions import CVMFSValidationError
from cvmfsscraper.http_get_models import (
    CVMFSBaseModel,
    GetCVMFSPublished,
    GetCVMFSRepositoriesJSON,
    GetCVMFSStatusJSON,
    GetGeoAPI,
)
from cvmfsscraper.tools import GEOAPI_SERVERS


def get_contents(server: str, file: str, repo: str = "data") -> Union[str, bytes]:
    """Read and return the content of a specified file.

    This function reads the content of a specified file from a
    test data directory and returns it. Depending on the file, it returns
    either bytes or a string.

    :param server: The server where the data resides.
    :param file: The name of the file to read.
    :param repo: The repository where the data resides. Default is "data".

    :raises: FileNotFoundError: if the data file is not found.

    :returns: Content of the file as either bytes or string.
    """
    geoapi_str = ",".join(GEOAPI_SERVERS)

    # Lookup table for filenames and their paths. Binary read flag is optional.
    lookup: Dict[str, Dict[str, str]] = {
        "repositories.json": {
            "path": f"data/{server}/cvmfs/info/v1/repositories.json",
            "json": True,
        },
        ".cvmfs_status.json": {
            "path": f"data/{server}/cvmfs/{repo}/.cvmfs_status.json",
            "json": True,
        },
        "geoapi": {
            "path": f"data/stratum1-no.tld/cvmfs/data/api/v1.0/geo/x/{geoapi_str}",
        },
        ".cvmfspublished": {
            "path": f"data/{server}/cvmfs/{repo}/.cvmfspublished",
            "binary": True,
        },
    }

    # Get the absolute path to the directory containing this script
    current_script_dir = os.path.dirname(os.path.abspath(__file__))

    # Build the path to the data file using the lookup table
    datafile = os.path.join(current_script_dir, lookup[file]["path"])

    # Determine the read mode based on the binary flag (default to text mode)
    mode = "rb" if lookup[file].get("binary", False) else "r"

    # Read the data file based on its mode
    with open(datafile, mode) as f:
        if lookup[file].get("json", False):
            return json.loads(f.read())
        return f.read()


class BaseCVMFSModelTestCase(TestCase):
    """Base model for testing CVMFS models."""

    def verify_date_field(
        self, cls: type[CVMFSBaseModel], input_data: Dict[str, Any], field: str
    ) -> None:
        """Verify that a given field in the dataset is validated as a CVMFS date."""
        data = deepcopy(input_data)

        data[field] = "foo"
        with self.assertRaises(PydanticValidationError):
            cls(**data)

        data[field] = "Mon Jun 14 14:00:00 NOTATZ 2021"
        with self.assertRaises(PydanticValidationError):
            cls(**data)

        data[field] = "Mon Jun 14 25:00:00 UTC 2021"
        with self.assertRaises(PydanticValidationError):
            cls(**data)

        if field == "T":
            data[field] = 1694299917
            cls(**data)
        else:
            data[field] = "Mon Jun 14 14:00:00 UTC 2021"
            cls(**data)

    def verify_str_field(
        self,
        cls: type[CVMFSBaseModel],
        input_data: Dict[str, Any],
        field: str,
        min_length: int = 0,
        max_length: int = 0,
        is_hex: bool = False,
    ) -> None:
        """Verify that a given field in the dataset is validated as a string."""
        data = deepcopy(input_data)

        data[field] = 1
        with self.assertRaises(PydanticValidationError):
            cls(**data)

        data[field] = []
        with self.assertRaises(PydanticValidationError):
            cls(**data)

        if min_length:
            data[field] = "a" * (min_length - 1)
            with self.assertRaises(PydanticValidationError):
                cls(**data)

        if max_length:
            data[field] = "a" * (max_length + 1)
            with self.assertRaises(PydanticValidationError):
                cls(**data)

        if is_hex:
            # Substitute the first character with a non-hex character
            data[field] = "g" * (min_length or 5)
            with self.assertRaises(PydanticValidationError):
                cls(**data)

        # Create a string of the correct length (and hex if required)
        data[field] = "a" * (min_length or 5)
        cls(**data)

    def verify_int_field(
        self,
        cls: type[CVMFSBaseModel],
        input_data: Dict[str, Any],
        field: str,
        require_positive: bool = False,
    ) -> None:
        """Verify that a given field in the dataset is validated as an integer."""
        data = deepcopy(input_data)

        data[field] = "foo"
        with self.assertRaises(PydanticValidationError):
            cls(**data)

        data[field] = []
        with self.assertRaises(PydanticValidationError):
            cls(**data)

        if require_positive:
            data[field] = -1
            with self.assertRaises(PydanticValidationError):
                cls(**data)

        data[field] = 1
        cls(**data)


class TestCVMFSPublishedModel(BaseCVMFSModelTestCase):
    """Test creation of CVMFSPublished instances."""

    def setUp(self) -> None:
        """Set up the test case."""
        # Fetch the published file catalog from the test data.
        # We'll use the data repo of the stratum0.
        self.data = get_contents("stratum0.tld", ".cvmfspublished", "data")

        return super().setUp()

    def test_create_cvmfs_published(self) -> None:
        """Test creation of CVMFSPublished instances."""
        # This is the expected data:
        # C7bbb07002bea5370c1e30082b8a955c7de40c21d
        # B19456
        # Rd41d8cd98f00b204e9800998ecf8427e
        # D240
        # S13
        # Gyes
        # Ano
        # Ndata
        # X2f14a4ac9674937f1d335fd9a9bd20f4d06fb49f
        # H738301fed55210e7bf40511c466eb9f93e05e296
        # T1669133684
        # M85e4f386da0d5d77c7f66cf2f58e10951f24b653
        # Y8d2f044f4cb73575373e6ba2fd3438b5679ec99e

        blob = GetCVMFSPublished.parse_blob(self.data)
        obj = GetCVMFSPublished(**blob)

        rch = "7bbb07002bea5370c1e30082b8a955c7de40c21d"

        self.assertEqual(obj.root_cryptographic_hash, rch)
        self.assertEqual(obj.get_catalog_entry("C"), rch)
        self.assertEqual(obj.get_catalog_entry("root_cryptographic_hash"), rch)

        self.assertFalse(obj.alternative_name)
        self.assertFalse(obj.get_catalog_entry("A"))

        self.assertEqual(obj.root_path_hash, "d41d8cd98f00b204e9800998ecf8427e")
        self.assertEqual(obj.get_catalog_entry("R"), "d41d8cd98f00b204e9800998ecf8427e")

        self.assertEqual(obj.root_catalog_ttl, 240)
        self.assertEqual(obj.get_catalog_entry("D"), 240)

        self.assertEqual(obj.revision, 13)
        self.assertEqual(obj.get_catalog_entry("S"), 13)

        self.assertTrue(obj.is_garbage_collectable)
        self.assertTrue(obj.get_catalog_entry("G"))

        self.assertEqual(obj.full_name, "data")
        self.assertEqual(obj.get_catalog_entry("N"), "data")

        sch = "2f14a4ac9674937f1d335fd9a9bd20f4d06fb49f"

        self.assertEqual(obj.signing_certificate_cryptographic_hash, sch)
        self.assertEqual(obj.get_catalog_entry("X"), sch)

        thh = "738301fed55210e7bf40511c466eb9f93e05e296"

        self.assertEqual(obj.tag_history_cryptographic_hash, thh)
        self.assertEqual(obj.get_catalog_entry("H"), thh)

        datetime_obj = datetime.fromtimestamp(1669133684, timezone.utc)
        self.assertEqual(obj.revision_timestamp, datetime_obj)
        self.assertEqual(obj.get_catalog_entry("T"), datetime_obj)

        jmh = "85e4f386da0d5d77c7f66cf2f58e10951f24b653"

        self.assertEqual(obj.metadata_cryptographic_hash, jmh)
        self.assertEqual(obj.get_catalog_entry("M"), jmh)

        refch = "8d2f044f4cb73575373e6ba2fd3438b5679ec99e"

        self.assertEqual(obj.reflog_checksum_cryptographic_hash, refch)
        self.assertEqual(obj.get_catalog_entry("Y"), refch)

        self.assertEqual(obj.get_catalog_entry("B"), 19456)
        self.assertEqual(obj.root_size, 19456)

    def test_create_cvmfs_published_with_missing_data(self) -> None:
        """Test creation of CVMFSPublished instances with missing data."""
        # Remove the first line from the data file
        data = b"\n".join(self.data.split(b"\n")[1:])

        # This does not raise a value error as missing data is not checked until
        # the model is created.
        with self.assertRaises(PydanticValidationError):
            blob = GetCVMFSPublished.parse_blob(data)
            GetCVMFSPublished(**blob)

    def test_create_cvmfs_published_with_invalid_data(self) -> None:
        """Test creation of CVMFSStatus instances with invalid data."""
        # A and G are supposed to be yes/no, try to set them to something else
        broken = b""
        with self.assertRaises(CVMFSValidationError):
            GetCVMFSPublished.parse_blob(broken)

        broken = self.data.replace(b"Ano", b"Efoo")
        with self.assertRaises(CVMFSValidationError):
            GetCVMFSPublished.parse_blob(broken)

        adata = self.data.replace(b"Ano", b"Afoo")
        with self.assertRaises(CVMFSValidationError):
            GetCVMFSPublished.parse_blob(adata)

        gdata = self.data.replace(b"Gyes", b"Gfoo")
        with self.assertRaises(CVMFSValidationError):
            GetCVMFSPublished.parse_blob(gdata)

    def test_cvmfspublished_field_validation(self) -> None:
        """Test that the model validates the fields."""
        parsed_blob = GetCVMFSPublished.parse_blob(self.data)
        cls = GetCVMFSPublished
        self.verify_str_field(cls, parsed_blob, "C", 40, 40, is_hex=True)
        self.verify_str_field(cls, parsed_blob, "R", 32, 32, is_hex=True)
        self.verify_str_field(cls, parsed_blob, "X", 40, 40, is_hex=True)
        self.verify_str_field(cls, parsed_blob, "H", 40, 40, is_hex=True)
        self.verify_str_field(cls, parsed_blob, "M", 40, 40, is_hex=True)
        self.verify_str_field(cls, parsed_blob, "Y", 40, 40, is_hex=True)

        self.verify_int_field(cls, parsed_blob, "S", require_positive=True)
        self.verify_int_field(cls, parsed_blob, "D", require_positive=True)
        self.verify_int_field(cls, parsed_blob, "B", require_positive=True)

        self.verify_date_field(cls, parsed_blob, "T")

    def test_using_invalid_catalog_entry(self) -> None:
        """Test that using invalid catalog entries raises an exception."""
        obj = GetCVMFSPublished(**GetCVMFSPublished.parse_blob(self.data))

        with self.assertRaises(AttributeError):
            obj.get_catalog_entry("foo")

        with self.assertRaises(AttributeError):
            obj.get_catalog_entry("")

        with self.assertRaises(AttributeError):
            obj.get_catalog_entry("E")


class TestGetCVMFSRepositoriesJSON(BaseCVMFSModelTestCase):
    """Test creation of CVMFSRepositoriesJSON instances."""

    def setUp(self) -> None:
        """Set up the test case."""
        # Fetch the status.json file from the test data.
        # We'll use the data repo of the stratum0.
        self.stratum0repos = get_contents("stratum0.tld", "repositories.json")
        self.stratum1replicas = get_contents("stratum1-no.tld", "repositories.json")
        return super().setUp()

    def test_create_get_cvmfs_repositories_json(self) -> None:
        """Test creation of GetCVMFSRepositoriesJSON instances."""
        s0repos = GetCVMFSRepositoriesJSON(**self.stratum0repos)
        s1replicas = GetCVMFSRepositoriesJSON(**self.stratum1replicas)

        self.assertEqual(len(s0repos.repositories), 2)
        self.assertEqual(s0repos.replicas, [])

        if s0repos.repositories:
            self.assertEqual(s0repos.repositories[0].name, "test")
            self.assertEqual(s0repos.repositories[0].url, "/cvmfs/test")

        self.assertEqual(s1replicas.repositories, [])
        self.assertEqual(len(s1replicas.replicas), 2)

        if s1replicas.replicas:
            self.assertEqual(s1replicas.replicas[0].name, "test")
            self.assertEqual(s1replicas.replicas[0].url, "/cvmfs/test")

    def test_field_validation(self) -> None:
        """Test field validation."""
        cls = GetCVMFSRepositoriesJSON
        self.verify_int_field(cls, self.stratum0repos, "schema", require_positive=True)
        self.verify_date_field(cls, self.stratum0repos, "last_geodb_update")
        for field in ["cvmfs_version", "os_id", "os_version_id", "os_pretty_name"]:
            self.verify_str_field(cls, self.stratum0repos, field)

    def test_repositories_and_replicas(self) -> None:
        """Test that we need one of repositories or replicas, but not both."""
        data = deepcopy(self.stratum0repos)

        # Remove repositories, this leaves us with neither as stratum0 has no replicas
        data["repositories"] = []
        with self.assertRaises(PydanticValidationError):
            GetCVMFSRepositoriesJSON(**data)

        s0repos: Dict[str, Any] = deepcopy(self.stratum0repos["repositories"])

        # Add the repositories from stratum0 as both repositories and replicas
        # This should fail validation
        data["repositories"] = deepcopy(s0repos)
        data["replicas"] = deepcopy(s0repos)
        with self.assertRaises(PydanticValidationError):
            GetCVMFSRepositoriesJSON(**data)

        # Remove replicas, this leaves us with repositories
        data["replicas"] = []
        GetCVMFSRepositoriesJSON(**data)


class TestCVMFSStatusJSON(BaseCVMFSModelTestCase):
    """Test the CVMFSStatusJSON model."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.s0data = get_contents("stratum0.tld", ".cvmfs_status.json", "data")
        self.s1data = get_contents("stratum1-no.tld", ".cvmfs_status.json", "data")
        return super().setUp()

    def test_create_cvmfs_status_json(self) -> None:
        """Test creation of CVMFSStatusJSON instances."""
        GetCVMFSStatusJSON(**self.s0data)
        GetCVMFSStatusJSON(**self.s1data)

    def test_status_field_validation(self) -> None:
        """Test field validation."""
        cls = GetCVMFSStatusJSON
        self.verify_date_field(cls, self.s0data, "last_gc")
        self.verify_date_field(cls, self.s1data, "last_snapshot")


class TestCVMFSGeoAPI(BaseCVMFSModelTestCase):
    """Test the CVMFSGeoAPI model."""

    def setUp(self) -> None:
        """Set up the test case."""
        self.geoapi = get_contents("stratum1-no.tld", "geoapi")
        return super().setUp()

    def test_create_cvmfs_geoapi(self) -> None:
        """Test creation of CVMFSGeoAPI instances."""
        host_indices = self.geoapi.split(",")

        obj = GetGeoAPI(host_indices=host_indices, host_names_input=GEOAPI_SERVERS)

        self.assertIsNotNone(obj)
        self.assertEqual(obj.host_indices, [2, 1, 3])
        self.assertEqual(obj.host_names_input, GEOAPI_SERVERS)
        self.assertEqual(
            obj.host_names_ordered(),
            [GEOAPI_SERVERS[1], GEOAPI_SERVERS[0], GEOAPI_SERVERS[2]],
        )

    def test_geoapi_field_validation(self) -> None:
        """Test that the model validates the fields."""
        host_indices = self.geoapi.split(",")
        host_indices[0] = "foo"

        with self.assertRaises(PydanticValidationError):
            GetGeoAPI(host_indices=host_indices, host_names_input=GEOAPI_SERVERS)

        host_indices = self.geoapi.split(",")
        # remove the last element
        host_indices = host_indices[:-1]

        with self.assertRaises(PydanticValidationError):
            GetGeoAPI(host_indices=host_indices, host_names_input=GEOAPI_SERVERS)
