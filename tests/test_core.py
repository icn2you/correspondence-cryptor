import unittest
from decimal import Decimal

from correspondence_cryptor import (
    decode_caesar_cipher,
    encode_caesar_cipher,
    read_received_messages,
    brute_force_offset,
    decode_if_able,
)

from correspondence_cryptor.core import (
    LOW_CONFIDENCE,
    calc_chi_squared,
    calc_etaoin_rate,
    calc_observed_frequencies,
    shift,
)


class TestChiSquared(unittest.TestCase):
    def test_zero_N_returns_zero(self) -> None:
        self.assertEqual(calc_chi_squared({}, Decimal("0")), Decimal("0"))

    def test_observed_total_mismatch_raises(self) -> None:
        with self.assertRaises(ValueError):
            calc_chi_squared({"A": Decimal("3")}, Decimal("2"))


class TestEtaoinRate(unittest.TestCase):
    def test_etaoin_zero_when_N_zero(self) -> None:
        self.assertEqual(calc_etaoin_rate({}, Decimal("0")), Decimal("0"))

    def test_etaoin_basic(self) -> None:
        rate = calc_etaoin_rate({"E": Decimal("3"), "T": Decimal("2")}, Decimal("10"))
        self.assertEqual(rate, Decimal("0.500000"))  # (3+2)/10, quantized to 6dp


class TestObservedFrequencies(unittest.TestCase):
    def test_empty_and_whitespace(self) -> None:
        self.assertEqual(calc_observed_frequencies(""), {})
        self.assertEqual(calc_observed_frequencies("   \n\t"), {})

    def test_case_insensitive_counts(self) -> None:
        freqs = calc_observed_frequencies("AaBbZz!!")
        self.assertEqual(freqs["A"], Decimal("2"))
        self.assertEqual(freqs["B"], Decimal("2"))
        self.assertEqual(freqs["Z"], Decimal("2"))
        # non-mentioned letters should be zero
        self.assertEqual(freqs["C"], Decimal("0"))


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
        self.assertEqual(guessed, LOW_CONFIDENCE)  # current policy: return 0 on N==0


class TestDecodeIfAble(unittest.TestCase):
    def test_plaintext_passthrough_when_not_encoded(self) -> None:
        meta = {"encoded": False, "offset": None, "cipher": "Caesar"}
        self.assertEqual(decode_if_able("Hello, World!", meta), "Hello, World!")

    def test_decodes_when_encoded_and_int_offset(self) -> None:
        meta = {"encoded": True, "offset": 3, "cipher": "caesar"}
        self.assertEqual(decode_if_able("Ebiil, Tloia!", meta), "Hello, World!")

    def test_does_not_decode_when_offset_unknown(self) -> None:
        meta = {"encoded": True, "offset": None, "cipher": "caesar"}
        out = decode_if_able("Ebiil, Tloia!", meta)
        self.assertIn("Unable to decode", out)

    def test_rejects_unsupported_cipher(self) -> None:
        meta = {"encoded": True, "offset": 3, "cipher": "vigenere"}
        out = decode_if_able("Ebiil, Tloia!", meta)
        self.assertIn("unsupported cipher", out)

    def test_offset_bool_is_not_treated_as_int(self) -> None:
        # bool is a subclass of int; we must *not* accept it
        meta = {"encoded": True, "offset": True, "cipher": "caesar"}
        out = decode_if_able("Ebiil, Tloia!", meta)
        self.assertIn("Unable to decode", out)

    def test_cipher_case_insensitive(self) -> None:
        meta = {"encoded": True, "offset": 3, "cipher": "CaEsAr"}
        self.assertEqual(decode_if_able("Ebiil", meta), "Hello")


if __name__ == "__main__":
    unittest.main()
