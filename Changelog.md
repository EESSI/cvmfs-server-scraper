# Changelog

## [Unreleased]

## [0.0.4] - 2024-06-15

### Added

- Added support for stratum1 servers to use S3 as a backend. If any server has S3 as a backend, one has to set the `repos` for the scraping to ensure that the repositories in question are scraped. This is due to the fact that the S3 backend does not offer a repository list to clients (or the scraper). Also note that GeoAPI is not supported for S3 backends and will always return `GeoAPIStatus.NO_RESPONSE`.

## [0.0.3] - 2024-01-21

### Added

- Add logging support via `structlog`.
- Updated documentation in README.md.

### Changed

- Allowed `last_gc` for a repo to be optional. Newly created repos may not have this set.
- Migrated project to ruff only (no black/isort)

### Removed

- Removed printing errors to stderr. Migrated to to logging at the level `error`.

## [0.0.2] - 2024-01-20

### Added

- Support for server metadata from `repositories.json`, available as the dictionary `server.metadata`
- Large scale code refactoring and cleaning, adding typing and docstrings
- Endpoint data validation through use of pydantic models
- Server objects can now be of either CVMFSServer (generic, behaves depending on how self.server_type is set (either 0 or 1)), Stratum0Server (a stratum0 server), or Stratum1Server (a stratum1 server).

### Fixed

- `fetch_errors` did not properly set path or the error / exception.
- Fixed github actions (CI) to use pipx to install poetry.

### Changed

- Migrated from setup.cfg to poetry.
- `scrape` and `scrape_server` are moved from the package `cvmfsserver.main` to `cvmfsserver`
- Importing `scrape` or `scrape_server` from `cvmfsserver.main` will print a warning about deprecation.
- GeoAPI status is now an enum of type GeoAPIStatus, with values `GeoAPIStatus.OK`, `GeoAPIStatus.NOT_FOUND` (no repositories available), `GeoAPIStatus.LOCATION_ERROR` (location could not be determined), and `GeoAPIStatus.NO_RESPONSE` (other error).
- Updated a number of dependencies.

### Removed

- Removed support for setting `forced_repositories` on a server as it served no purpose.

## [0.0.1] - 2022-04-05

### Initial release

- Multithreaded scraping information from a set of CVMFS servers
- Uses repositories.json to determine which repositories to scrape
- For repositories, parses `/.cvmfspublished` and `/.cvmfs_status.json`
- Does not support server metadata from `repositories.json`
