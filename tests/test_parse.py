import unittest
from collections import Counter, OrderedDict
from grable.parsers import LiteralParser, ConcatParser
from grable.parsers import AlternationParser, VariableParser


class TestParsers(unittest.TestCase):

    def setUp(self):
        self.input_surf = { "surf": "blepton" }
        self.input_gloss = { "gl": "[jump][3sg]"}
        self.blep = LiteralParser("surf", "blep")
        self.ton = LiteralParser("surf", "ton")
        self.ble = LiteralParser("surf", "ble")
        self.p = LiteralParser("surf", "p")
        self.null_surf = LiteralParser("surf", "")
        self.tr = LiteralParser("gl", "[tr]")
        self.run = LiteralParser("gl", "[run]")
        self.jump = LiteralParser("gl", "[jump]")
        self.sg3 = LiteralParser("gl", "[3sg]")
        
        self.whole_word = ConcatParser([self.blep, self.ton])
        self.whole_word2 = ConcatParser([self.ble, self.p, self.ton])
        self.beginnings = AlternationParser([self.blep, self.ble])
        self.garden_path = ConcatParser([self.beginnings, self.ton])

        self.glosses = ConcatParser([self.jump, self.sg3])
        self.transduce = ConcatParser([self.blep, self.jump, self.ton, self.sg3])
        self.nested_transduce = ConcatParser([ConcatParser([self.blep, self.jump]),
                                            ConcatParser([self.ton, self.sg3])])

        self.transduce2 = ConcatParser([self.ble, self.run, 
                                        self.p, self.tr, 
                                        self.ton, self.sg3])
        
        self.ambiguous = AlternationParser([self.transduce, self.transduce2])
        
    def tearDown(self):
        pass

    def test_literal(self):
        result = list(self.blep(self.input_surf, Counter()))
        self.assertEqual(result, [({}, {"surf": "ton"})])

        result = list(self.jump(self.input_gloss, Counter()))
        self.assertEqual(result, [({}, {"gl": "[3sg]"})])

    def test_concat(self):
        result = list(self.whole_word(self.input_surf, Counter()))
        self.assertEqual(result, [({}, {'surf': ''})])

        result = list(self.whole_word2(self.input_surf, Counter()))
        self.assertEqual(result, [({}, {'surf': ''})])

        result = list(self.glosses(self.input_gloss, Counter()))
        self.assertEqual(result, [({}, {'gl': ''})])

    def test_alternate(self):
        result = list(self.beginnings(self.input_surf, Counter()))
        self.assertEqual(result, [({}, {'surf': 'ton'}), 
                                  ({}, {'surf': 'pton'})])

        result = list(self.whole_word(self.input_surf, Counter()))
        self.assertEqual(result, [({}, {'surf': ''})])

        result = list(self.garden_path(self.input_surf, Counter()))
        self.assertEqual(result, [({}, {'surf': ''})])


    def test_transduce(self):
        result = list(self.transduce(self.input_surf, Counter()))
        self.assertEqual(result, [({"gl": "[jump][3sg]"}, {'surf': ''})])


        result = list(self.nested_transduce(self.input_surf, Counter()))
        self.assertEqual(result, [({"gl": "[jump][3sg]"}, {'surf': ''})])


        result = list(self.transduce(self.input_gloss, Counter()))
        self.assertEqual(result, [({"surf": "blepton"}, {'gl': ''})])

        result = list(self.ambiguous(self.input_surf, Counter()))
        self.assertEqual(result, [({"gl": "[jump][3sg]"}, {'surf': ''}),
                                ({"gl": "[run][tr][3sg]"}, {'surf': ''})
        ])

        result = list(self.ambiguous(self.input_gloss, Counter()))
        self.assertEqual(result, [({"surf": "blepton"}, {'gl': ''})])


if __name__ == '__main__':
    unittest.main()