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
Version: 0.6.0 (2025-10-11)

Key Features
------------
- Encoding/decoding of Caesar cipher text.
- Automatic key recovery via χ² analysis plus heuristic blend
  (ETAOIN rate, vowel-ratio score, keyword-hit score).
- Strong type annotations and `TypedDict` schemas for message metadata.
- Demonstrates good engineering practices: constants, helper functions,
  type guards, and pure functional style.

Example
-------
>>> plaintext = "The quick brown fox jumps over the lazy dog. Caesar rocks!"
>>> ciphertext = encode_caesar_cipher(plaintext, 10)
>>> brute_force_offset(ciphertext)
10
>>> decode_caesar_cipher(ciphertext, 10) == plaintext
True

Notes
-----
- For educational and demonstration purposes only.
- Not intended for production cryptography or secure communication.
- Accuracy of χ² decreases for ciphertexts shorter than ~70 characters
  due to sample-size effects.
"""

import heapq
import json
import math
import re
import string
import textwrap
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from importlib import resources
from typing import (
    Any,
    Final,
    Iterable,
    Literal,
    Mapping,
    Optional,
    Sequence,
    TypedDict,
    TypeGuard,
    cast,
    overload,
)


# --- Data Classes ---
@dataclass
class ConfidenceLevel:
    """Sentinel values for confidence status codes."""

    low: int = -1
    unk: int = -2


@dataclass
class ConfidenceParams:
    """Sigmoid tuning parameters:
    - α (alpha): controls curve steepness (higher = more decisive)
    - μ (mu): midpoint margin where confidence ≈ 0.5
    """

    alpha: float = 12.0
    mu: float = 0.10


@dataclass
class DecryptionResult:
    """Result record for a single brute-force candidate."""

    key: int
    confidence: float
    chi2: Decimal
    etaoin_rate: float
    vowel_ratio: float
    keyword_hits: float


# --- Constants ---
FILEPATH: Final[str] = "correspondence_cryptor.resources"
ALPHABET: Final[str] = string.ascii_uppercase
ETAOIN: Final[tuple[str, ...]] = ("E", "T", "A", "O", "I", "N")
VOWELS: Final[tuple[str, ...]] = ("A", "E", "I", "O", "U")
KEYWORDS: Final[set[str]] = {
    "the",
    "and",
    "of",
    "to",
    "in",
    "is",
    "it",
    "that",
    "for",
    "you",
    "with",
    "on",
    "was",
    "as",
    "I".lower(),  # lowercase for data normalization
    "be",
    "this",
    "are",
}
ZERO: Final[Decimal] = Decimal("0")
CENTER: Final[float] = 0.41  # expected vowel ratio in English
SIGMA: Final[float] = 0.06  # standard deviation for Gaussian
K: Final[float] = 4.0  # saturation factor
BONUS: Final[float] = 0.05  # diversity bonus
CERTAINTY = ConfidenceLevel()
CONFIDENCE = ConfidenceParams()
# accepted letter frequencies in English text, expressed as a percentage
ENGLISH_FREQ_PCTS: Final[dict[str, Decimal]] = {
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

# Confirm English frequency percents table is sane
_total_pct = sum(ENGLISH_FREQ_PCTS.values())
assert abs(_total_pct - Decimal("100.0")) < Decimal(
    "0.5"
), f"ENGLISH_FREQ_PCTS sums to {_total_pct}, expected ≈ 100.0"
del _total_pct

ENGLISH_FREQ_PROPS: Final[dict[str, Decimal]] = {
    letter: (pct / Decimal("100")) for letter, pct in ENGLISH_FREQ_PCTS.items()
}

# Confirm English frequency proportions table is sane
_total_prop = sum(ENGLISH_FREQ_PROPS.values())
assert abs(_total_prop - Decimal("1.0")) < Decimal(
    "0.005"
), f"ENGLISH_FREQ_PROPS sums to {_total_prop}, expected ≈ 1.0"
del _total_prop

# blended-score weights
# tie-break weights for internal use only; not part of public API
# Will promote to dataclass in v0.8.0.
_ETAOIN_WEIGHT: Final[float] = 0.40
_VOWEL_WEIGHT: Final[float] = 0.30
_KEYWORD_WEIGHT: Final[float] = 0.30

# Confirm weights sum to 1.0
_total_weight = _ETAOIN_WEIGHT + _VOWEL_WEIGHT + _KEYWORD_WEIGHT
assert abs(_total_weight - 1.0) < 1e-9


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
    if N == ZERO or not observed:
        return ZERO

    E = ENGLISH_FREQ_PROPS
    chi2: Decimal = ZERO
    factor: Decimal = Decimal("1")
    sum_expected = sum(E.values())

    if sum_expected <= Decimal("1.01"):  # proportions (≈1.0)
        factor = N
    elif Decimal("99.0") <= sum_expected <= Decimal("101.0"):  # percents (≈100)
        factor = N / Decimal("100")
    else:  # pragma: no cover
        raise ValueError(f"Unexpected expected-frequency table scale: {sum_expected}")

    if sum(observed.values(), ZERO) != N:
        raise ValueError("Observed total does not equal N")

    # χ2=∑(O−E)²/E
    for ch in ALPHABET:
        upper = ch.upper()
        expected_count: Decimal = E[upper] * factor
        observed_count: Decimal = observed.get(upper, ZERO)

        if expected_count > ZERO:
            chi2 += ((observed_count - expected_count) ** 2) / expected_count

    return chi2.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)


def _blend_scores(
    etaoin_score: float, vowel_score: float, keyword_score: float
) -> float:
    """Return a weighted composite of ETAOIN, vowel, and keyword heuristics.

    Inputs should already be in [0, 1]. Output is clamped to [0, 1] and rounded to 6 dp.
    Used only for tie-breaking among near-equal χ² candidates.
    """
    e = clamp_01(etaoin_score)
    v = clamp_01(vowel_score)
    k = clamp_01(keyword_score)

    composite = _ETAOIN_WEIGHT * e + _VOWEL_WEIGHT * v + _KEYWORD_WEIGHT * k

    return round(composite, 6)


def clamp_01(x: float) -> float:
    """Clamp x to [0,1]."""
    return max(0.0, min(1.0, x))


def compute_etaoin_rate(etaoin: Mapping[str, Decimal], N: Decimal) -> float:
    """Proportion of ETAOIN letters (E,T,A,O,I,N) among alphabetic letters.

    Returns a float in [0, 1] computed as sum(etaoin)/N, rounded to 6 decimals.
    """
    if N == ZERO:
        return 0.0

    etaoin_rate = float(sum(etaoin.values())) / float(N)
    return round(etaoin_rate, 6)


def compute_keyword_hits(tokens: Iterable[str]) -> float:
    """Heuristic: frequency + diversity of common function words (case-agnostic).

    - tokens: iterable of words (do not pass a set)
    Returns a float in [0, 1].
    """
    hits, distinct = 0, 0
    seen: set[str] = set()

    for t in tokens:
        token = t.lower()
        if token in KEYWORDS:
            hits += 1
            if token not in seen:
                seen.add(token)
                distinct += 1

    if hits == 0:
        return 0.0

    score = 1.0 - math.exp(-hits / K)

    if distinct >= 5:
        score += BONUS

    return round(clamp_01(score), 6)


def compute_letter_frequencies(msg: str) -> dict[str, Decimal]:
    """Calculate observed frequencies in msg of all 26 letters."""
    if not msg.strip():
        return cast(dict[str, Decimal], {})
    return {ltr: Decimal(msg.upper().count(ltr)) for ltr in ALPHABET}


def compute_vowel_ratio(vowels: Mapping[str, Decimal], N: Decimal) -> float:
    """Heuristic score based on the ratio of vowels to letters.

    Computes the vowel share (AEIOU) and maps it through a Gaussian
    centered at ~0.41 (σ≈0.06) to produce a score in [0, 1].
    """
    if N == ZERO:
        return 0.0

    ratio = float(sum(vowels.values())) / float(N)
    score = math.exp(-((ratio - CENTER) ** 2) / (2 * SIGMA**2))
    return round(score, 6)


def compute_evidence(margin: float) -> float:
    """Computes the evidence strength as a sigmoid of the normalized χ² margin.

    Maps small χ² differences to low confidence and large differences to high confidence,
    controlled by α (curve steepness) and μ (midpoint margin).

    Examples
    --------
    >>> round(compute_evidence(0.0), 2)
    0.23
    >>> round(compute_evidence(0.1), 1)
    0.5
    >>> round(compute_evidence(0.2), 2)
    0.77
    """
    return 1.0 / (1.0 + math.exp(-(CONFIDENCE.alpha * (margin - CONFIDENCE.mu))))


def break_tie_between_candidates(
    candidates: Sequence[tuple[int, Decimal, float, float, float]],
) -> int:
    """Break ties among near-equal χ² candidates using a blended heuristic
    (ETAOIN, vowel score, keyword score). Returns the winning key.
    """
    # candidates: (key, chi2, etaoin_score, vowel_score, keyword_score)
    best = max(candidates, key=lambda t: _blend_scores(t[2], t[3], t[4]))
    return best[0]


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
        path = resources.files(FILEPATH).joinpath(filename)
        with path.open("r", encoding="utf-8") as f:
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
@overload
def brute_force_offset(
    msg: str, return_all: Literal[True], verbose: bool = False
) -> list[DecryptionResult]: ...
@overload
def brute_force_offset(
    msg: str, return_all: Literal[False], verbose: bool = False
) -> int: ...
@overload
def brute_force_offset(msg: str, *, verbose: bool = False) -> int: ...
def brute_force_offset(
    msg: str, return_all: bool = False, verbose: bool = False
) -> int | list[DecryptionResult]:
    """
    Brute-force the Caesar shift for `msg` by scoring all 26 candidates.

    Strategy:
      1) For each shift k in [0..25], decode and compute:
         - χ² (chi-squared) between observed letter counts and the expected
           English distribution (E table), using Decimal for precision.
         - ETAOIN rate = (E+T+A+O+I+N)/N as a cheap “English-likeness” tie-breaker.
      2) Pick the smallest χ². If runners-up are within 10% of the best χ²,
         break ties using a blended heuristic (ETAOIN score, vowel score, and keyword score).

    Returns:
      int: the most likely shift (0..25). Note that 0 is a valid key.

    Notes:
      - If the message contains no alphabetic characters (N == 0), this function
        returns -1 (low confidence). Future versions may surface an explicit
        confidence score or top-N candidates.
    """
    offset = CERTAINTY.low
    N0 = sum(compute_letter_frequencies(msg).values(), ZERO)

    if N0 == ZERO:
        return offset

    # score → {key: (χ², ETAOIN rate, vowel ratio, keyword hits)}
    scores: dict[int, tuple[Decimal, float, float, float]] = {}

    for key in range(26):
        decoded = decode_caesar_cipher(msg, key)
        tokenized = re.findall(r"[A-Za-z']+", decoded)
        observed = compute_letter_frequencies(decoded)
        etaoin = {ltr: observed[ltr] for ltr in ETAOIN}
        vowels = {ltr: observed[ltr] for ltr in VOWELS}
        N = sum(observed.values(), Decimal("0"))
        scores[key] = (
            calc_chi_squared(observed, N),
            compute_etaoin_rate(etaoin, N),
            compute_vowel_ratio(vowels, N),
            compute_keyword_hits(tokenized),
        )

        if verbose:
            print(
                f"[k={key:02d}] chi2={scores[key][0]:.6f} eta={scores[key][1]:.3f} "
                f"vow={scores[key][2]:.3f} kw={scores[key][3]:.3f}"
            )

    # Rank top three scores by:
    #   1) χ² ascending
    #   2) ETAOIN descending
    #   3) key ascending
    top3_keys = heapq.nsmallest(
        3, scores, key=lambda k: (scores[k][0], -scores[k][1], k)
    )

    best_k, second_k, third_k = top3_keys
    best_chi2, best_eta, _, _ = scores[best_k]
    second_chi2, _, _, _ = scores[second_k]
    third_chi2, _, _, _ = scores[third_k]
    threshold: Decimal = best_chi2 * Decimal("0.1")

    tiny = Decimal("1e-9")
    margin = float((second_chi2 - best_chi2) / max(second_chi2, tiny))
    evidence = compute_evidence(margin)  # 0..1
    etaoin_norm = best_eta
    confidence = 0.6 * evidence + 0.4 * etaoin_norm

    if abs(best_chi2 - second_chi2) < threshold:
        candidates = [
            (k, scores[k][0], scores[k][1], scores[k][2], scores[k][3])
            for k in top3_keys
        ]
        if abs(best_chi2 - third_chi2) < threshold:
            offset = break_tie_between_candidates(candidates)
        else:
            offset = break_tie_between_candidates(candidates[:2])
    else:
        offset = best_k

    if return_all:
        return [
            DecryptionResult(
                k,  # key
                float(
                    0.6 * compute_evidence(margin) + 0.4 * float(scores[k][1])
                ),  # confidence level
                scores[k][0],  # χ²
                scores[k][1],  # ETAOIN rate
                scores[k][2],  # vowel ratio
                scores[k][3],  # keyword hits
            )
            for k in top3_keys
        ]

    if verbose:
        print(
            f"[DEBUG] best={best_k:02d}, χ²={best_chi2:.4f}, η={best_eta:.4f}, "
            f"margin={margin:.3f}, evidence={evidence:.2f}, confidence={confidence:.2f}"
        )

    return offset


# --- decode wrapper (with safety) ---
def try_decode(text: str, meta: Mapping[str, Any]) -> str:
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


# --- logging wrapper ---
def log_debug(msg: str) -> None:
    """Emit a debug message.

    Thin wrapper around `print()` so the call site stays stable if/when the project
    is switched to the standard `logging` framework (e.g., `logger.debug(msg)`).

    Parameters
    ----------
    msg : str → message to emit at debug level

    Notes
    -----
    Side-effect: writes to stdout.
    """
    print(msg)


# --- CLI Demo ---
def main() -> None:  # pragma: no cover
    """CLI demo: load messages, auto-detect Caesar key if needed, and print decoded output.

    Reads `recd_msgs.json` from package resources and prints a formatted summary
    for each message. If a message is marked encoded with an unknown key, attempts
    to brute-force the Caesar offset and decode it.

    Side-effects
    ------------
    - Prints to stdout.
    - May modify in-memory `meta["offset"]` for messages when a key is recovered.
    """
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
                bruted_key: int = brute_force_offset(msg["text"])

                if bruted_key >= 0:
                    meta["offset"] = bruted_key
                    known_key = True

                additional_details += (
                    f"The key has{' not ' if not known_key else ' '}been determined. "
                )
            else:
                known_key = True

        body = try_decode(msg["text"], meta)
        message = (
            f"> Message {i} is from {name}. "
            f"It is {status}.{additional_details if additional_details is not None else '> '}"
            f"{'The message is as follows:' if known_key else 'Unable to decrypt message.'}\n"
            f"---\n"
            f"{textwrap.fill(body, width=72)}\n"
            f"---\n"
        )
        print(message)
