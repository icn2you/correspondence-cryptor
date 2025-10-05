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
- Added encoding unit tests (15 total passing tests).
- Added round-trip encryption/decryption validation to the unit test suite.
- Added `.envrc` support for automatic virtualenv activation.
- Enhanced project with `Makefile`, `pytest.ini`, and `pytest-watch` integration.
- Split development dependencies into `requirements-dev.txt`.

### 🧹 Changed
- Refactored offset normalization logic into `shift()` function for consolidated handling.
