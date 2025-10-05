import unittest

from correspondence_cryptor import decode_caesar_cipher, encode_caesar_cipher, read_received_messages, shift


class TestMessageLoading(unittest.TestCase):
    def test_load_returns_list_of_dicts(self):
        msgs = read_received_messages("recd_msgs.json")
        self.assertIsInstance(msgs, list)
        self.assertTrue(all(isinstance(m, dict) for m in msgs))

    def test_load_returns_empty_list_for_missing_file(self):
        msgs = read_received_messages("non_existent.json")
        self.assertEqual(msgs, [])


class TestCorrespondenceCryptorDecode(unittest.TestCase):
    """ABCDEFGHIJKLMNOPQRSTUVWXYZ"""
    # decoding functionality tests
    def test_basic_decode(self):
        self.assertEqual(decode_caesar_cipher("ebiil", 3), "hello")

    def test_preserves_case(self):
        self.assertEqual(decode_caesar_cipher("Ebiil", 3), "Hello")

    def test_non_letters_passthrough(self):
        self.assertEqual(decode_caesar_cipher("ebiil, tbii!", 3), "hello, well!")

    def test_large_and_negative_offsets(self):
        self.assertEqual(decode_caesar_cipher("ebiil", 29), "hello")  # 29 == 3 mod 26
        self.assertEqual(decode_caesar_cipher("ebiil", -23), "hello")  # -23 == 3 mod 26

    def test_empty_input(self):
        self.assertEqual(decode_caesar_cipher("", 10), "")

    def test_shift_unit(self):
        # A simple boundary check using ALPHABET
        self.assertEqual(shift("Z", 2), "B")
        self.assertEqual(shift("z", 2), "b")
        self.assertEqual(shift("!", 5), "!")


class TestCorrespondenceCryptorEncode(unittest.TestCase):
    """ABCDEFGHIJKLMNOPQRSTUVWXYZ"""
    # encoding functionality tests
    def test_basic_encode(self):
        self.assertEqual(encode_caesar_cipher("hello", 3), "ebiil")

    def test_preserves_case(self):
        self.assertEqual(encode_caesar_cipher("Hello", 3), "Ebiil")

    def test_non_letters_passthrough(self):
        self.assertEqual(encode_caesar_cipher("hello, well!", 3), "ebiil, tbii!")

    def test_large_offset_normalization(self):
        # 29 mod 26 == 3 → left shift by 3
        self.assertEqual(encode_caesar_cipher("hello", 29), "ebiil")

    def test_negative_offset_supported(self):
        # -23 == 3 mod 26 (and encode uses -offset under the hood)
        self.assertEqual(encode_caesar_cipher("hello", -23), "ebiil")

    def test_empty_input(self):
        self.assertEqual(encode_caesar_cipher("", 7), "")
    
    def test_wrap_edges_mixed_case(self):
        self.assertEqual(encode_caesar_cipher("ZzAa", 1), "YyZz")


class TestRoundTrip(unittest.TestCase):
    def test_round_trip(self):
        msg = "Hello, World!"
        for k in (0, 1, 5, 13, 25, 52, -101):
            with self.subTest(k=k):
                self.assertEqual(
                    decode_caesar_cipher(encode_caesar_cipher(msg, k), k),
                    msg,
                )


class TestWrapCases(unittest.TestCase):
    def test_wrap_pairs(self):
        cases = [("ZzAa", 1, "YyZz"), ("AaZz", 2, "YyXx")]
        for msg, k, expected in cases:
            with self.subTest(k=k, msg=msg):
                self.assertEqual(encode_caesar_cipher(msg, k), expected)


if __name__ == "__main__":
    unittest.main()
