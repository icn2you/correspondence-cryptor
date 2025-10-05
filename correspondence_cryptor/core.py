#!/usr/bin/env python3
"""
correspondence-cryptor: Caesar cipher demo

Demonstrates basic string manipulation in Python, utilizing a Caesar Cipher.
"""

import string
from textwrap import dedent
from typing import Final


# --- Constants ---
ALPHABET: Final = string.ascii_uppercase


# --- Functions ---
def decode_caesar_cipher(msg: str, offset: int) -> str:
    """Decode a Caesar-ciphered message by shifting letters to the right by `offset`."""
    return "".join(shift(c, offset) for c in msg)


def encode_caesar_cipher(msg: str, offset: int) -> str:
    """Encode a Caesar-ciphered message by shifting letters to the left by `offset`."""
    return "".join(shift(c, -offset) for c in msg)


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
