"""
test_core.py
============
unit tests for correspondence_cryptor.core

Covers:
- χ² calc; letter frequencies; encode/decode roundtrips
- Heuristics: ETAOIN (float), vowel-ratio score, keyword hits, clamp_01
- Brute force: finds known shifts; N==0 policy
- Tie-break: blended heuristic (ETAOIN + vowel + keywords)

Version: 0.6.0 (2025-10-11)
How to run: `python -m unittest -v` or `pytest -q`
"""

import contextlib
import io
import unittest
from decimal import Decimal

from correspondence_cryptor import (
    decode_caesar_cipher,
    encode_caesar_cipher,
    read_received_messages,
    brute_force_offset,
    try_decode,
)

from correspondence_cryptor.core import (
    DecryptionResult,
    CERTAINTY,
    calc_chi_squared,
    clamp_01,
    compute_etaoin_rate,
    compute_letter_frequencies,
    compute_keyword_hits,
    compute_vowel_ratio,
    compute_evidence,
    break_tie_between_candidates,
    shift,
    log_debug,
)


class TestChiSquared(unittest.TestCase):
    def test_zero_N_returns_zero(self) -> None:
        self.assertEqual(calc_chi_squared({}, Decimal("0")), Decimal("0"))

    def test_observed_total_mismatch_raises(self) -> None:
        with self.assertRaises(ValueError):
            calc_chi_squared({"A": Decimal("3")}, Decimal("2"))


class TestClamp01(unittest.TestCase):
    def test_clamps_below_zero(self) -> None:
        self.assertEqual(clamp_01(-1.5), 0.0)

    def test_clamps_above_one(self) -> None:
        self.assertEqual(clamp_01(1.5), 1.0)

    def test_passes_through_in_range(self) -> None:
        self.assertEqual(clamp_01(0.42), 0.42)


class TestEtaoinRate(unittest.TestCase):
    def test_etaoin_zero_when_N_zero(self) -> None:
        self.assertEqual(compute_etaoin_rate({}, Decimal("0")), Decimal("0"))

    def test_etaoin_basic(self) -> None:
        rate = compute_etaoin_rate(
            {"E": Decimal("3"), "T": Decimal("2")}, Decimal("10")
        )
        self.assertEqual(rate, Decimal("0.500000"))  # (3+2)/10, quantized to 6dp


class TestKeywordHits(unittest.TestCase):
    def test_zero_hits(self) -> None:
        tokens = ["xyz", "foo", "bar"]
        self.assertEqual(compute_keyword_hits(tokens), 0.0)

    def test_frequency_and_diversity(self) -> None:
        # 5 hits (distinct >= 5) → saturation + bonus
        tokens = ["the", "and", "of", "to", "in"]
        score = compute_keyword_hits(tokens)
        # 1 - exp(-5/4) + 0.05 ≈ 0.763495 → rounded 6dp
        self.assertAlmostEqual(score, 0.763495, places=6)

    def test_repeated_hits_increase_score(self) -> None:
        # frequency should matter (not just set membership)
        base = compute_keyword_hits(["the"])
        more = compute_keyword_hits(["the", "the", "the", "and"])
        self.assertGreater(more, base)


class TestLetterFrequencies(unittest.TestCase):
    def test_empty_and_whitespace(self) -> None:
        self.assertEqual(compute_letter_frequencies(""), {})
        self.assertEqual(compute_letter_frequencies("   \n\t"), {})

    def test_case_insensitive_counts(self) -> None:
        freqs = compute_letter_frequencies("AaBbZz!!")
        self.assertEqual(freqs["A"], Decimal("2"))
        self.assertEqual(freqs["B"], Decimal("2"))
        self.assertEqual(freqs["Z"], Decimal("2"))
        # non-mentioned letters should be zero
        self.assertEqual(freqs["C"], Decimal("0"))


class TestVowelRatio(unittest.TestCase):
    def test_center_ratio_scores_near_one(self) -> None:
        # N=100, vowels=41 → ratio exactly 0.41 → exp(0) = 1.0
        vowels = {
            "A": Decimal("20"),
            "E": Decimal("21"),
            "I": Decimal("0"),
            "O": Decimal("0"),
            "U": Decimal("0"),
        }
        score = compute_vowel_ratio(vowels, Decimal("100"))
        self.assertEqual(score, 1.0)

    def test_far_from_center_scores_small(self) -> None:
        # ratio 0.20 (far from 0.41) should be very small
        vowels = {"A": Decimal("10"), "E": Decimal("10")}
        score = compute_vowel_ratio(vowels, Decimal("100"))
        self.assertLess(score, 0.01)


