import os
import unittest

import penman

from amr_utils.amr import *
from amr_utils.amr_readers import AMR_Reader
from amr_utils.utils import silence_warnings

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

        # test non-DAG AMRs
        amr = amrs[0].copy()
        amr.root = 'g'
        output = amr.graph_string(pretty_print=False)
        if output != '(g / go-02 :ARG0 (b / boy) :ARG4 (c / city :name (n / name :op1 "New" :op2 "York" :op3 "City")))':
            raise Exception('Failed to print AMR')
        amr.nodes['a'] = 'aardvark'
        amr.nodes['z'] = 'zebra'
        amr.edges.append(('a', ':mod', 'z'))
        output = amr.graph_string(pretty_print=False)
        if output != '(g / go-02 :ARG0 (b / boy) :ARG4 (c / city :name (n / name :op1 "New" :op2 "York" :op3 "City")))':
            raise Exception('Failed to print AMR')
        # test missing nodes
        amr = amrs[0].copy()
        del amr.nodes['b']
        output = amr.graph_string(pretty_print=False)
        if output != '(w / want-01 :ARG0 b :ARG1 (g / go-02 :ARG0 b :ARG4 ' \
                     '(c / city :name (n / name :op1 "New" :op2 "York" :op3 "City"))))':
            raise Exception('Failed to print AMR')
        # test empty root
        amr = amrs[0].copy()
        amr.root = None
        output = amr.graph_string(pretty_print=False)
        if output != '(a / amr-empty)':
            raise Exception('Failed to print AMR')

        # thorough test
        for filename in os.listdir(LDC_DIR):
            file = os.path.join(LDC_DIR, filename)
            for _, amr_string in reader.iterate_amr_strings(file, separate_metadata=True):
                amr = reader.parse(amr_string)
                whitespace_re = re.compile(r'\s+')
                amr_string1 = whitespace_re.sub(' ', amr_string)
                amr_string2 = amr.graph_string(pretty_print=False)
                if amr_string1 != amr_string2:
                    raise Exception('Mismatching AMR string')

    def test_subgraph_string(self):
        reader = AMR_Reader()
        amrs = reader.load(TEST_FILE1, quiet=True)
        amr = amrs[0]
        output = amr.subgraph_string(subgraph_root='g')
        if output != '(g / go-02 :ARG0 (b / boy) :ARG4 (c / city :name (n / name :op1 "New" :op2 "York" :op3 "City")))':
            raise Exception('Failed to print subgraph')

        output = amr.subgraph_string(subgraph_root='g', subgraph_nodes=['g', 'c'])
        if output != '(g / go-02 :ARG0 b :ARG4 (c / city :name n))':
            raise Exception('Failed to print subgraph')

        output = amr.subgraph_string(subgraph_root='w', subgraph_nodes=['w', 'g', 'b'],
                                     subgraph_edges=[('w', ':ARG0', 'b'), ('w', ':ARG1', 'g'), ('g', ':ARG0', 'b')])
        if output != '(w / want-01 :ARG0 (b / boy) :ARG1 (g / go-02 :ARG0 b))':
            raise Exception('Failed to print subgraph')

        amr = AMR()
        output = amr.subgraph_string(subgraph_root='a', subgraph_nodes=['a','b'])
        if output != '(a / amr-empty)':
            raise Exception('Failed to print subgraph')

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
        # test missing node
        amr = amrs[0]
        del amr.nodes['b']
        for t in amr.triples():
            pass

        # thorough test
        for filename in os.listdir(LDC_DIR):
            file = os.path.join(LDC_DIR, filename)
            for _, amr_string in reader.iterate_amr_strings(file, separate_metadata=True):
                amr = reader.parse(amr_string)
                triples1 = {t for t in amr.triples()}
                triples2 = {t for _, t in amr.depth_first_triples(normalize_inverse_relations=False)}
                if triples1 != triples2:
                    raise Exception('Mismatching triples')

    def test_depth_first_triples(self):
        reader = AMR_Reader()
        amrs = reader.load(TEST_FILE1, quiet=True)

        # test run
        for amr in amrs:
            for depth, triple in amr.depth_first_triples():
                pass

        # test ordering, depth_first
        correct = [(1, ('j', ':instance', 'jump-03')), (1, ('j', ':ARG0', 'f')), (2, ('f', ':instance', 'fox')),
                   (2, ('f', ':ARG1-of', 'q')), (3, ('q', ':instance', 'quick-02')), (2, ('f', ':mod', 'b')),
                   (3, ('b', ':instance', 'brown')), (1, ('j', ':ARG2', 'd')), (2, ('d', ':instance', 'dog')),
                   (2, ('d', ':mod', 'l')), (3, ('l', ':instance', 'lazy'))]
        # (j/jump-03 :ARG0 (f/fox
        # 		:ARG1-of (q/quick-02)
        # 		:mod (b/brown))
        # 	:ARG2 (d/dog :mod (l/lazy)))
        test = [(depth, triple) for depth, triple in amrs[1].depth_first_triples()]
        if test != correct:
            raise Exception('Incorrect order')

        # handle attributes
        correct = [('w', ':instance', 'want-01'), ('w', ':ARG0', 'b'), ('b', ':instance', 'boy'),
                   ('w', ':ARG1', 'g'), ('g', ':instance', 'go-02'), ('g', ':ARG0', 'b'), ('g', ':ARG4', 'c'),
                   ('c', ':instance', 'city'), ('c', ':name', 'n'), ('n', ':instance', 'name'),
                   ('n', ':op1', '"New"'), ('n', ':op2', '"York"'), ('n', ':op3', '"City"')]
        # (w/want-01 :ARG0 (b/boy)
        # 	:ARG1 (g/go-02 :ARG0 b
        # 		:ARG4 (c/city :name (n/name :op1 "New"
        # 			:op2 "York"
        # 			:op3 "City"))))
        test = [t for _, t in amrs[0].depth_first_triples()]
        if test != correct:
            raise Exception('Incorrect output')

        # handle artifacts
        correct = [('l', ':instance', 'love-01'), ('l', ':ARG0', 'p'), ('l', ':ARG1', 'p'),
                   ('p', ':instance', 'person'), ('p', ':mod', 'e'), ('e', ':instance', 'every')]
        # (l/love-01
        #     :ARG0 p
        # 	:ARG1 (p/person
        #         :mod (e/every)))
        test = [t for i, t in amrs[4].depth_first_triples()]
        if test != correct:
            raise Exception('Incorrect output')

        # test subgraphs
        correct = [('g', ':instance', 'go-02'), ('g', ':ARG0', 'b'), ('b', ':instance', 'boy'), ('g', ':ARG4', 'c'),
                   ('c', ':instance', 'city'), ('c', ':name', 'n'), ('n', ':instance', 'name'),
                   ('n', ':op1', '"New"'), ('n', ':op2', '"York"'), ('n', ':op3', '"City"')]
        # (w/want-01 :ARG0 (b/boy)
        # 	:ARG1 (g/go-02 :ARG0 b
        # 		:ARG4 (c/city :name (n/name :op1 "New"
        # 			:op2 "York"
        # 			:op3 "City"))))
        test = [t for _, t in amrs[0].depth_first_triples(subgraph_root='g')]
        if test != correct:
            raise Exception('Incorrect output')

        correct = [('g', ':instance', 'go-02'), ('g', ':ARG0', 'b'), ('g', ':ARG4', 'c'),
                   ('c', ':instance', 'city'), ('c', ':name', 'n')]
        # (w/want-01 :ARG0 (b/boy)
        # 	:ARG1 (g/go-02 :ARG0 b
        # 		:ARG4 (c/city :name (n/name :op1 "New"
        # 			:op2 "York"
        # 			:op3 "City"))))
        test = [t for _, t in amrs[0].depth_first_triples(subgraph_root='g', subgraph_nodes=['g', 'c'])]
        if test != correct:
            raise Exception('Incorrect output')

        correct = [('w', ':instance', 'want-01'), ('w', ':ARG0', 'b'), ('b', ':instance', 'boy'),
                   ('w', ':ARG1', 'g'), ('g', ':instance', 'go-02'), ('g', ':ARG0', 'b')]
        # (w/want-01 :ARG0 (b/boy)
        # 	:ARG1 (g/go-02 :ARG0 b
        # 		:ARG4 (c/city :name (n/name :op1 "New"
        # 			:op2 "York"
        # 			:op3 "City"))))
        test = [t for _, t in amrs[0].depth_first_triples(subgraph_edges=[('w', ':ARG0', 'b'), ('w', ':ARG1', 'g'),
                                                                          ('g', ':ARG0', 'b')])]
        if test != correct:
            raise Exception('Incorrect output')
        # test cycle
        correct = [('l2', ':instance', 'love-01'), ('l2', ':ARG1', 'l'), ('l', ':instance', 'love-01'),
                   ('l', ':ARG0', 'i'), ('i', ':instance', 'i'), ('l', ':ARG1', 'p'), ('p', ':instance', 'person'),
                   ('p', ':ARG0-of', 'l2')]
        # (l/love-01 :ARG0 (i/i)
        # 	:ARG1 (p/person
        # 	    :ARG0-of (l2/love-01
        # 	        :ARG1 l)))
        test = [t for _, t in amrs[3].depth_first_triples(subgraph_root='l2')]
        if test != correct:
            raise Exception('Mishandled cycle')

        # thorough test
        for filename in os.listdir(LDC_DIR):
            file = os.path.join(LDC_DIR, filename)
            for _, amr_string in reader.iterate_amr_strings(file, separate_metadata=True):
                amr = reader.parse(amr_string)
                triples1 = [t for _, t in amr.depth_first_triples(normalize_inverse_relations=False)]
                with silence_warnings():
                    g = penman.decode(amr_string, model=reader._TreePenmanModel())
                triples2 = [(s, r, t) for s, r, t in g.triples]
                if triples1 != triples2:
                    raise Exception('Mismatching triples')

    def test_is_frame(self):
        for neg_ex in ['abc', 'abc-def', '0', 'abc-0', 'abc-9999', '0-01', 'abc--01', '-01', '-abc-01']:
            if AMR_Notation.is_frame(neg_ex):
                raise Exception(f'{neg_ex} is not a frame!')
        for pos_ex in ['abc-01', 'abc-99', 'abc-def-100']:
            if not AMR_Notation.is_frame(pos_ex):
                raise Exception(f'{pos_ex} is a frame!')

    def test_is_constant(self):
        for neg_ex in ['abc-01', 'abc', 'abc-def-100']:
            if AMR_Notation.is_constant(neg_ex):
                raise Exception(f'{neg_ex} is not a constant!')
        for pos_ex in ['-', '+', '?', '"New York"', 'imperative', 'expressive']:
            if not AMR_Notation.is_constant(pos_ex):
                raise Exception(f'{pos_ex} is a constant!')

    def test_is_attribute(self):
        amr = AMR(nodes={'a': 'a', 'b': 'b'}, edges=[('a', ':rel', 'b')])
        for neg_ex in ['abc-01', 'abc', 'abc-def-100']:
            amr.nodes['b'] = neg_ex
            if AMR_Notation.is_attribute(amr, amr.edges[0]):
                raise Exception(f'{amr.edges[0][1]} {neg_ex} is not an attribute!')
        for pos_ex in ['-', '+', '?', '"New York"']:
            amr.nodes['b'] = pos_ex
            if not AMR_Notation.is_attribute(amr, amr.edges[0]):
                raise Exception(f'{amr.edges[0][1]} {pos_ex} is an attribute!')
        for ex in ['imperative', 'expressive']:
            amr.nodes['b'] = ex
            amr.edges[0] = ('a', ':mod', 'b')
            if AMR_Notation.is_attribute(amr, amr.edges[0]):
                raise Exception(f'{amr.edges[0][1]} {ex} is not an attribute!')
            amr.edges[0] = ('a', ':mode', 'b')
            if not AMR_Notation.is_attribute(amr, amr.edges[0]):
                raise Exception(f'{amr.edges[0][1]} {ex} is an attribute!')

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
        for neg_ex in [':ARG', ':snt', ':op', ':domain-of', ':mod-of', ':ARG100', 'ARG0', ':consists']:
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

    def test_reify_relation(self):
        correct = (':ARG1-of', 'be-located-at-91', ':ARG2')
        test = AMR_Notation.reify_relation(':location')
        if test != correct:
            raise Exception(f'Failed to reify edge!')

    def test_amr_shape(self):
        reader = AMR_Reader()
        amr = reader.parse('''
        (d / do-01
            :ARG0 a
            :ARG1 a
            :ARG2 a
            :ARG3 (a / aardvark
                :mod b
                :mod b
                :mod (b / buffalo))
            :ARG4 a)
        ''')
        correct = 3
        test = amr.shape.locate_instance('a')
        if test != correct:
            raise Exception('Failed to build AMR Shape')
        correct = 2
        test = amr.shape.locate_instance('b')
        if test != correct:
            raise Exception('Failed to build AMR Shape')


if __name__ == '__main__':
    unittest.main()
