import unittest

from correspondence_cryptor import ALPHABET, decode_caesar_cipher, shift


class TestCorrespondenceCryptor(unittest.TestCase):
    """ABCDEFGHIJKLMNOPQRSTUVWXYZ"""
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


if __name__ == "__main__":
    unittest.main()
