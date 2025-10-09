#!/usr/bin/env python3
"""
correspondence_cryptor.core
===========================

A demonstration module implementing Caesar cipher encoding, decoding,
and brute-force cryptanalysis with χ² and ETAOIN-frequency scoring.

This example showcases clean Python design, use of modern typing,
`decimal.Decimal` arithmetic for precision, and structured docstrings.
It is intended for educational use and as a portfolio example of
well-documented, idiomatic Python code.

Author: Christopher B. Zenner
Created: 2025-10-03
License: MIT (for demonstration purposes)
Version: 0.5.0 (2025-10-08)

Key Features
------------
- Encoding/decoding of Caesar cipher text.
- Automatic key recovery via χ² analysis and ETAOIN tie-break.
- Strong type annotations and `TypedDict` schemas for message metadata.
- Demonstrates good engineering practices: constants, helper functions,
  type guards, and pure functional style.

Example
-------
>>> from correspondence_cryptor.core import encode_caesar_cipher, brute_force_offset
>>> ciphertext = encode_caesar_cipher("Hello, World!", 3)
>>> brute_force_offset(ciphertext)
3
>>> decode_caesar_cipher(ciphertext, 3)
'Hello, World!'

Notes
-----
For educational and demonstration purposes only.
Not intended for production cryptography or secure communication.
"""

import heapq
import json
import string
import textwrap
from decimal import Decimal, ROUND_HALF_UP
from importlib import resources
from typing import Any, Final, Mapping, Optional, Sequence, TypedDict, TypeGuard, cast


# --- Constants ---
ALPHABET: Final[str] = string.ascii_uppercase
ETAOIN: Final[tuple[str, ...]] = ("E", "T", "A", "O", "I", "N")
FILEPATH: Final[str] = "correspondence_cryptor.resources"
LOW_CONFIDENCE = -1  # sentinel for messages with no alpha characters
ZERO: Final[Decimal] = Decimal("0")
EXPECTED_RELATIVE_FREQUENCIES: Final[dict[str, Decimal]] = {
    "E": Decimal("12.70"),
    "T": Decimal("9.06"),
    "A": Decimal("8.17"),
    "O": Decimal("7.51"),
    "I": Decimal("6.97"),
    "N": Decimal("6.75"),
    "S": Decimal("6.33"),
    "H": Decimal("6.09"),
    "R": Decimal("5.99"),
    "D": Decimal("4.25"),
    "L": Decimal("4.03"),
    "C": Decimal("2.78"),
    "U": Decimal("2.76"),
    "M": Decimal("2.41"),
    "W": Decimal("2.36"),
    "F": Decimal("2.23"),
    "G": Decimal("2.02"),
    "Y": Decimal("1.97"),
    "P": Decimal("1.93"),
    "B": Decimal("1.49"),
    "V": Decimal("0.98"),
    "K": Decimal("0.77"),
    "J": Decimal("0.15"),
    "X": Decimal("0.15"),
    "Q": Decimal("0.10"),
    "Z": Decimal("0.07"),
}


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
def calc_chi_squared(observed: Mapping[str, Decimal], N: Decimal) -> Decimal:
    """Calculate χ² based on expected and observed frequencies."""
    chi2 = ZERO
    E = EXPECTED_RELATIVE_FREQUENCIES

    if N == 0:
        return ZERO

    if sum(observed.values(), ZERO) != N:
        raise ValueError("Observed total does not equal N")

    # χ2=∑(O−E)²/E
    for ch in ALPHABET:
        upper = ch.upper()
        expected: Decimal = E[upper] / Decimal("100") * Decimal(N)
        observed_count: Decimal = observed.get(upper, ZERO)
        if expected > ZERO:
            chi2 += ((observed_count - expected) ** 2) / expected

    return chi2.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def calc_etaoin_rate(etaoin: Mapping[str, Decimal], N: Decimal) -> Decimal:
    """Calculate ETAOIN rate from individual values specified in etaoin."""
    if N == ZERO:
        return ZERO

    etaoin_rate = sum(etaoin.values()) / N
    return etaoin_rate.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def calc_observed_frequencies(msg: str) -> dict[str, Decimal]:
    """Calculate observed frequencies in msg of all 26 letters."""
    return (
        {ltr: Decimal(msg.upper().count(ltr)) for ltr in ALPHABET}
        if msg.strip()
        else {}
    )


