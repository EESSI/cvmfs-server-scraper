"""Base testing framework for cvmfsscraper tests."""

import os
import urllib.error
import urllib.request
from typing import Dict, Union
from unittest.mock import Mock
from urllib.error import HTTPError


def validate_and_load(data_dir: str) -> Dict[str, Union[str, bytes]]:
    """Load test data for all hosts in a data directory.

    :param data_dir: Directory containing host data.

    :returns: A dictionary mapping URLs to their corresponding test data.
    """
    url_mapping = {}

    for root, _, files in os.walk(data_dir):
        for file in files:
            filepath = os.path.join(root, file)
            relpath = os.path.relpath(filepath, data_dir)
            url = f"http://{relpath}"

            # Determine read mode based on file extension
            mode = "r" if not filepath.endswith(".cvmfspublished") else "rb"

            with open(filepath, mode) as f:
                data = f.read()

            url_mapping[url] = data
    return url_mapping


# Get the directory containing the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the full path to the data directory
data_dir = os.path.join(script_dir, "data")

# Load the endpoints
ENDPOINTS = validate_and_load(data_dir)

# Add exceptions to URL mapping
ENDPOINTS["http://example.com/timeout"] = urllib.error.URLError("timeout")


def mock_urlopen(
    url: Union[str, urllib.request.Request], timeout: Union[int, float, None] = None
) -> Union[Mock, Exception]:
    """Mock urllib.request.urlopen based on a predefined URL mapping.

    :param url: The URL to fetch.
    :param timeout: The timeout duration (unused in this mock).

    :raises: HTTPError if the URL does not exist in the mapping.
    :raises: Exception if the URL is meant to simulate an exception.

    :returns: Mocked HTTPResponse object with read() method.
    """
    url = url.full_url if isinstance(url, urllib.request.Request) else url

    if url not in ENDPOINTS:
        raise HTTPError(url, 404, "Not Found", {}, None)

    result = ENDPOINTS[url]

    if isinstance(result, Exception):
        raise result

    mock_response = Mock()
    if isinstance(result, str):
        mock_response.read.return_value = result.encode("UTF-8")
    else:
        mock_response.read.return_value = result.strip()

    return mock_response
