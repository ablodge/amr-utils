import json
import unittest

from amr_utils.amr import AMR
from amr_utils.amr_alignments import AMR_Alignment, AMR_Alignment_Set
from amr_utils.amr_readers import AMR_Reader, Graph_Metadata_AMR_Reader

TEST_FILE1 = 'test_data/test_amrs.txt'
TEST_FILE2 = 'test_data/test_amrs2.txt'

LDC_DIR = '../../LDC_2020/data/amrs/unsplit'

LEAMR_FILE = r'C:\Users\Austin\OneDrive\Desktop\leamr\data-release\alignments\ldc+little_prince.subgraph_alignments.json'
LEAMR_AMRS = r'C:\Users\Austin\OneDrive\Desktop\leamr\data-release\amrs\ldc+little_prince.txt'


class Test_AMR_Alignments(unittest.TestCase):
    amr = AMR.from_string('''
    (w / want-01
        :ARG0 (b / boy)
        :ARG1 (g / go-02
            :ARG0 b
            :ARG4 (c / city
                :name (n / name :op1 "New"
                    :op2 "York" :op3 "City"))))
    ''',
                          tokens=['The', 'boy', 'wants', 'to', 'go', 'to', 'New', 'York', '.'])
    alignments = AMR_Alignment_Set(amr)
    alignments.align(type='subgraph', tokens=[1], nodes=['b'])
    alignments.align(type='subgraph', tokens=[2], nodes=['w'])
    alignments.align(type='subgraph', tokens=[4], nodes=['g'])
    alignments.align(type='subgraph', tokens=[6, 7], nodes=['c', 'n', 'x0', 'x1', 'x2'],
                     edges=[('c', ':name', 'n'), ('n', ':op1', 'x0'), ('n', ':op2', 'x1'),
                            ('n', ':op3', 'x2')])
    alignments.align(type='arg structure', tokens=[2], nodes=['w'],
                     edges=[('w', ':ARG0', 'b'), ('w', ':ARG1', 'g')])
    alignments.align(type='arg structure', tokens=[4], nodes=['g'],
                     edges=[('g', ':ARG0', 'b'), ('g', ':ARG4', 'c')])
    alignments.align(type='reentrancy:control', tokens=[2], edges=[('g', ':ARG0', 'b')])

    amr2 = AMR.from_string('''
    (m / make-up-10
        :ARG0 (i / i)
        :ARG1 (s / story
                :mod (w / whole)))
    ''',
                           tokens=['I', 'made', 'the', 'whole', 'story', 'up', '!'])
    alignments2 = AMR_Alignment_Set(amr2)
    alignments2.align(tokens=[0], nodes=['b'])
    alignments2.align(tokens=[1, 5], nodes=['m'])
    alignments2.align(tokens=[2])
    alignments2.align(tokens=[3], nodes=['w'])
    alignments2.align(tokens=[4], nodes=['s'])
    alignments2.align(tokens=[6])

    def test_alignment(self):
        align1 = AMR_Alignment(type='subgraph', tokens=[1], nodes=['b'])
        align2 = AMR_Alignment(type='subgraph', tokens=[2], nodes=['w'])
        align3 = AMR_Alignment(type='subgraph', tokens=[4], nodes=['g'])
        align4 = AMR_Alignment(type='subgraph', tokens=[6, 7], nodes=['c', 'n', 'x0', 'x1', 'x2'],
                               edges=[('c', ':name', 'n'), ('n', ':op1', 'x0'), ('n', ':op2', 'x1'),
                                      ('n', ':op3', 'x2')])
        align5 = AMR_Alignment(type='arg structure', tokens=[2], nodes=['w'],
                               edges=[('w', ':ARG0', 'b'), ('w', ':ARG1', 'g')])
        align6 = AMR_Alignment(type='arg structure', tokens=[4], nodes=['g'],
                               edges=[('g', ':ARG0', 'b'), ('g', ':ARG4', 'c')])
        align7 = AMR_Alignment(type='reentrancy:control', tokens=[2], edges=[('g', ':ARG0', 'b')])

        self.assertRaises(ValueError, lambda: AMR_Alignment(tokens=[], nodes=['w']))
        # print()

    def test_to_json(self):
        test = []
        for align in self.alignments:
            test.append(align.to_json())
        test2 = []
        for align in self.alignments:
            test2.append(align.to_json(self.amr))
        correct = [{'type': 'subgraph', 'tokens': [1], 'nodes': ['b'], 'description': 'subgraph : boy => (a0 / boy)'},
                   {'type': 'arg structure', 'tokens': [2], 'nodes': ['w'],
                    'edges': [('w', ':ARG0', 'b'), ('w', ':ARG1', 'g')],
                    'description': 'arg structure : wants => (a0 / want-01 :ARG0 <var> :ARG1 <var>)'},
                   {'type': 'reentrancy:control', 'tokens': [2], 'edges': [('g', ':ARG0', 'b')],
                    'description': 'reentrancy:control : wants => (<var> :ARG0 <var>)'},
                   {'type': 'subgraph', 'tokens': [2], 'nodes': ['w'], 'description':
                       'subgraph : wants => (a0 / want-01)'},
                   {'type': 'arg structure', 'tokens': [4], 'nodes': ['g'],
                    'edges': [('g', ':ARG0', 'b'), ('g', ':ARG4', 'c')],
                    'description': 'arg structure : go => (a0 / go-02 :ARG0 <var> :ARG4 <var>)'},
                   {'type': 'subgraph', 'tokens': [4], 'nodes': ['g'], 'description': 'subgraph : go => (a0 / go-02)'},
                   {'type': 'subgraph', 'tokens': [6, 7], 'nodes': ['c', 'n', 'x0', 'x1', 'x2'],
                    'edges': [('c', ':name', 'n'), ('n', ':op1', 'x0'), ('n', ':op2', 'x1'), ('n', ':op3', 'x2')],
                    'description':
                        'subgraph : New York => (a0 / city :name (a1 / name :op1 "New" :op2 "York" :op3 "City"))'}]
        if test2 != correct:
            raise Exception('Failed to produce JSON')

        # test anonymize
        correct = [{'type': 'subgraph', 'tokens': [1], 'nodes': ['b']},
                   {'type': 'arg structure', 'tokens': [2], 'nodes': ['w'],
                    'edges': [('w', ':_', 'b'), ('w', ':_', 'g')]},
                   {'type': 'reentrancy:control', 'tokens': [2], 'edges': [('g', ':_', 'b')]},
                   {'type': 'subgraph', 'tokens': [2], 'nodes': ['w']},
                   {'type': 'arg structure', 'tokens': [4], 'nodes': ['g'],
                    'edges': [('g', ':_', 'b'), ('g', ':_', 'c')]},
                   {'type': 'subgraph', 'tokens': [4], 'nodes': ['g']},
                   {'type': 'subgraph', 'tokens': [6, 7], 'nodes': ['c', 'n', 'x0', 'x1', 'x2'],
                    'edges': [('c', ':_', 'n'), ('n', ':_', 'x0'), ('n', ':_', 'x1'), ('n', ':_', 'x2')]}]
        test = self.alignments.to_json(anonymize=True)
        if test != correct:
            raise Exception('Failed to produce JSON')


    def test_description(self):
        align = AMR_Alignment(type='subgraph', tokens=[6, 7], nodes=['c', 'n', 'x0', 'x1', 'x2'],
                              edges=[('c', ':name', 'n'), ('n', ':op1', 'x0'), ('n', ':op2', 'x1'),
                                     ('n', ':op3', 'x2')])
        test = align.description(self.amr)
        if test != 'subgraph : New York => (a0 / city :name (a1 / name :op1 "New" :op2 "York" :op3 "City"))':
            raise Exception('Failed to make description')
        align = AMR_Alignment(type='arg structure', tokens=[2], edges=[('w', ':ARG0', 'b'), ('w', ':ARG1', 'g')])
        test = align.description(self.amr)
        if test != 'arg structure : wants => (<var> :ARG0 <var> :ARG1 <var>)':
            raise Exception('Failed to make description')

    def test_str(self):
        align = AMR_Alignment(type='subgraph', tokens=[6, 7], nodes=['c', 'n', 'x0', 'x1', 'x2'],
                              edges=[('c', ':name', 'n'), ('n', ':op1', 'x0'), ('n', ':op2', 'x1'),
                                     ('n', ':op3', 'x2')])
        test = str(align)
        if test != '[AMR_Alignment] subgraph : 6, 7 => c, n, x0, x1, x2, c :name n, n :op1 x0, n :op2 x1, n :op3 x2':
            raise Exception('Failed to make description')

    def test_ordering(self):
        prev_align = None
        for align in self.alignments:
            if prev_align is not None:
                if not (prev_align < align):
                    raise Exception('Incorrect Ordering')
                if align < prev_align:
                    raise Exception('Incorrect Ordering')
            prev_align = align
        prev_align = None
        for align in self.alignments2:
            if prev_align is not None:
                if not (prev_align < align):
                    raise Exception('Incorrect Ordering')
                if align < prev_align:
                    raise Exception('Incorrect Ordering')
            prev_align = align

        # spans
        align1 = AMR_Alignment(tokens=[0, 1])
        align2 = AMR_Alignment(tokens=[0, 2])
        if not (align1 < align2):
            raise Exception('Incorrect Ordering')
        align1 = AMR_Alignment(tokens=[0, 1])
        align2 = AMR_Alignment(tokens=[1])
        if not (align1 < align2):
            raise Exception('Incorrect Ordering')

        # types
        align1 = AMR_Alignment(tokens=[0])
        align2 = AMR_Alignment(tokens=[0], type='type A')
        if not (align1 < align2):
            raise Exception('Incorrect Ordering')
        align1 = AMR_Alignment(tokens=[0], type='type A')
        align2 = AMR_Alignment(tokens=[0], type='type B')
        if not (align1 < align2):
            raise Exception('Incorrect Ordering')

        # nodes
        align1 = AMR_Alignment(tokens=[0])
        align2 = AMR_Alignment(tokens=[0], nodes=['a'])
        if not (align1 < align2):
            raise Exception('Incorrect Ordering')
        align1 = AMR_Alignment(tokens=[0], nodes=['a'])
        align2 = AMR_Alignment(tokens=[0], nodes=['a', 'b'])
        if not (align1 < align2):
            raise Exception('Incorrect Ordering')

        # edges
        align1 = AMR_Alignment(tokens=[0])
        align2 = AMR_Alignment(tokens=[0], edges=[('a', ':mod', 'z')])
        if not (align1 < align2):
            raise Exception('Incorrect Ordering')
        align1 = AMR_Alignment(tokens=[0], edges=[('a', ':mod', 'z')])
        align2 = AMR_Alignment(tokens=[0], edges=[('a2', ':mod', 'z')])
        if not (align1 < align2):
            raise Exception('Incorrect Ordering')

    def test_is_connected(self):
        # pos examples
        align = AMR_Alignment(type='subgraph', tokens=[6, 7], nodes=['c', 'n', 'x0', 'x1', 'x2'],
                              edges=[('c', ':name', 'n'), ('n', ':op1', 'x0'), ('n', ':op2', 'x1'),
                                     ('n', ':op3', 'x2')])
        if not align.is_connected(self.amr):
            raise Exception('Failed to test connectivity')
        align = AMR_Alignment(type='arg structure', tokens=[2], edges=[('w', ':ARG0', 'b'), ('w', ':ARG1', 'g')])
        if not align.is_connected(self.amr):
            raise Exception('Failed to test connectivity')
        align = AMR_Alignment(type='arg structure', tokens=[2], nodes=['w'],
                              edges=[('w', ':ARG0', 'b'), ('w', ':ARG1', 'g')])
        if not align.is_connected(self.amr):
            raise Exception('Failed to test connectivity')
        align = AMR_Alignment(type='reentrancy:control', tokens=[2], edges=[('g', ':ARG0', 'b')])
        if not align.is_connected(self.amr):
            raise Exception('Failed to test connectivity')
        align = AMR_Alignment(type='arg structure', tokens=[2], nodes=['g'],
                              edges=[('w', ':ARG1', 'g'), ('g', ':ARG0', 'b'), ('g', ':ARG4', 'c')])
        if not align.is_connected(self.amr):
            raise Exception('Failed to test connectivity')

        # neg examples
        align = AMR_Alignment(type='arg structure', tokens=[2], edges=[('w', ':ARG0', 'b'), ('c', ':name', 'n')])
        if align.is_connected(self.amr):
            raise Exception('Failed to test connectivity')
        align = AMR_Alignment(type='arg structure', tokens=[2], nodes=['w', 'c'])
        if align.is_connected(self.amr):
            raise Exception('Failed to test connectivity')
        align = AMR_Alignment(type='arg structure', tokens=[2], nodes=['n'],
                              edges=[('w', ':ARG0', 'b'), ('w', ':ARG1', 'g')])
        if align.is_connected(self.amr):
            raise Exception('Failed to test connectivity')

    def test_add(self):
        ordering = [str(align) for align in self.alignments]

        # test container
        for align in self.alignments:
            if align._container is not self.alignments:
                raise Exception('Failed to add alignment')
        align = AMR_Alignment(tokens=[0], nodes=['b'])
        self.alignments.add(align)

        # test contains
        if align not in self.alignments:
            raise Exception('Failed to add alignment')

        # test container
        if align._container is not self.alignments:
            raise Exception('Failed to add alignment')

        # test ordering
        prev_align = None
        for a in self.alignments:
            if prev_align is not None:
                if not (prev_align < a):
                    raise Exception('Incorrect Ordering')
                if a < prev_align:
                    raise Exception('Incorrect Ordering')
            prev_align = a

        # test double container
        new_alignments = AMR_Alignment_Set(self.amr)
        self.assertRaises(ValueError, lambda: new_alignments.add(align))

        # test add existing alignment
        len1 = len(self.alignments)
        self.alignments.add(AMR_Alignment(tokens=[0], nodes=['b']))
        if len(self.alignments) != len1:
            raise Exception('Failed to add alignment')
        self.alignments.remove(align)
        if align._container is not None:
            raise Exception('Failed to add alignment')
        if [str(a) for a in self.alignments] != ordering:
            raise Exception('Failed to add alignment')
        if align in self.alignments:
            raise Exception('Failed to add alignment')

    def test_remove(self):
        ordering = [str(align) for align in self.alignments]

        align = self.alignments.get(span=[6,7])
        if align._container is not self.alignments:
            raise Exception('Failed to remove alignment')
        self.alignments.remove(align)

        # test ordering
        prev_align = None
        for a in self.alignments:
            if prev_align is not None:
                if not (prev_align < a):
                    raise Exception('Incorrect Ordering')
                if a < prev_align:
                    raise Exception('Incorrect Ordering')
            prev_align = a

        # test container
        if align._container is not None:
            raise Exception('Failed to remove alignment')
        if align in self.alignments:
            raise Exception('Failed to remove alignment')
        self.alignments.add(align)

        if [str(a) for a in self.alignments] != ordering:
            raise Exception('Failed to remove alignment')

    def test_modify_alignment(self):
        ordering = [str(align) for align in self.alignments]

        align = self.alignments.get(node='w')
        if align._container is None:
            raise Exception('Failed to modify alignment')

        # test `add()`
        align.add(nodes=['b'])
        if 'b' not in align.nodes():
            raise Exception('Failed to modify alignment')

        # test ordering
        prev_align = None
        for a in self.alignments:
            if prev_align is not None:
                if not (prev_align < a):
                    raise Exception('Incorrect Ordering')
                if a < prev_align:
                    raise Exception('Incorrect Ordering')
            prev_align = a

        # test `set()`
        align.set(nodes=['w'])

        if [str(a) for a in self.alignments] != ordering:
            raise Exception('Failed to modify alignment')

    def test_binary_search(self):
        test = [align for align in self.alignments._binary_search_by_span(span=(2,))]
        correct = [AMR_Alignment(type='arg structure', tokens=[2], nodes=['w'],
                                 edges=[('w', ':ARG0', 'b'), ('w', ':ARG1', 'g')]),
                   AMR_Alignment(type='reentrancy:control', tokens=[2], edges=[('g', ':ARG0', 'b')]),
                   AMR_Alignment(type='subgraph', tokens=[2], nodes=['w'])]
        if test != correct:
            raise Exception('Failed to iter by binary search')

        test = [align for align in self.alignments._binary_search_by_token(2)]
        correct.append(AMR_Alignment(type='subgraph', tokens=[1], nodes=['b']))
        if test != correct:
            raise Exception('Failed to iter by binary search')

    def test_linear_search(self):
        test = [align for align in self.alignments._linear_search_by_token(2)]
        correct = [AMR_Alignment(type='subgraph', tokens=[1], nodes=['b']),
                   AMR_Alignment(type='arg structure', tokens=[2], nodes=['w'],
                                 edges=[('w', ':ARG0', 'b'), ('w', ':ARG1', 'g')]),
                   AMR_Alignment(type='reentrancy:control', tokens=[2], edges=[('g', ':ARG0', 'b')]),
                   AMR_Alignment(type='subgraph', tokens=[2], nodes=['w'])]
        if test != correct:
            raise Exception('Failed to iter by binary search')

    def test_get(self):
        # Empty alignments
        alignments = AMR_Alignment_Set(self.amr)
        align = alignments.get(token_id=0)
        if align is not None:
            raise Exception('Failed to get alignment')
        align = alignments.get(token_id=0, node='a')
        if align is not None:
            raise Exception('Failed to get alignment')

        # by token
        alignments = self.alignments
        align = alignments.get(token_id=2)
        correct = AMR_Alignment(type='arg structure', tokens=[2], nodes=['w'],
                                edges=[('w', ':ARG0', 'b'), ('w', ':ARG1', 'g')])
        if align != correct:
            raise Exception('Failed to get alignment')
        align = alignments.get(token_id=6)
        correct = AMR_Alignment(type='subgraph', tokens=[6, 7], nodes=['c', 'n', 'x0', 'x1', 'x2'],
                                edges=[('c', ':name', 'n'), ('n', ':op1', 'x0'), ('n', ':op2', 'x1'),
                                       ('n', ':op3', 'x2')])
        if align != correct:
            raise Exception('Failed to get alignment')

        # by span
        align = alignments.get(span=[2])
        correct = AMR_Alignment(type='arg structure', tokens=[2], nodes=['w'],
                                edges=[('w', ':ARG0', 'b'), ('w', ':ARG1', 'g')])
        if align != correct:
            raise Exception('Failed to get alignment')
        align = alignments.get(span=[6, 7])
        correct = AMR_Alignment(type='subgraph', tokens=[6, 7], nodes=['c', 'n', 'x0', 'x1', 'x2'],
                                edges=[('c', ':name', 'n'), ('n', ':op1', 'x0'), ('n', ':op2', 'x1'),
                                       ('n', ':op3', 'x2')])
        if align != correct:
            raise Exception('Failed to get alignment')

        # by node
        align = alignments.get(node='w')
        correct = AMR_Alignment(type='arg structure', tokens=[2], nodes=['w'],
                                edges=[('w', ':ARG0', 'b'), ('w', ':ARG1', 'g')])
        if align != correct:
            raise Exception('Failed to get alignment')
        # by edge
        align = alignments.get(edge=('w', ':ARG0', 'b'))
        correct = AMR_Alignment(type='arg structure', tokens=[2], nodes=['w'],
                                edges=[('w', ':ARG0', 'b'), ('w', ':ARG1', 'g')])
        if align != correct:
            raise Exception('Failed to get alignment')

        # missing value
        align = alignments.get(token_id=0)
        if align is not None:
            raise Exception('Failed to get alignment')

        # token and node
        correct = AMR_Alignment(tokens=[2], nodes=['b'])
        alignments.add(correct)
        align = alignments.get(token_id=2, node='b')
        if align != correct:
            raise Exception('Failed to get alignment')
        alignments.remove(correct)

        # span and node
        correct = AMR_Alignment(tokens=[6, 7], nodes=['b'])
        alignments.add(correct)
        align = alignments.get(token_id=6, node='b')
        if align != correct:
            raise Exception('Failed to get alignment')
        alignments.remove(correct)

        # type and span and node
        test = self.alignments.get(span=[2], type='subgraph', node='w')
        correct = AMR_Alignment(type='subgraph', tokens=[2], nodes=['w'])
        if test != correct:
            raise Exception('Failed to get alignment')

        # overlapping spans
        align = alignments.get(span=[5, 6])
        if align is not None:
            raise Exception('Failed to get alignment')

        # contained span
        align = alignments.get(span=[6])
        if align is not None:
            raise Exception('Failed to get alignment')

        # gappy MWE
        correct = AMR_Alignment(tokens=[1, 5], nodes=['m'])
        align = self.alignments2.get(token_id=1)
        if align != correct:
            raise Exception('Failed to get alignment')
        align = self.alignments2.get(token_id=5)
        if align != correct:
            raise Exception('Failed to get alignment')
        align = self.alignments2.get(span=[1, 5])
        if align != correct:
            raise Exception('Failed to get alignment')

    def test_get_all(self):
        # token
        test = self.alignments.get_all(token_id=2)
        correct = [AMR_Alignment(type='arg structure', tokens=[2], nodes=['w'],
                                 edges=[('w', ':ARG0', 'b'), ('w', ':ARG1', 'g')]),
                   AMR_Alignment(type='reentrancy:control', tokens=[2], edges=[('g', ':ARG0', 'b')]),
                   AMR_Alignment(type='subgraph', tokens=[2], nodes=['w'])
                   ]
        if test != correct:
            raise Exception('Failed to get alignment')
        # span
        test = self.alignments.get_all(span=[6, 7])
        correct = [AMR_Alignment(type='subgraph', tokens=[6, 7], nodes=['c', 'n', 'x0', 'x1', 'x2'],
                                 edges=[('c', ':name', 'n'), ('n', ':op1', 'x0'), ('n', ':op2', 'x1'),
                                        ('n', ':op3', 'x2')])]
        if test != correct:
            raise Exception('Failed to get alignment')
        # node
        test = self.alignments.get_all(node='w')
        correct = [AMR_Alignment(type='arg structure', tokens=[2], nodes=['w'],
                                 edges=[('w', ':ARG0', 'b'), ('w', ':ARG1', 'g')]),
                   AMR_Alignment(type='subgraph', tokens=[2], nodes=['w'])
                   ]
        if test != correct:
            raise Exception('Failed to get alignment')

        # edge
        test = self.alignments.get_all(edge=('g', ':ARG0', 'b'))
        correct = [AMR_Alignment(type='reentrancy:control', tokens=[2], edges=[('g', ':ARG0', 'b')]),
                   AMR_Alignment(type='arg structure', tokens=[4], nodes=['g'],
                                 edges=[('g', ':ARG0', 'b'), ('g', ':ARG4', 'c')]),
                   ]
        if test != correct:
            raise Exception('Failed to get alignment')

        # node and token
        test = self.alignments.get_all(token_id=2, node='w')
        correct = [AMR_Alignment(type='arg structure', tokens=[2], nodes=['w'],
                                 edges=[('w', ':ARG0', 'b'), ('w', ':ARG1', 'g')]),
                   AMR_Alignment(type='subgraph', tokens=[2], nodes=['w'])
                   ]
        if test != correct:
            raise Exception('Failed to get alignment')

        # type and span and node
        test = self.alignments.get_all(span=[2], node='w', type='subgraph')
        correct = [AMR_Alignment(type='subgraph', tokens=[2], nodes=['w'])]
        if test != correct:
            raise Exception('Failed to get alignment')

        # missing
        test = self.alignments.get_all(span=[0])
        if test:
            raise Exception('Failed to get alignment')

    def test_find(self):
        # failed condition
        test = self.alignments.find(lambda a: 'z' in a.nodes())
        if test is not None:
            raise Exception('Failed to find alignments')

        # contains edges
        test = self.alignments.find(lambda a: bool(a.edges()))
        correct = AMR_Alignment(type='arg structure', tokens=[2], nodes=['w'],
                                 edges=[('w', ':ARG0', 'b'), ('w', ':ARG1', 'g')])
        if test != correct:
            raise Exception('Failed to find alignments')
        # multiple tokens
        test = self.alignments.find(lambda a: len(a.tokens()) > 1)
        correct = AMR_Alignment(type='subgraph', tokens=[6, 7], nodes=['c', 'n', 'x0', 'x1', 'x2'],
                                 edges=[('c', ':name', 'n'), ('n', ':op1', 'x0'), ('n', ':op2', 'x1'),
                                        ('n', ':op3', 'x2')])
        if test != correct:
            raise Exception('Failed to find alignments')

        # gappy MWE
        def is_gappy(tokens):
            prev_tok = None
            for tok in tokens:
                if prev_tok is not None and tok != prev_tok + 1:
                    return True
                prev_tok = tok
            return False

        test = self.alignments2.find(lambda a: is_gappy(a.tokens()))
        correct = AMR_Alignment(tokens=[1, 5], nodes=['m'])
        if test != correct:
            raise Exception('Failed to find alignments')

    def test_find_all(self):
        # failed condition
        test = self.alignments.find_all(lambda a: 'z' in a.nodes())
        if test:
            raise Exception('Failed to find alignments')

        # contains edges
        test = self.alignments.find_all(lambda a: bool(a.edges()))
        correct = [AMR_Alignment(type='arg structure', tokens=[2], nodes=['w'],
                                 edges=[('w', ':ARG0', 'b'), ('w', ':ARG1', 'g')]),
                   AMR_Alignment(type='reentrancy:control', tokens=[2], edges=[('g', ':ARG0', 'b')]),
                   AMR_Alignment(type='arg structure', tokens=[4], nodes=['g'],
                                 edges=[('g', ':ARG0', 'b'), ('g', ':ARG4', 'c')]),
                   AMR_Alignment(type='subgraph', tokens=[6, 7], nodes=['c', 'n', 'x0', 'x1', 'x2'],
                                 edges=[('c', ':name', 'n'), ('n', ':op1', 'x0'), ('n', ':op2', 'x1'),
                                        ('n', ':op3', 'x2')]),
                   ]
        if test != correct:
            raise Exception('Failed to find alignments')
        # multiple tokens
        test = self.alignments.find_all(lambda a: len(a.tokens()) > 1)
        correct = [AMR_Alignment(type='subgraph', tokens=[6, 7], nodes=['c', 'n', 'x0', 'x1', 'x2'],
                                 edges=[('c', ':name', 'n'), ('n', ':op1', 'x0'), ('n', ':op2', 'x1'),
                                        ('n', ':op3', 'x2')]),
                   ]
        if test != correct:
            raise Exception('Failed to find alignments')

        # gappy MWE
        def is_gappy(tokens):
            prev_tok = None
            for tok in tokens:
                if prev_tok is not None and tok != prev_tok+1:
                    return True
                prev_tok = tok
            return False
        test = self.alignments2.find_all(lambda a: is_gappy(a.tokens()))
        correct = [AMR_Alignment(tokens=[1, 5], nodes=['m'])]
        if test != correct:
            raise Exception('Failed to find alignments')

    def test_from_json(self):
        json_data = [{'type': 'subgraph', 'tokens': [1], 'nodes': ['b'], 'description': 'subgraph : boy => (a0 / boy)'},
                   {'type': 'arg structure', 'tokens': [2], 'nodes': ['w'],
                    'edges': [('w', ':ARG0', 'b'), ('w', ':ARG1', 'g')],
                    'description': 'arg structure : wants => (a0 / want-01 :ARG0 <var> :ARG1 <var>)'},
                   {'type': 'reentrancy:control', 'tokens': [2], 'edges': [('g', ':ARG0', 'b')],
                    'description': 'reentrancy:control : wants => (<var> :ARG0 <var>)'},
                   {'type': 'subgraph', 'tokens': [2], 'nodes': ['w'], 'description':
                       'subgraph : wants => (a0 / want-01)'},
                   {'type': 'arg structure', 'tokens': [4], 'nodes': ['g'],
                    'edges': [('g', ':ARG0', 'b'), ('g', ':ARG4', 'c')],
                    'description': 'arg structure : go => (a0 / go-02 :ARG0 <var> :ARG4 <var>)'},
                   {'type': 'subgraph', 'tokens': [4], 'nodes': ['g'], 'description': 'subgraph : go => (a0 / go-02)'},
                   {'type': 'subgraph', 'tokens': [6, 7], 'nodes': ['c', 'n', 'x0', 'x1', 'x2'],
                    'edges': [('c', ':name', 'n'), ('n', ':op1', 'x0'), ('n', ':op2', 'x1'), ('n', ':op3', 'x2')],
                    'description':
                        'subgraph : New York => (a0 / city :name (a1 / name :op1 "New" :op2 "York" :op3 "City"))'}]
        alignments = AMR_Alignment_Set.from_json(self.amr, json_data)
        if len(alignments) != len(self.alignments):
            raise Exception('Failed to read JSON')
        for align1, align2 in zip(alignments, self.alignments):
            if align1 != align2:
                raise Exception('Failed to read JSON')
        reader = AMR_Reader()
        amrs = reader.load('test_data/test_amrs.txt')
        with open('test_data/test_amrs.alignments.json') as fr:
            json_data = json.load(fr)
        for amr, key in zip(amrs, json_data):
            edges = set(amr.edges)
            alignments = AMR_Alignment_Set.from_json(amr, json_data[key])
            for align in alignments:
                for n in align.nodes():
                    if n not in amr.nodes:
                        raise Exception('Failed to read JSON')
                for e in align.edges():
                    if e not in edges:
                        raise Exception('Failed to read JSON')

    def test_is_projective(self):
        # raising
        amr = AMR.from_string('''
        (p / possible-01
            :ARG1 (g / go-02
                :ARG0 (i / i)
                :purpose (r / run-01
                    :ARG0 i)))
        ''',
        tokens=['I', 'might', 'go', 'for', 'a', 'run', '.'])
        alignments = AMR_Alignment_Set(amr)
        alignments.align(tokens=[0], nodes=['i'])
        alignments.align(tokens=[1], nodes=['p'])
        alignments.align(tokens=[2], nodes=['g'])
        alignments.align(tokens=[3], edges=[('g', ':purpose', 'r')])
        alignments.align(tokens=[5], nodes=['r'])

        align = alignments.find_nonprojective_alignment()
        correct = AMR_Alignment(tokens=[1], nodes=['p'])
        if align != correct:
            raise Exception('Failed to find non-projective alignments.')

        if alignments.is_projective():
            raise Exception('Failed to find non-projective alignments.')

        # control
        if self.alignments.is_projective():
            raise Exception('Failed to find non-projective alignments.')

        # test cycle
        amr = AMR.from_string('''
        # ::tok The quick brown fox jumped over the lazy dog .
        (j / jump-03
            :ARG0 (f / fox
                :ARG1-of (q / quick-02)
                :mod (b / brown))
            :ARG2 (d / dog
                :mod (l / lazy)))
        ''')
        alignments = AMR_Alignment_Set(amr)
        alignments.align(tokens=[1], nodes=['q'])
        alignments.align(tokens=[2], nodes=['b'])
        alignments.align(tokens=[3], nodes=['f'])
        alignments.align(tokens=[4], nodes=['j'])
        alignments.align(tokens=[5], edges=[('j', ':ARG2', 'd')])
        alignments.align(tokens=[7], nodes=['l'])
        alignments.align(tokens=[8], nodes=['d'])

        if not alignments.is_projective():
            raise Exception('Failed to find non-projective alignments.')

        # test cycle
        amr = AMR.from_string('''
        # ::tok I love the person who loves that I love them
        (l / love-01
            :ARG0 (i / i)
            :ARG1 (p / person
                :ARG0-of (l2 / love-01
                    :ARG1 l)))
                ''')
        alignments = AMR_Alignment_Set(amr)
        alignments.align(tokens=[0], nodes=['i'])
        alignments.align(tokens=[1], nodes=['l'])
        alignments.align(tokens=[3], nodes=['p'])
        alignments.align(tokens=[5], nodes=['l2'])

        if not alignments.is_projective():
            raise Exception('Failed to find non-projective alignments.')

    def test_leamr_alignments(self):
        # reader = Graph_Metadata_AMR_Reader()
        # amrs = reader.load(LEAMR_AMRS)
        #
        # with open(LEAMR_FILE) as fr:
        #     json_data = json.load(fr)
        #
        # for amr in amrs:
        #     alignments = AMR_Alignment_Set.from_json(amr, json_data[amr.id])
        #     if not alignments.is_projective():
        #         print('Non-projective alignment')
        #     if not alignments.is_connected():
        #         print('Disconnected alignment')
        raise NotImplementedError()


if __name__ == '__main__':
    unittest.main()
