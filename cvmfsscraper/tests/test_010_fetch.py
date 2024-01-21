"""Test that fetching data works as expected."""

import json
import sys
from unittest import TestCase
from unittest.mock import Mock, patch

from cvmfsscraper import scrape
from cvmfsscraper.constants import GeoAPIStatus
from cvmfsscraper.main import scrape as scrape_deprecated
from cvmfsscraper.main import scrape_server as scrape_server_deprecated
from cvmfsscraper.server import Stratum0Server, Stratum1Server
from cvmfsscraper.tools import fetch, fetch_absolute

from .base import ENDPOINTS, mock_urlopen


class MockedURLLibRequest(TestCase):
    """An abstract class that mocks urllib.request.urlopen."""

    def setUp(self) -> None:
        """Mock urllib.request.urlopen."""
        self.mock_urlopen = patch("urllib.request.urlopen", side_effect=mock_urlopen).start()
        self.addCleanup(patch.stopall)


class TestFetchAPI(MockedURLLibRequest):
    """Test fetching data over (mocked) HTTP."""

    def test_basic_fetching(self) -> None:
        """Test fetching data with fetch."""
        endpoint = "http://stratum1-no.tld/cvmfs/info/v1/repositories.json"

        data = fetch(self, "stratum1-no.tld", "cvmfs/info/v1/repositories.json")
        self.assertEqual(data, ENDPOINTS[endpoint])

        data_slash = fetch(self, "stratum1-no.tld", "/cvmfs/info/v1/repositories.json")
        self.assertEqual(data_slash, ENDPOINTS[endpoint])

        data_abs = fetch_absolute(self, endpoint)
        self.assertEqual(data_abs, ENDPOINTS[endpoint])
        self.assertEqual(data, data_abs)
        self.assertEqual(data_slash, data_abs)

    def test_fetching_with_errors(self) -> None:
        """Test fetching data with fetch."""
        # structlog fails on this specific test for
        # python < 3.10, so skip this test for those versions
        if sys.version_info < (3, 10):  # pragma: no cover
            return

        endpoint = "http://stratum1-no.tld/cvmfs/info/v1/repositories.json.404"
        obj = Mock()
        obj.fetch_errors = []
        data = fetch_absolute(obj, endpoint)
        self.assertEqual(data, None)
        self.assertEqual(obj.fetch_errors[0]["path"], endpoint)
        self.assertEqual(obj.fetch_errors[0]["error"].code, 404)

    def test_fetching_with_timeout(self) -> None:
        """Test fetching data with fetch."""
        endpoint = "http://example.com/timeout"
        obj = Mock()
        obj.fetch_errors = []
        data = fetch_absolute(obj, endpoint)
        self.assertEqual(data, None)
        self.assertEqual(obj.fetch_errors[0]["path"], endpoint)
        self.assertEqual(obj.fetch_errors[0]["error"].reason, "timeout")


class TestModernAPI(MockedURLLibRequest):
    """Test fetching missing or broken endpoints with the new API."""

    def test_fetching_unknown_endpoint(self):
        """Test that fetching an unknown endpoint raises the correct exception."""
        stratum1 = Stratum1Server("stratum1-no.tld", [], [], scrape_on_init=False)

        with self.assertRaises(TypeError):
            stratum1.fetch_endpoint("unknown")


