# This file exists to test the translate_roman_numeral function in symbolizer.py

from symbolizer import translate_roman_numeral as trn
import unittest

class TestRomanNumerals(unittest.TestCase):

    def test_I_1(self):
        self.assertEqual(trn('I'), 1)

    def test_II_2(self):
        self.assertEqual(trn('II'), 2)

    def test_VII_7(self):
        self.assertEqual(trn('VII'), 7)

    def test_MMDCCCLXXVIII_2878(self):
        self.assertEqual(trn('MMDCCCLXXVIII'), 2878)

    def test_IV_4(self):
        self.assertEqual(trn('IV'), 4)

    def test_IX_9(self):
        self.assertEqual(trn('IX'), 9)

    def test_MCMXIX_1919(self):
        self.assertEqual(trn('MCMXIX'), 1919)

    def test_CD_400(self):
        self.assertEqual(trn('CD'), 400)

    def test_MMMMMMMMMMMM_12000(self):
        self.assertEqual(trn('MMMMMMMMMMMM'), 12000)

    def test_IIV_raises(self):
        with self.assertRaises(ValueError) as ctx:
            trn('IIV')

    def test_VX_raises(self):
        with self.assertRaises(ValueError) as ctx:
            trn('VX')

    def test_DM_raises(self):
        with self.assertRaises(ValueError) as ctx:
            trn('DM')

    def test_IVI_raises(self):
        with self.assertRaises(ValueError) as ctx:
            trn('IVI')

    def test_CMC_raises(self):
        with self.assertRaises(ValueError) as ctx:
            trn('CMC')

    def test_XXXXX_raises(self):
        with self.assertRaises(ValueError) as ctx:
            trn('XXXXX')

    def test_CCCCC_raises(self):
        with self.assertRaises(ValueError) as ctx:
            trn('CCCCC')

    def test_VV_raises(self):
        with self.assertRaises(ValueError) as ctx:
            trn('VV')

    def test_DD_raises(self):
        with self.assertRaises(ValueError) as ctx:
            trn('DD')

    def test_LL_raises(self):
        with self.assertRaises(ValueError) as ctx:
            trn('LL')

    def test_foobar_raises(self):
        with self.assertRaises(ValueError) as ctx:
            trn('foobar')

    def test_i_raises(self):
        with self.assertRaises(ValueError) as ctx:
            trn('i')

if __name__ == '__main__':
    unittest.main()
