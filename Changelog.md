# Changelog

## [Unreleased]

### Added

- Support for server metadata from `repositories.json`, available as the dictionary `server.metadata`
- Large scale code refactoring and cleaning, adding typing and docstrings

### Changed

- `scrape` and `scrape_server` are moved from the package `cvmfsserver.main` to `cvmfsserver`
- Importing `scrape` or `scrape_server` from `cvmfsserver.main` will print a warning about deprecation.

## [0.1.0] - 2022-04-05

### Initial release

- Multithreaded scraping information from a set of CVMFS servers
- Uses repositories.json to determine which repositories to scrape
- For repositories, parses `/.cvmfspublished` and `/.cvmfs_status.json`
- Does not support server metadata from `repositories.json`
