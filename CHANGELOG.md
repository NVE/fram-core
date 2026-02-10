# Change Log

## [0.1.2] - 2026-02-10
- Removed `assert` in `framcore.queries` that is too strict and should be added somewhere else.

## [0.1.1] - 2026-02-05

### Fixed
- Internal function `_get_level_value_from_timevector` in `framcore.queries` module returns incorrect result when the reference period of the input time vector is different from the reference period of the target time index.
 
## [0.1.0] - 2025-12-12
 
 
### Added
- Option to force Julia installation in JuliaModel
- Unit tests
- Improved docstrings
 
### Changed
-
-
 
### Fixed
- Minor fixes and cleanup in code