class TestComputeEvidence(unittest.TestCase):
    def test_evidence_edges(self) -> None:
        self.assertGreater(compute_evidence(1.0), 0.9)
        self.assertLess(compute_evidence(-1.0), 0.1)


class TestTieBreakBlend(unittest.TestCase):
    def test_composite_prefers_higher_blend(self) -> None:
        # candidates: (key, chi2, etaoin, vowel_score, keyword_score)
        # same chi2 → tie-break relies on blended heuristic
        cand1 = (3, Decimal("10.0"), 0.60, 0.90, 0.20)  # strong vowel
        cand2 = (7, Decimal("10.0"), 0.70, 0.60, 0.40)  # stronger eta+kw
        winner = break_tie_between_candidates([cand1, cand2])
        self.assertEqual(winner, 7)


class TestCorrespondenceCryptorDecode(unittest.TestCase):
    """ABCDEFGHIJKLMNOPQRSTUVWXYZ"""

    # decoding functionality tests
    def test_basic_decode(self) -> None:
        self.assertEqual(decode_caesar_cipher("ebiil", 3), "hello")

    def test_preserves_case(self) -> None:
        self.assertEqual(decode_caesar_cipher("Ebiil", 3), "Hello")

    def test_non_letters_passthrough(self) -> None:
        self.assertEqual(decode_caesar_cipher("ebiil, tbii!", 3), "hello, well!")

    def test_large_and_negative_offsets(self) -> None:
        self.assertEqual(decode_caesar_cipher("ebiil", 29), "hello")  # 29 == 3 mod 26
        self.assertEqual(decode_caesar_cipher("ebiil", -23), "hello")  # -23 == 3 mod 26

    def test_empty_input(self) -> None:
        self.assertEqual(decode_caesar_cipher("", 10), "")

    def test_shift_unit(self) -> None:
        # A simple boundary check using ALPHABET
        self.assertEqual(shift("Z", 2), "B")
        self.assertEqual(shift("z", 2), "b")
        self.assertEqual(shift("!", 5), "!")


class TestCorrespondenceCryptorEncode(unittest.TestCase):
    """ABCDEFGHIJKLMNOPQRSTUVWXYZ"""

    # encoding functionality tests
    def test_basic_encode(self) -> None:
        self.assertEqual(encode_caesar_cipher("hello", 3), "ebiil")

    def test_preserves_case(self) -> None:
        self.assertEqual(encode_caesar_cipher("Hello", 3), "Ebiil")

    def test_non_letters_passthrough(self) -> None:
        self.assertEqual(encode_caesar_cipher("hello, well!", 3), "ebiil, tbii!")

    def test_large_offset_normalization(self) -> None:
        # 29 mod 26 == 3 → left shift by 3
        self.assertEqual(encode_caesar_cipher("hello", 29), "ebiil")

    def test_negative_offset_supported(self) -> None:
        # -23 == 3 mod 26 (and encode uses -offset under the hood)
        self.assertEqual(encode_caesar_cipher("hello", -23), "ebiil")

    def test_empty_input(self) -> None:
        self.assertEqual(encode_caesar_cipher("", 7), "")

    def test_wrap_edges_mixed_case(self) -> None:
        self.assertEqual(encode_caesar_cipher("ZzAa", 1), "YyZz")


class TestRoundTrip(unittest.TestCase):
    def test_round_trip(self) -> None:
        msg = "Hello, World!"
        for k in (0, 1, 5, 13, 25, 52, -101):
            with self.subTest(k=k):
                self.assertEqual(
                    decode_caesar_cipher(encode_caesar_cipher(msg, k), k),
                    msg,
                )


class TestWrapCases(unittest.TestCase):
    def test_wrap_pairs(self) -> None:
        cases = [("ZzAa", 1, "YyZz"), ("AaZz", 2, "YyXx")]
        for msg, k, expected in cases:
            with self.subTest(k=k, msg=msg):
                self.assertEqual(encode_caesar_cipher(msg, k), expected)


class TestMessageLoading(unittest.TestCase):
    def test_load_returns_list_of_dicts(self) -> None:
        msgs = read_received_messages("recd_msgs.json")
        self.assertIsInstance(msgs, list)
        self.assertTrue(all(isinstance(m, dict) for m in msgs))

    def test_load_returns_empty_list_for_missing_file(self) -> None:
        msgs = read_received_messages("non_existent.json")
        self.assertEqual(msgs, [])


