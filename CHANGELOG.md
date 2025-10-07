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
