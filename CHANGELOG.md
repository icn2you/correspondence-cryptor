# Changelog

All notable changes to this project will be documented in this file.  
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**Legend:**  
✨ = Feature | 🐛 = Bug Fix | 📚 = Docs | 🧪 = Tests | 🧹 = Refactor | ⚙️ = Tooling

## [0.1.0] - 2025-10-03
> 🎉 The first public release of *correspondence-cryptor*, introducing Caesar cipher decoding and a foundational codebase.

### 🚀 Initial Release
- Implemented basic Caesar cipher decoding functionality.
- Added `shift()` function for letter shifting with case preservation.
- Introduced foundational unit tests and initial project scaffolding.

## [0.2.0] - 2025-10-04
> ✨ Added Caesar cipher encoding, expanded tests, and improved developer tooling.

### ✨ Added
- Added `encode_caesar_cipher()` function for Caesar cipher encoding.
- Improved test coverage for encoding functionality.
- Added round-trip encryption/decryption validation to the unit test suite.
- Added `.envrc` support for automatic virtualenv activation.
- Enhanced project with `Makefile`, `pytest.ini`, and `pytest-watch` integration.
- Split development dependencies into `requirements-dev.txt`.

### 🧹 Changed
- Refactored offset normalization logic into `shift()` function for consolidated handling.

## [0.3.0] - 2025-10-05
> ✨ Added message loader with data normalization and robust tests.

### ✨ Added
- Implemented `read_received_messages()` function to load external JSON data and normalize it into a list of message objects.
- Improved test coverage for loading functionality, including the handling of a missing data file.

## [0.4.0] - 2025-10-06
> ✨ Added typed JSON parsing, decode guard, and expanded schema support.

### ✨ Added
- Defined `Meta` and `Message` `TypedDict` schemas for structured message metadata and payloads.
- Implemented parsing and normalization of external JSON into strongly typed message objects with UTF-8 decoding and improved error handling.
- Added `decode_if_able()` function to conditionally decode Caesar-ciphered messages based on metadata and offset validation.
- Introduced cipher validation with case-insensitive matching for `"caesar"`.
- Expanded package exports in `__init__.py` to include new types, constants, and helper functions.

### 🧹 Changed
- Updated `shift()` function to handle ASCII-only input, normalize offsets, and preserve case consistently.
- Refined decode logic to reject unsupported ciphers and provide helpful error messages when offsets are missing.
- Updated sample `recd_msgs.json` to match the new schema, including the addition of a valid offset for decoding.

## [0.5.0] - 2025-10-09
> 🔓 Added brute-force key recovery with χ² + ETAOIN tie-break.

### ✨ Added
- Implemented `brute_force_offset()` function to guess unknown Caesar offsets by minimizing χ² against expected English letter frequencies.
- Implemented ETAOIN tie-break functionality: when candidates are within 10% of the best χ², choose the one with the highest (E+T+A+O+I+N)/N rate.
- Added `LOW_CONFIDENCE = -1` sentinel when a message has no alphabetic characters (`N == 0`).
- Introduced helper functions `calc_chi_squared()`, `calc_etaoin_rate()`, and `calc_observed_frequencies()` that use `Decimal` for precision.
- Introduced initial `mypy.ini` configuration for strict static type checking.
- Enhanced module-level docstring with examples, type hints, and portfolio context.

### 🧹 Changed
- Enhanced CLI flow such that it brute-forces the key when an encrypted message has an unknown offset and updates `meta["offset"]` once found.
- Strengthened type hints and container annotations; ensured Decimal-aware summations and full MyPy compliance.
- Updated public exports in `__init__.py` (constants, types, and new API).

### ✅ Tests
- Added and expanded test coverage for brute-force recovery, low-confidence behavior, and `decode_if_able()` function.
- Utilized comprehensive quality belt, including Black, Ruff, MyPy, and Pytest; source code passed all tests.

## [0.6.0] - 2025-10-11
> ✨ Added heuristics + blended tie-break (BREAKING: `decode_if_able`→`try_decode`; `etaoin_rate`→float)

### ✨ Added
- Added vowel-ratio heuristic (Gaussian μ≈0.41, σ≈0.06).
- Added keyword-hit heuristic (saturation + diversity bonus).
- Implemented blended tie-break (ETAOIN 0.40, vowel 0.30, keywords 0.30).
- Added verbose per-key diagnostics and top-3 results with `return_all=True`.
- Implemented `DecryptionResult` dataclass for top-N reporting.
- Introduced `clamp_01()` helper function and internal `_blend_scores()` utility.

### 🧹 Changed
- Enhanced tie-break functionality to use a blended heuristic when χ² candidates are within 10%.
- Refactored `compute_etaoin_rate()` function to return a `float` in [0,1] (previously `Decimal`).
- Renamed `decode_if_able()` function to `try_decode()` (public API and exports).
- Moved coverage configuration to `pyproject.toml`; excluded CLI/demo from coverage; marked defensive branches.

### 🧪 Tests
- Added unit tests for vowel ratio, keyword hits, blended tie-break, verbose/`return_all=True`, and `log_debug()` function.
- Enabled doctests; achieved overall test coverage of ~94% on Python 3.13.

### ⚠️ Breaking
- Renamed `decode_if_able()` function → `try_decode()` (updated imports and callers).
- Changed `compute_etaoin_rate()` return type to `float`.
