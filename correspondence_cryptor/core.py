#!/usr/bin/env python3
"""
correspondence-cryptor: Caesar cipher demo

Demonstrates basic string manipulation in Python, utilizing a Caesar Cipher.
"""

import json
import string
from importlib import resources
from textwrap import dedent
from typing import Final


# --- Constants ---
ALPHABET: Final = string.ascii_uppercase
FILEPATH: Final = "correspondence_cryptor.resources"


# --- Functions ---
def decode_caesar_cipher(msg: str, offset: int) -> str:
    """Decode a Caesar-ciphered message by shifting letters to the right by `offset`."""
    return "".join(shift(c, offset) for c in msg)


def encode_caesar_cipher(msg: str, offset: int) -> str:
    """Encode a Caesar-ciphered message by shifting letters to the left by `offset`."""
    return "".join(shift(c, -offset) for c in msg)


def read_received_messages(filename: str) -> list[dict]:
    """Read received messages from `filename` if it exists; otherwise, return an empty list."""
    try:
        with resources.files(FILEPATH).joinpath(filename).open() as f:
            data = json.load(f)
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        return []
    except ValueError as e:
        print(f"JSON decoding error: {e}")
        return []

    # Normalize shape: dict → list with explicit id field
    if isinstance(data, dict):
        data = [{"id": k, **v} for k, v in data.items()]
    elif not isinstance(data, list):
        raise TypeError("Expected dict or list of messages")

    return data


def shift(c: str, offset: int) -> str:
    """Shift a single character by `offset`, preserving case; non-letters pass through."""
    if not c.isalpha():
        return c
    # Normalize offset once so negatives or big numbers still work
    offset = offset % 26
    idx = (ALPHABET.find(c.upper()) + offset) % 26
    shifted = ALPHABET[idx]
    return shifted.lower() if c.islower() else shifted


def main() -> None:
    encoded_msg = dedent(
        """\
        xuo jxuhu! jxyi yi qd unqcfbu ev q squiqh syfxuh. 
        muhu oek qrbu je tusetu yj? y xefu ie!
        iudt cu q cuiiqwu rqsa myjx jxu iqcu evviuj!
        """
    )
    print(decode_caesar_cipher(encoded_msg, 10))
