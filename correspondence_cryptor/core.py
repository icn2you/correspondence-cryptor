#!/usr/bin/env python3
"""
correspondence-cryptor: Caesar cipher demo

Demonstrates basic string manipulation in Python, utilizing a Caesar Cipher.
"""

import json
import string
from importlib import resources
from typing import Any, Final, Mapping, Optional, TypedDict, TypeGuard, cast


# --- Constants ---
ALPHABET: Final[str] = string.ascii_uppercase
FILEPATH: Final[str] = "correspondence_cryptor.resources"


# --- Typed Schemas ---
class Meta(TypedDict, total=False):
    name: Optional[str]
    email: Optional[str]
    subject: Optional[str]
    encoded: bool
    cipher: str
    offset: Optional[int]


class Message(TypedDict):
    id: str
    text: str
    meta: Meta


# --- Functions ---
# --- helpers ---
def is_int_but_not_bool(x: Any) -> TypeGuard[int]:
    return isinstance(x, int) and not isinstance(x, bool)


def shift(c: str, offset: int) -> str:
    """Shift ASCII letters by `offset`, preserving case; pass everything else through."""
    upper = c.upper()
    if upper not in ALPHABET:
        return c
    # Normalize offset once so negatives or big numbers still work
    k = offset % 26
    idx = (ALPHABET.index(upper) + k) % 26
    ch = ALPHABET[idx]
    return ch.lower() if c.islower() else ch


# --- core transformers ---
def decode_caesar_cipher(msg: str, offset: int) -> str:
    """Decode by shifting letters to the right by `offset`."""
    return "".join(shift(c, offset) for c in msg)


def encode_caesar_cipher(msg: str, offset: int) -> str:
    """Encode by shifting letters to the left by `offset`."""
    return "".join(shift(c, -offset) for c in msg)


# --- decode wrapper (with safety) ---
def decode_if_able(text: str, meta: Mapping[str, Any]) -> str:
    """
    Decode only if meta['encoded'] is True and meta['offset'] is an int (not a bool).
    Otherwise, return the original text or a helpful message.
    """
    if not bool(meta.get("encoded", False)):
        return text  
    # Only handle Caesar cipher
    if (c := meta.get("cipher")) is not None and c.casefold() != "caesar":
        return f"Unable to decode: unsupported cipher {c!r}"
    if is_int_but_not_bool(offset := meta.get("offset")):
        return decode_caesar_cipher(text, offset)

    return "Unable to decode message due to unknown offset."


# --- io wrapper ---
def read_received_messages(filename: str) -> list[Message]:
    """
    Read messages from package resources; tolerate dict or list inputs, and
    normalize to a list of Message-like dicts.
    """
    try:
        with resources.files(FILEPATH).joinpath(filename).open("r", encoding="utf-8") as f:
            data: Any = json.load(f)
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSON decoding error: {e}")
        return []

    if isinstance(data, dict):
        # Promote to list with explicit id
        normalized = [{"id": k, **v} for k, v in data.items()]
        return cast(list[Message], normalized)

    if isinstance(data, list):
        return cast(list[Message], data)

    raise TypeError("Expected dictionary or list of messages")


# --- CLI Demo ---
def main() -> None:
    messages = read_received_messages("recd_msgs.json")
    print(f"You have {len(messages)} new message{'s' if len(messages)!=1 else ''}.")
    
    for i, msg in enumerate(messages, start=1):
        meta: Meta = msg["meta"] 
        name = meta.get("name") or "Unknown"
        encoded = bool(meta.get("encoded", False))
        status = "encrypted" if encoded else "not encrypted"
        body = decode_if_able(msg["text"], meta)
        
        message = (
            f"> Message {i} is from {name}. "
            f"It is {status}:\n"
            f"{body}"
        )
        print(message)