class TestScraping(MockedURLLibRequest):
    """Test scraping data from a server."""

    def test_stratum1_manually_scraping(self) -> None:
        """Test that the server can be manually scraped."""
        stratum1_no = Stratum1Server("stratum1-no.tld", [], [], scrape_on_init=False)

        # Check default values in the server
        self.assertEqual(stratum1_no.name, "stratum1-no.tld")
        self.assertEqual(stratum1_no.geoapi_status, GeoAPIStatus.NOT_YET_TESTED)
        self.assertTrue(stratum1_no.is_stratum1())
        self.assertEqual(len(stratum1_no.repositories), 0)

        stratum1_no.scrape()

        self.assertEqual(len(stratum1_no.repositories), 2)
        self.assertEqual(stratum1_no.geoapi_status, GeoAPIStatus.OK)

    def test_repo_order_and_string_value(self) -> None:
        """Test that a scraping returns the repositories sorted by name."""
        stratum1_no = Stratum1Server("stratum1-no.tld", [], [], scrape_on_init=False)

        stratum1_no.scrape()

        self.assertEqual(len(stratum1_no.repositories), 2)
        self.assertEqual(stratum1_no.repositories[0].name, "data")
        self.assertEqual(stratum1_no.repositories[1].name, "test")

        self.assertEqual(str(stratum1_no.repositories[0]), "data")
        self.assertEqual(str(stratum1_no.repositories[1]), "test")

    def test_scraping_stratum0(self) -> None:
        """Test that a stratum0 server can be scraped."""
        stratum0 = Stratum0Server("stratum0.tld", [], [], scrape_on_init=False)
        self.assertTrue(stratum0.is_stratum0())

        stratum0.scrape()

        self.assertTrue(stratum0.is_stratum0())
        self.assertEqual(len(stratum0.repositories), 2)
        self.assertEqual(stratum0.repositories[0].name, "data")
        self.assertEqual(stratum0.repositories[1].name, "test")

        self.assertEqual(stratum0.geoapi_status, GeoAPIStatus.OK)

    def test_server_show(self) -> None:
        """Test the show method of a server."""
        server = Stratum1Server("stratum1-no.tld", [], [], scrape_on_init=False)
        empty_data = "Server: stratum1-no.tld\nMetadata:\nRepositories: 0\n"
        self.assertEqual(server.show(), empty_data)

        server.scrape()
        scraped_data = """Server: stratum1-no.tld
Metadata:
  - schema_version: 1
  - last_geodb_update: 2023-08-29 10:00:03
  - cvmfs_version: 2.10.0-1
  - os_id: rhel
  - os_version_id: 8.4
  - os_pretty_name: Red Hat Enterprise Linux 8.4 (Ootpa)
Repositories: 2
  - data
  - test
"""
        self.assertEqual(server.show(), scraped_data)


class TestRepositoryScraping(MockedURLLibRequest):
    """Test that repositories are scraped properly."""

    def test_that_default_repos_are_scraped(self) -> None:
        """Test that we get the same repos that are listed in repositories.json."""
        repodata = json.loads(
            fetch(
                self,
                "stratum1-no.tld",
                "cvmfs/info/v1/repositories.json",
            )
        )

        stratum1_no = Stratum1Server("stratum1-no.tld", [], [])

        # Assert that the server has the same number of repositories as the
        # number of entries in the repositories.json file. This is a stratum1 server
        # so they are replicas.
        self.assertEqual(len(stratum1_no.repositories), len(repodata["replicas"]))

        # Assert that all the names in repodata["replicas"] are in stratum1_no.repositories
        # stratum1_no.repositories is a list of Repository objects, so we need to
        # check the name attribute of each object.
        for repo in repodata["replicas"]:
            self.assertIn(repo["name"], [r.name for r in stratum1_no.repositories])

    def test_ignore_repos(self) -> None:
        """Test that using ignore_repos works as expected."""
        stratum1_no = Stratum1Server(
            "stratum1-no.tld",
            [],
            ignore_repos=["test"],
        )

        self.assertEqual(len(stratum1_no.repositories), 1)

        for repo in stratum1_no.repositories:
            self.assertNotEqual(repo.name, "test")

    def test_attribute_lookups(self) -> None:
        """Test that attributes from .cvmfspublished are as expected."""
        stratum1_no = Stratum1Server("stratum1-no.tld", [], [])
        datarepo = stratum1_no.repositories[0]
        self.assertEqual(datarepo.attribute("N"), "data")
        self.assertEqual(datarepo.attribute("full_name"), "data")
        self.assertEqual(datarepo.attributes()["N"], "data")


class TestThreadedFetching(MockedURLLibRequest):
    """Test fetching data using threaded interface."""

    def test_treaded_scraping(self) -> None:
        """Test that threaded scraping works as expected."""
        servers = scrape(
            stratum0_servers=[
                "stratum0.tld",
            ],
            stratum1_servers=[
                "stratum1-no.tld",
                "stratum1-au.tld",
                "stratum1-us-east-unsynced.tld",
            ],
            repos=[],
            ignore_repos=[],
        )

        self.assertEqual(len(servers), 4)


class TestDeprecatedScraping(MockedURLLibRequest):
    """Test deprecated scraping data from a server."""

    def test_treaded_scraping_deprecated(self) -> None:
        """Test that threaded scraping works as expected."""
        servers = scrape_deprecated(
            stratum0_servers=[
                "stratum0.tld",
            ],
            stratum1_servers=[
                "stratum1-no.tld",
                "stratum1-au.tld",
                "stratum1-us-east-unsynced.tld",
            ],
            repos=[],
            ignore_repos=[],
        )

        self.assertEqual(len(servers), 4)

    def test_single_scraping_deprecated(self) -> None:
        """Test that threaded scraping works as expected."""
        server = scrape_server_deprecated(
            "stratum0.tld",
            repos=[],
            ignore_repos=[],
            is_stratum0=True,
        )

        self.assertIsInstance(server, Stratum0Server)
