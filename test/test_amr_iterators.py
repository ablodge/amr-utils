import unittest

from amr_utils.amr_iterators import *
from amr_utils.amr_iterators import _depth_first_edges, _breadth_first_edges
from amr_utils.amr_readers import AMR_Reader

TEST_FILE1 = 'test_data/test_amrs.txt'
TEST_FILE2 = 'test_data/test_amrs2.txt'

LDC_DIR = '../../LDC_2020/data/amrs/unsplit'


class Test_AMR_Iterators(unittest.TestCase):
    reader = AMR_Reader()
    ldc_amrs = reader.load_dir(LDC_DIR, quiet=True)

    def test_depth_first(self):
        reader = AMR_Reader()
        amrs = reader.load(TEST_FILE1, quiet=True)
        amrs2 = reader.load(TEST_FILE2, quiet=True)

        # test run
        for amr in amrs:
            for e in _depth_first_edges(amr):
                pass

        # test ordering
        correct = [(1, ('j', ':ARG0', 'f')), (2, ('f', ':ARG1-of', 'q')), (2, ('f', ':mod', 'b')),
                   (1, ('j', ':ARG2', 'd')), (2, ('d', ':mod', 'l')), ]
        # (j / jump-03 :ARG0 (f / fox
        # 		:ARG1-of (q / quick-02)
        # 		:mod (b / brown))
        # 	:ARG2 (d / dog :mod (l / lazy)))
        test = [(d, e) for d, i, e in _depth_first_edges(amrs[1])]
        if test != correct:
            raise Exception('Incorrect order')
        correct = [(1, ('f', ':ARG1-of', 'q')), (1, ('f', ':mod', 'b'))]
        # (j / jump-03 :ARG0 (f / fox
        # 		:ARG1-of (q / quick-02)
        # 		:mod (b / brown))
        # 	:ARG2 (d / dog :mod (l / lazy)))
        test = [(d, e) for d, i, e in _depth_first_edges(amrs[1], start_node='f')]
        if test != correct:
            raise Exception('Incorrect order')

        # alphabetical edges
        correct = [(1, ('l', ':ARG0', 'p')), (2, ('p', ':mod', 'e')), (1, ('l', ':ARG1', 'p'))]
        # (l / love-01
        # 	:ARG1 (p / person
        #         :mod (e / every))
        #     :ARG0 p)
        test = [(d, e) for d, i, e in _depth_first_edges(amrs2[4])]
        if test != correct:
            raise Exception('Incorrect order')

        # ignore reentrancies
        correct = [(1, ('w', ':ARG0', 'b')), (1, ('w', ':ARG1', 'g')), (2, ('g', ':ARG4', 'c')),
                   (3, ('c', ':name', 'n')), (4, ('n', ':op1', 'x0')), (4, ('n', ':op2', 'x1')),
                   (4, ('n', ':op3', 'x2'))]
        # (w / want-01 :ARG0 (b / boy)
        # 	:ARG1 (g / go-02 :ARG0 b
        # 		:ARG4 (c / city :name (n / name :op1 "New"
        # 			:op2 "York"
        # 			:op3 "City"))))
        test = [(d, e) for d, i, e in _depth_first_edges(amrs[0], ignore_reentrancies=True)]
        if test != correct:
            raise Exception('Incorrect output')

        # cycles
        correct = [(1, ('l', ':ARG0', 'i')), (1, ('l', ':ARG1', 'p')), (2, ('p', ':ARG0-of', 'l2')),
                   (3, ('l2', ':ARG1', 'l'))]
        # (l / love-01 :ARG0 (i / i)
        # 	:ARG1 (p / person
        # 	    :ARG0-of (l2 / love-01
        # 	        :ARG1 l)))
        test = [(d, e) for d, i, e in _depth_first_edges(amrs[3])]
        if test != correct:
            raise Exception('Mishandled cycle')
        correct = [(1, ('l2', ':ARG1', 'l')), (2, ('l', ':ARG0', 'i')), (2, ('l', ':ARG1', 'p')),
                   (3, ('p', ':ARG0-of', 'l2'))]
        # (l / love-01 :ARG0 (i / i)
        # 	:ARG1 (p / person
        # 	    :ARG0-of (l2 / love-01
        # 	        :ARG1 l)))
        test = [(d, e) for d, i, e in _depth_first_edges(amrs[3], start_node='l2')]
        if test != correct:
            raise Exception('Mishandled cycle')

        # thorough number test
        for amr in self.ldc_amrs:
            edges_ = []
            for _, _, e in _depth_first_edges(amr):
                edges_.append(e)
            if len(amr.edges) != len(edges_):
                raise Exception('Number of edges mismatched:', amr.id)

    def test_breadth_first(self):
        reader = AMR_Reader()
        amrs = reader.load(TEST_FILE1, quiet=True)
        amrs2 = reader.load(TEST_FILE2, quiet=True)

        # test run
        for amr in amrs:
            for e in _breadth_first_edges(amr):
                pass

        # test ordering
        correct = [(1, ('j', ':ARG0', 'f')), (1, ('j', ':ARG2', 'd')), (2, ('f', ':ARG1-of', 'q')),
                   (2, ('f', ':mod', 'b')), (2, ('d', ':mod', 'l'))]
        # (j / jump-03 :ARG0 (f / fox
        # 		:ARG1-of (q / quick-02)
        # 		:mod (b / brown))
        # 	:ARG2 (d / dog :mod (l / lazy)))
        test = [(d, e) for d, i, e in _breadth_first_edges(amrs[1])]
        if test != correct:
            raise Exception('Incorrect order')
        correct = [(1, ('f', ':ARG1-of', 'q')), (1, ('f', ':mod', 'b'))]
        # (j / jump-03 :ARG0 (f / fox
        # 		:ARG1-of (q / quick-02)
        # 		:mod (b / brown))
        # 	:ARG2 (d / dog :mod (l / lazy)))
        test = [(d, e) for d, i, e in _breadth_first_edges(amrs[1], start_node='f')]
        if test != correct:
            raise Exception('Incorrect order')

        # alphabetical edges
        correct = [(1, ('l', ':ARG0', 'p')), (1, ('l', ':ARG1', 'p')), (2, ('p', ':mod', 'e'))]
        # (l / love-01
        #   :ARG1 (p / person
        #       :mod (e / every))
        #   :ARG0 p)
        test = [(d, e) for d, i, e in _breadth_first_edges(amrs2[4])]
        if test != correct:
            raise Exception('Incorrect order')
        correct = [(1, ('l', ':ARG1', 'p')), (1, ('l', ':ARG0', 'p')), (2, ('p', ':mod', 'e'))]
        test = [(d, e) for d, i, e in _breadth_first_edges(amrs2[4], preserve_shape=True)]
        if test != correct:
            raise Exception('Incorrect order')

        # ignore reentrancies
        correct = [(1, ('w', ':ARG0', 'b')), (1, ('w', ':ARG1', 'g')), (2, ('g', ':ARG4', 'c')),
                   (3, ('c', ':name', 'n')), (4, ('n', ':op1', 'x0')), (4, ('n', ':op2', 'x1')),
                   (4, ('n', ':op3', 'x2'))]
        # (w / want-01 :ARG0 (b / boy)
        # 	:ARG1 (g / go-02 :ARG0 b
        # 		:ARG4 (c / city :name (n / name :op1 "New"
        # 			:op2 "York"
        # 			:op3 "City"))))
        test = [(d, e) for d, i, e in _breadth_first_edges(amrs[0], ignore_reentrancies=True)]
        if test != correct:
            raise Exception('Incorrect output')

        # cycles
        correct = [(1, ('l', ':ARG0', 'i')), (1, ('l', ':ARG1', 'p')), (2, ('p', ':ARG0-of', 'l2')),
                   (3, ('l2', ':ARG1', 'l'))]
        # (l / love-01 :ARG0 (i / i)
        # 	:ARG1 (p / person
        # 	    :ARG0-of (l2 / love-01
        # 	        :ARG1 l)))
        test = [(d, e) for d, i, e in _breadth_first_edges(amrs[3])]
        if test != correct:
            raise Exception('Mishandled cycle')
        correct = [(1, ('l2', ':ARG1', 'l')), (2, ('l', ':ARG0', 'i')), (2, ('l', ':ARG1', 'p')),
                   (3, ('p', ':ARG0-of', 'l2'))]
        # (l / love-01 :ARG0 (i / i)
        # 	:ARG1 (p / person
        # 	    :ARG0-of (l2 / love-01
        # 	        :ARG1 l)))
        test = [(d, e) for d, i, e in _breadth_first_edges(amrs[3], start_node='l2')]
        if test != correct:
            raise Exception('Mishandled cycle')

        # thorough number test
        for amr in self.ldc_amrs:
            edges_ = []
            for _, _, e in _breadth_first_edges(amr):
                edges_.append(e)
            if len(amr.edges) != len(edges_):
                raise Exception('Number of edges mismatched:', amr.id)

    def test_nodes(self):
        reader = AMR_Reader()
        amrs = reader.load(TEST_FILE1, quiet=True)

        # test run
        for amr in amrs:
            for e in nodes(amr):
                pass

        # test ordering, breadth_first
        correct = ['j', 'f', 'd', 'q', 'b', 'l']
        # (j / jump-03 :ARG0 (f / fox
        # 		:ARG1-of (q / quick-02)
        # 		:mod (b / brown))
        # 	:ARG2 (d / dog :mod (l / lazy)))
        test = [n for n in nodes(amrs[1], breadth_first=True)]
        if test != correct:
            raise Exception('Incorrect order')

        # test ordering, depth_first
        correct = ['j', 'f', 'q', 'b', 'd', 'l']
        # (j / jump-03 :ARG0 (f / fox
        # 		:ARG1-of (q / quick-02)
        # 		:mod (b / brown))
        # 	:ARG2 (d / dog :mod (l / lazy)))
        test = [n for n in nodes(amrs[1], depth_first=True)]
        if test != correct:
            raise Exception('Incorrect order')

        # thorough number test
        for amr in self.ldc_amrs:
            nodes_ = []
            for n in nodes(amr, depth_first=True):
                nodes_.append(n)
            if len(amr.nodes) != len(nodes_):
                raise Exception('Number of nodes mismatched:', amr.id)

    def test_edges(self):
        reader = AMR_Reader()
        amrs = reader.load(TEST_FILE1, quiet=True)

        # test run
        for amr in amrs:
            for e in edges(amr):
                pass

        # test ordering, breadth_first
        correct = [('j', ':ARG0', 'f'), ('j', ':ARG2', 'd'), ('f', ':ARG1-of', 'q'), ('f', ':mod', 'b'),
                   ('d', ':mod', 'l'), ]
        # (j / jump-03 :ARG0 (f / fox
        # 		:ARG1-of (q / quick-02)
        # 		:mod (b / brown))
        # 	:ARG2 (d / dog :mod (l / lazy)))
        test = [e for e in edges(amrs[1], breadth_first=True)]
        if test != correct:
            raise Exception('Incorrect order')

        # test ordering, depth_first
        correct = [('j', ':ARG0', 'f'), ('f', ':ARG1-of', 'q'), ('f', ':mod', 'b'), ('j', ':ARG2', 'd'),
                   ('d', ':mod', 'l'), ]
        # (j / jump-03 :ARG0 (f / fox
        # 		:ARG1-of (q / quick-02)
        # 		:mod (b / brown))
        # 	:ARG2 (d / dog :mod (l / lazy)))
        test = [e for e in edges(amrs[1], depth_first=True)]
        if test != correct:
            raise Exception('Incorrect order')

        # thorough number test
        for amr in self.ldc_amrs:
            edges_ = []
            for e in edges(amr, depth_first=True):
                edges_.append(e)
            if len(amr.edges) != len(edges_):
                raise Exception('Number of edges mismatched:', amr.id)

    def test_attributes(self):
        reader = AMR_Reader()
        amrs = reader.load(TEST_FILE1, quiet=True)

        # test run
        for amr in amrs:
            for triple in attributes(amr):
                pass

        # test output
        correct = [('n', ':op1', '"New"'), ('n', ':op2', '"York"'), ('n', ':op3', '"City"')]
        # (w / want-01 :ARG0 (b / boy)
        # 	:ARG1 (g / go-02 :ARG0 b
        # 		:ARG4 (c / city :name (n / name :op1 "New"
        # 			:op2 "York"
        # 			:op3 "City"))))
        test = [triple for triple in attributes(amrs[0])]
        if test != correct:
            raise Exception('Incorrect output')

    def test_reentrencies(self):
        reader = AMR_Reader()
        amrs = reader.load(TEST_FILE1, quiet=True)

        # test run
        for amr in amrs:
            for n, e in reentrancies(amr):
                pass

        # test order
        correct = [('b', [('w', ':ARG0', 'b'), ('g', ':ARG0', 'b')])]
        # (w / want-01 :ARG0 (b / boy)
        # 	:ARG1 (g / go-02 :ARG0 b
        # 		:ARG4 (c / city :name (n / name :op1 "New"
        # 			:op2 "York"
        # 			:op3 "City"))))
        test = [(n, rs) for n, rs in reentrancies(amrs[0], depth_first=True)]
        if test != correct:
            raise Exception('Incorrect order')

        # test artifacts
        correct = [('p', [('l', ':ARG1', 'p'), ('l', ':ARG0', 'p')])]
        # (l / love-01
        #     :ARG0 p
        # 	:ARG1 (p / person
        #         :mod (e / every)))
        test = [(n, rs) for n, rs in reentrancies(amrs[4], preserve_shape=True)]
        if test != correct:
            raise Exception('Incorrect output')

        # test cycle
        correct = [('l', [('l2', ':ARG1', 'l')])]
        # (l / love-01 :ARG0 (i / i)
        # 	:ARG1 (p / person
        # 	    :ARG0-of (l2 / love-01
        # 	        :ARG1 l)))
        test = [(n, rs) for n, rs in reentrancies(amrs[3])]
        if test != correct:
            raise Exception('Mishandled cycle')

    def test_iterate_subgraphs(self):
        # single node
        special_desc = Subgraph_Pattern('*-91')
        for amr in self.ldc_amrs:
            for sub_amr in subgraphs_by_pattern(amr, special_desc):
                if len(sub_amr.edges) > 0:
                    raise Exception('Failed to iterate subgraphs.')
                if len(sub_amr.nodes) != 1:
                    raise Exception('Failed to iterate subgraphs.')
                if not sub_amr.nodes[sub_amr.root].endswith('-91'):
                    raise Exception('Failed to iterate subgraphs.')

        ne_desc = Subgraph_Pattern('* :name (name :op* *)')
        for amr in self.ldc_amrs:
            for sub_amr in subgraphs_by_pattern(amr, ne_desc):
                for s, r, t in edges(sub_amr, traverse_undirected_graph=True, breadth_first=True):
                    if not (r.startswith(':op') or r == ':name'):
                        raise Exception('Failed to iterate subgraphs.')
                if len(sub_amr.edges) < 2:
                    raise Exception('Failed to iterate subgraphs.')
                if 'name' not in [sub_amr.nodes[n] for n in sub_amr.nodes]:
                    raise Exception('Failed to iterate subgraphs.')

        org_desc = Subgraph_Pattern('have-org-role-91 :ARG* *')
        for amr in self.ldc_amrs:
            for sub_amr in subgraphs_by_pattern(amr, org_desc):
                if sub_amr.nodes[sub_amr.root] != 'have-org-role-91':
                    raise Exception('Failed to iterate subgraphs.')
                for s, r, t in sub_amr.edges:
                    if not r.startswith(':ARG'):
                        raise Exception('Failed to iterate subgraphs.')
                if len(sub_amr.edges) < 1:
                    raise Exception('Failed to iterate subgraphs.')

        # matches nodes labelled "and" or "or" along with their ":op" arguments
        conjunction_pattern = Subgraph_Pattern('(and|or :op* *)')
        for amr in self.ldc_amrs:
            for sub_amr in subgraphs_by_pattern(amr, conjunction_pattern):
                if sub_amr.nodes[sub_amr.root] not in ['and', 'or']:
                    raise Exception('Failed to iterate subgraphs.')
                for s, r, t in sub_amr.edges:
                    if not r.startswith(':op'):
                        raise Exception('Failed to iterate subgraphs.')
                if len(sub_amr.edges) < 1:
                    raise Exception('Failed to iterate subgraphs.')

        # matches subgraphs for countries beginning with "U"
        county_pattern = Subgraph_Pattern('(country :name (name :op1 "U* :op*? *))')
        for amr in self.ldc_amrs:
            for sub_amr in subgraphs_by_pattern(amr, county_pattern):
                if sub_amr.nodes[sub_amr.root] != 'country':
                    raise Exception('Failed to iterate subgraphs.')
                for s, r, t in edges(sub_amr, traverse_undirected_graph=True, breadth_first=True):
                    if not (r.startswith(':op') or r == ':name'):
                        raise Exception('Failed to iterate subgraphs.')
                if len(sub_amr.edges) < 2:
                    raise Exception('Failed to iterate subgraphs.')

    def test_named_entities(self):
        ner_tags = Counter()
        ner_types = defaultdict(Counter)
        for amr in self.ldc_amrs:
            taken = set()
            for ne_tag, attr, ne_amr in named_entities(amr):
                ner_tags[ne_tag] += 1
                ner_types[ne_tag][attr['type']] += 1
                if ne_amr.root in taken:
                    raise Exception('Failed to tag named entities')
                taken.add(ne_amr.root)
        if len(ner_tags) < 20:
            raise Exception('Failed to tag named entities')

    def test_traverse_undirected_graph(self):
        reader = AMR_Reader()
        amrs = reader.load(TEST_FILE1, quiet=True)
        amrs2 = reader.load(TEST_FILE2, quiet=True)

        # depth first
        amr = AMR.from_string('''
        (w / want-01 :ARG0 (b / boy)
            :ARG1 (g / go-02 :ARG0 b
                :ARG4 (c / city :name (n / name :op1 "New" 
                    :op2 "York" 
                    :op3 "City"))))
        ''')
        correct = [(1, ('c', ':ARG4-of', 'g')), (2, ('g', ':ARG0', 'b')), (3, ('b', ':ARG0-of', 'w')),
                   (4, ('w', ':ARG1', 'g')), (1, ('c', ':name', 'n')), (2, ('n', ':op1', 'x0')),
                   (2, ('n', ':op2', 'x1')), (2, ('n', ':op3', 'x2'))]
        test = [(d, e) for d, i, e in _depth_first_edges(amr, traverse_undirected_graph=True, start_node='c')]
        if test != correct:
            raise Exception('Incorrect order')

        # breadth first
        # test ordering
        correct = [(1, ('j', ':ARG0', 'f')), (1, ('j', ':ARG2', 'd')), (2, ('f', ':ARG1-of', 'q')),
                   (2, ('f', ':mod', 'b')), (2, ('d', ':mod', 'l')), ]
        # (j / jump-03 :ARG0 (f / fox
        # 		:ARG1-of (q / quick-02)
        # 		:mod (b / brown))
        # 	:ARG2 (d / dog :mod (l / lazy)))
        test = [(d, e) for d, i, e in _breadth_first_edges(amrs[1], traverse_undirected_graph=True)]
        if test != correct:
            raise Exception('Incorrect order')
        correct = [(1, ('f', ':ARG0-of', 'j')), (1, ('f', ':ARG1-of', 'q')), (1, ('f', ':mod', 'b')),
                   (2, ('j', ':ARG2', 'd')), (3, ('d', ':mod', 'l'))]
        # (j / jump-03 :ARG0 (f / fox
        # 		:ARG1-of (q / quick-02)
        # 		:mod (b / brown))
        # 	:ARG2 (d / dog :mod (l / lazy)))
        test = [(d, e) for d, i, e in _breadth_first_edges(amrs[1], traverse_undirected_graph=True, start_node='f')]
        if test != correct:
            raise Exception('Incorrect order')

        # alphabetical edges
        correct = [(1, ('l', ':ARG0', 'p')), (1, ('l', ':ARG1', 'p')), (2, ('p', ':mod', 'e'))]
        # (l / love-01
        # 	:ARG1 (p / person
        #         :mod (e / every))
        #     :ARG0 p)
        test = [(d, e) for d, i, e in _breadth_first_edges(amrs2[4], traverse_undirected_graph=True)]
        if test != correct:
            raise Exception('Incorrect order')

        # cycles
        correct = [(1, ('l', ':ARG0', 'i')), (1, ('l', ':ARG1', 'p')), (1, ('l', ':ARG1-of', 'l2')),
                   (2, ('p', ':ARG0-of', 'l2'))]
        # (l / love-01 :ARG0 (i / i)
        # 	:ARG1 (p / person
        # 	    :ARG0-of (l2 / love-01
        # 	        :ARG1 l)))
        test = [(d, e) for d, i, e in _breadth_first_edges(amrs[3], traverse_undirected_graph=True)]
        if test != correct:
            raise Exception('Mishandled cycle')
        correct = [(1, ('l2', ':ARG0', 'p')), (1, ('l2', ':ARG1', 'l')), (2, ('p', ':ARG1-of', 'l')),
                   (2, ('l', ':ARG0', 'i'))]
        # (l / love-01 :ARG0 (i / i)
        # 	:ARG1 (p / person
        # 	    :ARG0-of (l2 / love-01
        # 	        :ARG1 l)))
        test = [(d, e) for d, i, e in _breadth_first_edges(amrs[3], traverse_undirected_graph=True, start_node='l2')]
        if test != correct:
            raise Exception('Mishandled cycle')

        # thorough number test
        for amr in self.ldc_amrs:
            edges_ = []
            for _, _, e in _breadth_first_edges(amr, traverse_undirected_graph=True):
                edges_.append(e)
            if len(amr.edges) != len(edges_):
                raise Exception('Number of edges mismatched:', amr.id)

    def test_triples(self):
        amr = AMR.from_string('''
        (j / jump-03 :ARG0 (f / fox
                :ARG1-of (q / quick-02)
                :mod (b / brown))
            :ARG2 (d / dog :mod (l / lazy)))
        ''')
        correct = [('j', ':instance', 'jump-03'), ('j', ':ARG0', 'f'), ('f', ':instance', 'fox'), ('f', ':ARG1-of', 'q'),
                   ('q', ':instance', 'quick-02'), ('f', ':mod', 'b'), ('b', ':instance', 'brown'),
                   ('j', ':ARG2', 'd'), ('d', ':instance', 'dog'), ('d', ':mod', 'l'), ('l', ':instance', 'lazy')]
        test = [t for t in triples(amr, depth_first=True)]
        if test != correct:
            raise Exception('Failed to iterate triples')

        correct = [('j', ':instance', 'jump-03'), ('j', ':ARG0', 'f'), ('f', ':instance', 'fox'), ('j', ':ARG2', 'd'),
                   ('d', ':instance', 'dog'), ('f', ':ARG1-of', 'q'), ('q', ':instance', 'quick-02'), ('f', ':mod', 'b'),
                   ('b', ':instance', 'brown'), ('d', ':mod', 'l'), ('l', ':instance', 'lazy')]
        test = [t for t in triples(amr, breadth_first=True)]
        if test != correct:
            raise Exception('Failed to iterate triples')

        # cycles
        amr = AMR.from_string('''
        (l / love-01 :ARG0 (i / i)
            :ARG1 (p / person
                :ARG0-of (l2 / love-01
                    :ARG1 l)))
        ''')
        correct = [('l',':instance','love-01'), ('l', ':ARG0', 'i'), ('i',':instance','i'), ('l', ':ARG1', 'p'),
                   ('p',':instance','person'), ('p', ':ARG0-of', 'l2'), ('l2',':instance','love-01'),
                   ('l2', ':ARG1', 'l')]
        test = [t for t in triples(amr, depth_first=True)]
        if test != correct:
            raise Exception('Failed to iterate triples')

        for amr in self.ldc_amrs:
            correct = [t for d, t in amr.depth_first_triples()]
            test = [t for t in triples(amr, depth_first=True, preserve_shape=True)]
            if test != correct:
                raise Exception('Failed to iterate triples.')

    def test_instances(self):
        amr = AMR.from_string('''
                (j / jump-03 :ARG0 (f / fox
                        :ARG1-of (q / quick-02)
                        :mod (b / brown))
                    :ARG2 (d / dog :mod (l / lazy)))
                ''')

        correct = [('j', ':instance', 'jump-03'), ('f', ':instance', 'fox'), ('q', ':instance', 'quick-02'),
                   ('b', ':instance', 'brown'), ('d', ':instance', 'dog'), ('l', ':instance', 'lazy')]
        test = [n for n in instances(amr, depth_first=True)]
        if test != correct:
            raise Exception('Incorrect order')

        # test ordering, depth_first
        correct = [('j', ':instance', 'jump-03'), ('f', ':instance', 'fox'), ('d', ':instance', 'dog'),
                   ('q', ':instance', 'quick-02'), ('b', ':instance', 'brown'), ('l', ':instance', 'lazy')]
        test = [n for n in instances(amr, breadth_first=True)]
        if test != correct:
            raise Exception('Incorrect order')

    def test_subgraph_params(self):
        amr = AMR.from_string('''
        (h / hear-01
            :ARG0 (i / i)
            :ARG1 (j / jump-03 
                :ARG0 (f / fox
                    :ARG1-of (q / quick-02)
                    :mod (b / brown))
                :ARG2 (d / dog 
                    :mod (l / lazy))))
        ''')
        correct = [('j', ':ARG0', 'f'), ('f', ':ARG1-of', 'q'), ('f', ':mod', 'b'),
                   ('j', ':ARG2', 'd'), ('d', ':mod', 'l')]

        # edges
        correct = [('j', ':ARG0', 'f'), ('j', ':ARG2', 'd'), ('f', ':ARG1-of', 'q'), ('f', ':mod', 'b'),
                   ('d', ':mod', 'l')]
        test = [e for e in edges(amr, breadth_first=True, subgraph_root='j')]
        if test != correct:
            raise Exception('Incorrect order')

        correct = [('j', ':ARG0', 'f'), ('f', ':ARG1-of', 'q'), ('f', ':mod', 'b'), ]
        test = [e for e in edges(amr, breadth_first=True, subgraph_edges=[e for e in amr.edges if 'f' in e])]
        if test != correct:
            raise Exception('Incorrect order')

        # nodes
        correct = ['j', 'f', 'd', 'q', 'b', 'l']
        test = [n for n in nodes(amr, breadth_first=True, subgraph_root='j')]
        if test != correct:
            raise Exception('Incorrect order')

        correct = ['j', 'f', 'd', 'q']
        test = [n for n in nodes(amr, breadth_first=True, subgraph_nodes=['q', 'j', 'f', 'd'])]
        if test != correct:
            test = [n for n in nodes(amr, breadth_first=True, subgraph_nodes=['q', 'j', 'f', 'd'])]
            raise Exception('Incorrect order')

        # triples
        correct = [('j', ':instance', 'jump-03'), ('j', ':ARG0', 'f'), ('f', ':instance', 'fox'),
                   ('j', ':ARG2', 'd'), ('d', ':instance', 'dog'), ('f', ':ARG1-of', 'q'),
                   ('q', ':instance', 'quick-02'),
                   ('f', ':mod', 'b'), ('b', ':instance', 'brown'),
                   ('d', ':mod', 'l'), ('l', ':instance', 'lazy'), ]
        test = [e for e in triples(amr, breadth_first=True, subgraph_root='j')]
        if test != correct:
            raise Exception('Incorrect order')
        correct = [('j', ':instance', 'jump-03'), ('j', ':ARG0', 'f'), ('f', ':instance', 'fox'),
                   ('f', ':ARG1-of', 'q'), ('q', ':instance', 'quick-02'), ('f', ':mod', 'b'),
                   ('b', ':instance', 'brown')]
        test = [e for e in triples(amr, breadth_first=True, subgraph_edges=[e for e in amr.edges if 'f' in e])]
        if test != correct:
            raise Exception('Incorrect order')
        correct = [('j', ':instance', 'jump-03'), ('j', ':ARG0', 'f'), ('f', ':instance', 'fox'),
                   ('f', ':ARG1-of', 'q'), ('q', ':instance', 'quick-02'), ('f', ':mod', 'b'),
                   ('b', ':instance', 'brown')]
        test = [e for e in triples(amr, breadth_first=True, subgraph_nodes=['j', 'f', 'q', 'b'])]
        if test != correct:
            raise Exception('Incorrect order')

        # traverse graph
        correct = [('j', ':ARG0', 'f'), ('f', ':ARG1-of', 'q'), ('f', ':mod', 'b'),
                   ('j', ':ARG2', 'd'), ('d', ':mod', 'l'), ('j', ':ARG1-of', 'h'), ('h', ':ARG0', 'i')]
        test = [e for e in edges(amr, subgraph_root='j', traverse_undirected_graph=True, depth_first=True)]
        if test != correct:
            raise Exception('Incorrect order')
        correct = [('f', ':ARG0-of', 'j'), ('f', ':ARG1-of', 'q'), ('f', ':mod', 'b'), ]
        test = [e for e in edges(amr, subgraph_root='f', depth_first=True,
                                    subgraph_edges=[e for e in amr.edges if 'f' in e],
                                    traverse_undirected_graph=True)]
        if test != correct:
            raise Exception('Incorrect order')
        correct = [('j', ':ARG0', 'f'), ('j', ':ARG2', 'd'), ('j', ':ARG1-of', 'h'), ('f', ':ARG1-of', 'q'),
                   ('f', ':mod', 'b'), ('d', ':mod', 'l'), ('h', ':ARG0', 'i')]
        test = [e for e in edges(amr, breadth_first=True, subgraph_root='j', traverse_undirected_graph=True)]
        if test != correct:
            raise Exception('Incorrect order')
        correct = [('f', ':ARG0-of', 'j'), ('f', ':ARG1-of', 'q'), ('f', ':mod', 'b'), ]
        test = [e for e in edges(amr, breadth_first=True, subgraph_root='f',
                                    subgraph_edges=[e for e in amr.edges if 'f' in e],
                                    traverse_undirected_graph=True)]
        if test != correct:
            raise Exception('Incorrect order')

    def test_missing_concept(self):
        amr = AMR.from_string('''
        (w / want-01 :ARG0 (b / boy)
            :ARG1 (g / go-02 :ARG0 b
                :ARG4 (c / city :name (n / name :op1 "New" 
                    :op2 "York" 
                    :op3 "City"))))
        ''')
        del amr.nodes['g']
        for e in edges(amr, depth_first=True):
            pass

        with self.assertWarns(Warning):
            for n in nodes(amr):
                pass
        with self.assertWarns(Warning):
            for n in nodes(amr, depth_first=True):
                pass
        with self.assertWarns(Warning):
            for n in nodes(amr, breadth_first=True):
                pass

        with self.assertWarns(Warning):
            for n, es in reentrancies(amr):
                pass

        with self.assertWarns(Warning):
            for tr in triples(amr, breadth_first=True):
                pass

        with self.assertWarns(Warning):
            for _, _, sub_amr in named_entities(amr):
                pass

        with self.assertWarns(Warning):
            sub_amrs = [sub_amr for sub_amr in subgraphs_by_pattern(amr, 'want-01 :ARG* *')]
            if len(sub_amrs) != 1:
                raise Exception('Failed to iterate subgraphs')
            if len(sub_amrs[0].edges) != 2:
                raise Exception('Failed to iterate subgraphs')


if __name__ == '__main__':
    unittest.main()
