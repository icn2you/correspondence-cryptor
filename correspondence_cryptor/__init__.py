"""
correspondence_cryptor
======================

Educational Caesar-cipher toolkit with encoding/decoding and
brute-force key recovery using χ² and ETAOIN heuristics.

Public API:
- Types: Meta, Message
- Core: encode_caesar_cipher, decode_caesar_cipher, decode_if_able,
        read_received_messages, brute_force_offset
- Constants: ALPHABET, ETAOIN, FILEPATH
"""

from .core import (
    # Constants (public)
    ALPHABET,
    ETAOIN,
    FILEPATH,
    # Types
    Meta,
    Message,
    # Core functions (public)
    decode_caesar_cipher,
    encode_caesar_cipher,
    read_received_messages,
    brute_force_offset,
    try_decode,
)  # noqa: F401

__all__ = [
    # Constants
    "ALPHABET",
    "ETAOIN",
    "FILEPATH",
    # Types
    "Meta",
    "Message",
    # Core
    "decode_caesar_cipher",
    "encode_caesar_cipher",
    "read_received_messages",
    "brute_force_offset",
    "try_decode",
]
