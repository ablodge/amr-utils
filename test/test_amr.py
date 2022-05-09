import unittest

from amr_utils.amr_readers import *

TEST_FILE1 = 'test_data/test_amrs.txt'
TEST_FILE2 = 'test_data/test_amrs2.txt'

LDC_DIR = '../../LDC_2020/data/amrs/unsplit'


class Test_AMR(unittest.TestCase):

    def test_graph_string(self):
        reader = AMR_Reader()
        amrs = reader.load(TEST_FILE1, quiet=True)
        for amr in amrs:
            output = str(amr)
        amrs2 = reader.load(TEST_FILE2, quiet=True)
        for amr in amrs2:
            output = str(amr)

        # test preserves structure
        for _, amr_string in reader.iterate_amr_strings(TEST_FILE1, separate_metadata=True):
            amr = reader.parse(amr_string)
            whitespace_re = re.compile(r'\s+')
            amr_string1 = whitespace_re.sub(' ', amr_string)
            amr_string2 = amr.graph_string(pretty_print=False)
            if amr_string1 != amr_string2:
                raise Exception('Mismatching string')

        # test non-DAG AMRs
        amr = amrs[0]
        output = amr._graph_string(pretty_print=True, subgraph_root='g')

        # thorough test
        for filename in os.listdir(LDC_DIR):
            file = os.path.join(LDC_DIR, filename)
            for _, amr_string in reader.iterate_amr_strings(file, separate_metadata=True):
                amr = reader.parse(amr_string)
                whitespace_re = re.compile(r'\s+')
                amr_string1 = whitespace_re.sub(' ', amr_string)
                amr_string2 = amr.graph_string(pretty_print=False)
                n1 = len(amr.edges)
                amr_normalizers.remove_duplicate_edges(amr)
                n2 = len(amr.edges)
                if n1 != n2:
                    continue
                if amr_string1 != amr_string2:
                    raise Exception('Mismatching string')

    def test_triples(self):
        reader = AMR_Reader()
        amrs = reader.load(TEST_FILE1, quiet=True)
        # handle attributes
        correct = [('w', ':instance', 'want-01'), ('b', ':instance', 'boy'), ('g', ':instance', 'go-02'),
                   ('c', ':instance', 'city'), ('n', ':instance', 'name'), ('w', ':ARG0', 'b'),
                   ('w', ':ARG1', 'g'), ('g', ':ARG0', 'b'), ('g', ':ARG4', 'c'),
                   ('c', ':name', 'n'), ('n', ':op1', '"New"'), ('n', ':op2', '"York"'), ('n', ':op3', '"City"')]
        # (w/want-01 :ARG0 (b/boy)
        # 	:ARG1 (g/go-02 :ARG0 b
        # 		:ARG4 (c/city :name (n/name :op1 "New"
        # 			:op2 "York"
        # 			:op3 "City"))))
        test = [e for e in amrs[0].triples()]
        if test != correct:
            raise Exception('Incorrect output')

    def test_is_frame(self):
        for neg_ex in ['abc', 'abc-def', '0', 'abc-0', 'abc-9999', '0-01', 'abc--01', '-01', '-abc-01']:
            if AMR_Notation.is_frame(neg_ex):
                raise Exception(f'{neg_ex} is not a frame!')
        for pos_ex in ['abc-01', 'abc-99', 'abc-def-100']:
            if not AMR_Notation.is_frame(pos_ex):
                raise Exception(f'{pos_ex} is a frame!')

    def test_is_attribute(self):
        for neg_ex in ['abc-01', 'abc', 'abc-def-100']:
            if AMR_Notation.is_attribute(neg_ex):
                raise Exception(f'{neg_ex} is not a frame!')
        for pos_ex in ['-', '+', '?', '"New York"', 'imperative', 'expressive']:
            if not AMR_Notation.is_attribute(pos_ex):
                raise Exception(f'{pos_ex} is a frame!')

    def test_is_inverse_relation(self):
        for neg_ex in [':consist-of', ':prep-out-of', ':prep-on-behalf-of', ':domain', ':mod', ':ARG0']:
            if AMR_Notation.is_inverse_relation(neg_ex):
                raise Exception(f'{neg_ex} is not an inverse relation!')
        for pos_ex in [':consist-of-of', ':prep-out-of-of', ':prep-on-behalf-of-of', ':ARG0-of']:
            if not AMR_Notation.is_inverse_relation(pos_ex):
                raise Exception(f'{pos_ex} is an inverse relation!')

    def test_invert_relation(self):
        for input, output in [(':domain', ':mod'), (':ARG0', ':ARG0-of'), (':consist-of', ':consist-of-of'),
                              (':prep-out-of', ':prep-out-of-of'), (':prep-on-behalf-of', ':prep-on-behalf-of-of')]:
            if AMR_Notation.invert_relation(input) != output:
                raise Exception(f'The inverse of {input} is {output} !')
            if AMR_Notation.invert_relation(output) != input:
                raise Exception(f'The inverse of {output} is {input} !')

    def test_is_relation(self):
        for neg_ex in [':ARG', ':snt', ':op', ':domain-of', ':mod-of', ':ARG10', 'ARG0', ':consists']:
            if AMR_Notation.is_relation(neg_ex):
                raise Exception(f'{neg_ex} is not a relation!')
        for pos_ex in [':ARG9', ':snt999', ':op999', ':domain', ':mod', ':day', ':value', ':consist-of',
                       ':consist-of-of', ':ARG9-of', ':prep-out-of', ':prep-out-of-of']:
            if not AMR_Notation.is_relation(pos_ex):
                raise Exception(f'{pos_ex} is a relation!')

    def test_lexicographic_edge_key(self):
        amr = AMR(nodes={'a': 'a', 'b': 'b', 'c': 'c'})
        test = [('a', ':ARG0', 'b'), ('a', ':ARG11', 'b'), ('a', ':ARG10', 'b'), ('a', ':ARG2', 'b'),
                ('a', ':ARG0-of', 'b'), ('a', ':value', 'b'), ('a', ':mod', 'c'), ('a', ':mod', 'b')]
        test = [e for e in sorted(test, key=lambda e: AMR_Notation.lexicographic_edge_key(amr, e))]
        correct = [('a', ':ARG0', 'b'), ('a', ':ARG0-of', 'b'), ('a', ':ARG2', 'b'), ('a', ':ARG10', 'b'),
                   ('a', ':ARG11', 'b'), ('a', ':mod', 'b'), ('a', ':mod', 'c'), ('a', ':value', 'b'), ]
        if test != correct:
            raise Exception(f'Failed to sort edges!')


if __name__ == '__main__':
    unittest.main()