class TestBruteForce(unittest.TestCase):
    def test_finds_known_shift(self) -> None:
        # message with punctuation/case to ensure passthrough is okay
        plaintext = "Meet at Dawn, bring 3 torches!"
        for k in (0, 1, 5, 13, 25):
            with self.subTest(k=k):
                cipher = encode_caesar_cipher(plaintext, k)
                guessed = brute_force_offset(cipher)
                self.assertIsInstance(guessed, int)
                self.assertGreaterEqual(guessed, 0)
                self.assertLessEqual(guessed, 25)
                self.assertEqual(guessed, k)
                self.assertEqual(decode_caesar_cipher(cipher, guessed), plaintext)

    def test_no_letters_low_confidence_default(self) -> None:
        cipher = "12345!!!   --  "
        guessed = brute_force_offset(cipher)
        self.assertEqual(guessed, CERTAINTY.low)  # current policy: return 0 on N==0


class TestVerboseAndReturnAll(unittest.TestCase):
    def test_bruteforce_return_all_and_verbose(self) -> None:
        """When return_all=True, we expect per-candidate lines but no final summary line."""
        msg = "The quick brown fox jumps over the lazy dog."
        for k in (0, 7, 13):
            with self.subTest(k=k):
                cipher = encode_caesar_cipher(msg, k)
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    results = brute_force_offset(cipher, return_all=True, verbose=True)
                out = buf.getvalue()
                # per-candidate lines exist
                self.assertIn("[k=00]", out)
                # summary line is NOT printed in the return_all=True path
                self.assertNotIn("[DEBUG] best=", out)
                # and we get the top-3 results
                self.assertIsInstance(results, list)
                self.assertEqual(len(results), 3)
                self.assertTrue(all(isinstance(r, DecryptionResult) for r in results))

    def test_bruteforce_verbose_summary_when_not_return_all(self) -> None:
        """When return_all=False, the summary line should be printed."""
        msg = "The quick brown fox jumps over the lazy dog."
        cipher = encode_caesar_cipher(msg, 7)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            _ = brute_force_offset(cipher, verbose=True)  # default return_all=False
        out = buf.getvalue()
        self.assertIn("[DEBUG] best=", out)

    def test_log_debug_prints(self) -> None:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            log_debug("hello debug")
        self.assertIn("hello debug", buf.getvalue())


class TestThreeWayTieBreak(unittest.TestCase):
    def test_three_candidate_blended_tie(self) -> None:
        # Construct three candidates with same chi2 → blended heuristic should decide.
        # (key, chi2, etaoin, vowel, keyword)
        chi = Decimal("10.0")
        c1 = (3, chi, 0.60, 0.80, 0.20)  # good vowel
        c2 = (7, chi, 0.72, 0.60, 0.40)  # strong eta+kw
        c3 = (9, chi, 0.65, 0.70, 0.30)  # middling
        winner = break_tie_between_candidates([c1, c2, c3])
        # With weights 0.40/0.30/0.30, c2 should win.
        self.assertEqual(winner, 7)


class TestTryDecode(unittest.TestCase):
    def test_plaintext_passthrough_when_not_encoded(self) -> None:
        meta = {"encoded": False, "offset": None, "cipher": "Caesar"}
        self.assertEqual(try_decode("Hello, World!", meta), "Hello, World!")

    def test_decodes_when_encoded_and_int_offset(self) -> None:
        meta = {"encoded": True, "offset": 3, "cipher": "caesar"}
        self.assertEqual(try_decode("Ebiil, Tloia!", meta), "Hello, World!")

    def test_does_not_decode_when_offset_unknown(self) -> None:
        meta = {"encoded": True, "offset": None, "cipher": "caesar"}
        out = try_decode("Ebiil, Tloia!", meta)
        self.assertIn("Unable to decode", out)

    def test_rejects_unsupported_cipher(self) -> None:
        meta = {"encoded": True, "offset": 3, "cipher": "vigenere"}
        out = try_decode("Ebiil, Tloia!", meta)
        self.assertIn("unsupported cipher", out)

    def test_offset_bool_is_not_treated_as_int(self) -> None:
        # bool is a subclass of int; we must *not* accept it
        meta = {"encoded": True, "offset": True, "cipher": "caesar"}
        out = try_decode("Ebiil, Tloia!", meta)
        self.assertIn("Unable to decode", out)

    def test_cipher_case_insensitive(self) -> None:
        meta = {"encoded": True, "offset": 3, "cipher": "CaEsAr"}
        self.assertEqual(try_decode("Ebiil", meta), "Hello")


if __name__ == "__main__":
    unittest.main()
