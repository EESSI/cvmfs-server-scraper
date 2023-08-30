# Changelog

## [Unreleased]

### Added

- Support for server metadata from `repositories.json`, available as the dictionary `server.metadata`
- Large scale code refactoring and cleaning, adding typing and docstrings
- Server objects can now be of either CVMFSServer (generic, behaves depending on how self.server_type is set (either 0 or 1)), Stratum0Server (a stratum0 server), or Stratum1Server (a stratum1 server).

### Fixed

- `fetch_errors` did not properly set path or the error / exception.

### Changed

- Migrated from setup.cfg to poetry.
- `scrape` and `scrape_server` are moved from the package `cvmfsserver.main` to `cvmfsserver`
- Importing `scrape` or `scrape_server` from `cvmfsserver.main` will print a warning about deprecation.
- GeoAPI status is now an enum of type GeoAPIStatus, with values `GeoAPIStatus.OK`, `GeoAPIStatus.NOT_FOUND` (no repositories available), `GeoAPIStatus.LOCATION_ERROR` (location could not be determined), and `GeoAPIStatus.NO_RESPONSE` (other error).

### Removed

- Removed support for setting `forced_repositories` on a server as it served no purpose.

## [0.1.0] - 2022-04-05

### Initial release

- Multithreaded scraping information from a set of CVMFS servers
- Uses repositories.json to determine which repositories to scrape
- For repositories, parses `/.cvmfspublished` and `/.cvmfs_status.json`
- Does not support server metadata from `repositories.json`