def break_tie_between_candidates(
    candidates: Sequence[tuple[int, Decimal, Decimal]],
) -> int:
    """Break the tie between the top two/three candidates using the highest ETAOIN rate."""
    # Smallest ETAOIN rate wins; return its respective offset
    return max(candidates, key=lambda t: t[2])[0]


def is_int_but_not_bool(x: Any) -> TypeGuard[int]:
    """Check if x is an int and not a boolean value."""
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


# --- io wrapper ---
def read_received_messages(filename: str) -> list[Message]:
    """
    Read messages from package resources; tolerate dict or list inputs, and
    normalize to a list of Message-like dicts.
    """
    try:
        with (
            resources.files(FILEPATH)
            .joinpath(filename)
            .open("r", encoding="utf-8") as f
        ):
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


# --- brute force wrapper ---
def brute_force_offset(msg: str) -> int:
    """
    Brute-force the Caesar shift for `msg` by scoring all 26 candidates.

    Strategy:
      1) For each shift k in [0..25], decode and compute:
         - χ² (chi-squared) between observed letter counts and the expected
           English distribution (E table), using Decimal for precision.
         - ETAOIN rate = (E+T+A+O+I+N)/N as a cheap “English-likeness” tie-breaker.
      2) Pick the smallest χ². If runners-up are within 10% of the best χ²,
         break ties by choosing the candidate with the highest ETAOIN rate.

    Returns:
      int: the most likely shift (0..25). Note that 0 is a valid key.

    Notes:
      - If the message contains no alphabetic characters (N == 0), this function
        returns -1 (low confidence). Future versions may surface an explicit
        confidence score or top-N candidates.
    """
    offset = LOW_CONFIDENCE
    scores: dict[int, tuple[Decimal, Decimal]] = {}
    N0 = sum(calc_observed_frequencies(msg).values(), ZERO)

    if N0 == ZERO:
        return offset

    for key in range(26):
        decoded = decode_caesar_cipher(msg, key)
        observed = calc_observed_frequencies(decoded)
        etaoin = {ltr: observed[ltr] for ltr in ETAOIN if ltr in observed}
        N = sum(observed.values(), Decimal("0"))
        scores[key] = (calc_chi_squared(observed, N), calc_etaoin_rate(etaoin, N))

    top_three = heapq.nsmallest(3, scores.items(), key=lambda kv: kv[1][0])
    lowest_three: list[tuple[int, Decimal, Decimal]] = [
        (int(k), vals[0], vals[1]) for (k, vals) in top_three
    ]

    best_k, best_chi2, _ = lowest_three[0]
    _, second_chi2, _ = lowest_three[1]
    _, third_chi2, _ = lowest_three[2]
    threshold: Decimal = best_chi2 * Decimal("0.1")

    if abs(best_chi2 - second_chi2) < threshold:
        if abs(best_chi2 - third_chi2) < threshold:
            offset = break_tie_between_candidates(lowest_three)
        else:
            offset = break_tie_between_candidates(lowest_three[:2])
    else:
        offset = best_k

    return offset


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


# --- CLI Demo ---
def main() -> None:
    messages = read_received_messages("recd_msgs.json")
    print(f"You have {len(messages)} new message{'s' if len(messages)!=1 else ''}.")

    for i, msg in enumerate(messages, start=1):
        meta: Meta = msg["meta"]
        name = meta.get("name") or "Unknown"
        encoded = bool(meta.get("encoded", False))
        offset = meta.get("offset")
        status = "encrypted" if encoded else "not encrypted"
        known_key = True if offset is not None else False
        additional_details = None

        # offset is unknown for an encrypted message
        if status == "encrypted":
            additional_details = (
                f" The key is {'known' if known_key else 'unknown'}.\n> "
            )
            if offset is None:
                additional_details += "Attempting to determine the key ... "
                bruted_key = brute_force_offset(msg["text"])

                if bruted_key >= 0:
                    meta["offset"] = bruted_key
                    known_key = True

                additional_details += (
                    f"The key has{' not ' if not known_key else ' '}been determined. "
                )
            else:
                known_key = True

        body = decode_if_able(msg["text"], meta)
        message = (
            f"> Message {i} is from {name}. "
            f"It is {status}.{additional_details if additional_details is not None else '> '}"
            f"{'The message is as follows:' if known_key else 'Unable to decrypt message.'}\n"
            f"---\n"
            f"{textwrap.fill(body, width=72)}\n"
            f"---\n"
        )
        print(message)
