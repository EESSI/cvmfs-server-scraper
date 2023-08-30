"""Test basic functionality of the cvmfsscraper package."""

from unittest import TestCase

from cvmfsscraper.constants import GeoAPIStatus
from cvmfsscraper.repository import Repository
from cvmfsscraper.server import CVMFSServer, Stratum0Server, Stratum1Server


class TestCVMFSServerBasics(TestCase):
    """Test some basics for the server objects."""

    def test_server_str(self) -> None:
        """Test the string representation of a server."""
        server = CVMFSServer("testserver", [], [], scrape_on_init=False)
        self.assertEqual(str(server), "testserver")

    def test_is_down(self) -> None:
        """Test the is_down property of a server."""
        server = CVMFSServer("testserver", [], [], scrape_on_init=False)
        self.assertTrue(server.is_down())
        server._is_down = False
        self.assertFalse(server.is_down())


class TestCVMFSScraperConstants(TestCase):
    """Test constants in the cvmfsscraper package."""

    def test_geoapi_status(self):
        """Test the GeoAPIStatus enum."""
        self.assertEqual(str(GeoAPIStatus.OK), "OK (0)")
        self.assertEqual(str(GeoAPIStatus.LOCATION_ERROR), "LOCATION_ERROR (1)")
        self.assertEqual(str(GeoAPIStatus.NO_RESPONSE), "NO_RESPONSE (2)")
        self.assertEqual(str(GeoAPIStatus.NOT_FOUND), "NOT_FOUND (9)")
        self.assertEqual(str(GeoAPIStatus.NOT_YET_TESTED), "NOT_YET_TESTED (99)")

    def test_attribute_mapping(self):
        """Test the attribute mapping for repositories."""
        server = CVMFSServer("testserver", [], [], scrape_on_init=False)
        repo = Repository(server, "testrepo", "test")

        self.assertEqual(repo.attribute_mapping()["N"], "full_name")


class TestCVMFSScraperBasics(TestCase):
    """Basic testing of the cvmfsscraper package."""

    def test_create_server_instances(self):
        """Test creation of server instances and their results."""
        cs = CVMFSServer("test", ["test"], [], scrape_on_init=False)
        self.assertIsNotNone(cs)
        self.assertEqual(cs.name, "test")
        # Before scraping and without any other information, the server type is unknown
        self.assertEqual(cs.server_type, None)
        self.assertFalse(cs.is_stratum1())
        self.assertFalse(cs.is_stratum0())

        s0 = Stratum0Server("test", ["test"], [], scrape_on_init=False)
        self.assertIsNotNone(s0)
        self.assertEqual(s0.name, "test")
        self.assertEqual(s0.server_type, 0)
        self.assertFalse(s0.is_stratum1())
        self.assertTrue(s0.is_stratum0())

        s1 = Stratum1Server("test", ["test"], [], scrape_on_init=False)
        self.assertIsNotNone(s1)
        self.assertEqual(s1.name, "test")
        self.assertEqual(s1.server_type, 1)
        self.assertTrue(s1.is_stratum1())
        self.assertFalse(s1.is_stratum0())
