import unittest

from amr_utils.amr_iterators import *
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
            for e in depth_first_edges(amr):
                pass

        # test ordering
        correct = [(1, ('j', ':ARG0', 'f')), (2, ('f', ':ARG1-of', 'q')), (2, ('f', ':mod', 'b')),
                   (1, ('j', ':ARG2', 'd')), (2, ('d', ':mod', 'l')), ]
        # (j/jump-03 :ARG0 (f/fox
        # 		:ARG1-of (q/quick-02)
        # 		:mod (b/brown))
        # 	:ARG2 (d/dog :mod (l/lazy)))
        test = [e for e in depth_first_edges(amrs[1])]
        if test != correct:
            raise Exception('Incorrect order')
        correct = [(1, ('f', ':ARG1-of', 'q')), (1, ('f', ':mod', 'b'))]
        # (j/jump-03 :ARG0 (f/fox
        # 		:ARG1-of (q/quick-02)
        # 		:mod (b/brown))
        # 	:ARG2 (d/dog :mod (l/lazy)))
        test = [e for e in depth_first_edges(amrs[1], root='f')]
        if test != correct:
            raise Exception('Incorrect order')

        # alphabetical edges
        correct = [(1, ('l', ':ARG0', 'p')), (2, ('p', ':mod', 'e')), (1, ('l', ':ARG1', 'p'))]
        # (l/love-01
        # 	:ARG1 (p/person
        #         :mod (e/every))
        #     :ARG0 p)
        test = [e for e in depth_first_edges(amrs2[4], alphabetical_edges=True)]
        if test != correct:
            raise Exception('Incorrect order')

        # ignore reentrancies
        correct = [(1, ('w', ':ARG0', 'b')), (1, ('w', ':ARG1', 'g')), (2, ('g', ':ARG4', 'c')),
                   (3, ('c', ':name', 'n')), (4, ('n', ':op1', 'x0')), (4, ('n', ':op2', 'x1')),
                   (4, ('n', ':op3', 'x2'))]
        # (w/want-01 :ARG0 (b/boy)
        # 	:ARG1 (g/go-02 :ARG0 b
        # 		:ARG4 (c/city :name (n/name :op1 "New"
        # 			:op2 "York"
        # 			:op3 "City"))))
        test = [e for e in depth_first_edges(amrs[0], ignore_reentrancies=True)]
        if test != correct:
            raise Exception('Incorrect output')

        # cycles
        correct = [(1, ('l', ':ARG0', 'i')), (1, ('l', ':ARG1', 'p')), (2, ('p', ':ARG0-of', 'l2')), (3, ('l2', ':ARG1', 'l'))]
        # (l/love-01 :ARG0 (i/i)
        # 	:ARG1 (p/person
        # 	    :ARG0-of (l2/love-01
        # 	        :ARG1 l)))
        test = [e for e in depth_first_edges(amrs[3])]
        if test != correct:
            raise Exception('Mishandled cycle')
        correct = [(1, ('l2', ':ARG1', 'l')), (2, ('l', ':ARG0', 'i')), (2, ('l', ':ARG1', 'p')),
                   (3, ('p', ':ARG0-of', 'l2'))]
        # (l/love-01 :ARG0 (i/i)
        # 	:ARG1 (p/person
        # 	    :ARG0-of (l2/love-01
        # 	        :ARG1 l)))
        test = [e for e in depth_first_edges(amrs[3], root='l2')]
        if test != correct:
            raise Exception('Mishandled cycle')

        # thorough number test
        for amr in self.ldc_amrs:
            edges_ = []
            for _, e in depth_first_edges(amr):
                edges_.append(e)
            if len(amr.edges) != len(edges_):
                raise Exception('Number of edges mismatched:', amr.id)

    def test_breadth_first(self):
        reader = AMR_Reader()
        amrs = reader.load(TEST_FILE1, quiet=True)
        amrs2 = reader.load(TEST_FILE2, quiet=True)

        # test run
        for amr in amrs:
            for e in breadth_first_edges(amr):
                pass

        # test ordering
        correct = [(1, ('j', ':ARG0', 'f')), (1, ('j', ':ARG2', 'd')), (2, ('f', ':ARG1-of', 'q')),
                   (2, ('f', ':mod', 'b')), (2, ('d', ':mod', 'l'))]
        # (j/jump-03 :ARG0 (f/fox
        # 		:ARG1-of (q/quick-02)
        # 		:mod (b/brown))
        # 	:ARG2 (d/dog :mod (l/lazy)))
        test = [e for e in breadth_first_edges(amrs[1])]
        if test != correct:
            raise Exception('Incorrect order')
        correct = [(1, ('f', ':ARG1-of', 'q')), (1, ('f', ':mod', 'b'))]
        # (j/jump-03 :ARG0 (f/fox
        # 		:ARG1-of (q/quick-02)
        # 		:mod (b/brown))
        # 	:ARG2 (d/dog :mod (l/lazy)))
        test = [e for e in breadth_first_edges(amrs[1], root='f')]
        if test != correct:
            raise Exception('Incorrect order')

        # alphabetical edges
        correct = [(1, ('l', ':ARG0', 'p')), (1, ('l', ':ARG1', 'p')), (2, ('p', ':mod', 'e'))]
        # (l/love-01
        #   :ARG1 (p/person
        #       :mod (e/every))
        #   :ARG0 p)
        test = [e for e in breadth_first_edges(amrs2[4], alphabetical_edges=True)]
        if test != correct:
            raise Exception('Incorrect order')

        # ignore reentrancies
        correct = [(1, ('w', ':ARG0', 'b')), (1, ('w', ':ARG1', 'g')), (2, ('g', ':ARG4', 'c')),
                   (3, ('c', ':name', 'n')), (4, ('n', ':op1', 'x0')), (4, ('n', ':op2', 'x1')),
                   (4, ('n', ':op3', 'x2'))]
        # (w/want-01 :ARG0 (b/boy)
        # 	:ARG1 (g/go-02 :ARG0 b
        # 		:ARG4 (c/city :name (n/name :op1 "New"
        # 			:op2 "York"
        # 			:op3 "City"))))
        test = [e for e in breadth_first_edges(amrs[0], ignore_reentrancies=True)]
        if test != correct:
            raise Exception('Incorrect output')

        # cycles
        correct = [(1, ('l', ':ARG0', 'i')), (1, ('l', ':ARG1', 'p')), (2, ('p', ':ARG0-of', 'l2')),
                   (3, ('l2', ':ARG1', 'l'))]
        # (l/love-01 :ARG0 (i/i)
        # 	:ARG1 (p/person
        # 	    :ARG0-of (l2/love-01
        # 	        :ARG1 l)))
        test = [e for e in breadth_first_edges(amrs[3])]
        if test != correct:
            raise Exception('Mishandled cycle')
        correct = [(1, ('l2', ':ARG1', 'l')), (2, ('l', ':ARG0', 'i')), (2, ('l', ':ARG1', 'p')), (3, ('p', ':ARG0-of', 'l2'))]
        # (l/love-01 :ARG0 (i/i)
        # 	:ARG1 (p/person
        # 	    :ARG0-of (l2/love-01
        # 	        :ARG1 l)))
        test = [e for e in breadth_first_edges(amrs[3], root='l2')]
        if test != correct:
            raise Exception('Mishandled cycle')

        # thorough number test
        for amr in self.ldc_amrs:
            edges_ = []
            for _, e in breadth_first_edges(amr):
                edges_.append(e)
            if len(amr.edges) != len(edges_):
                raise Exception('Number of edges mismatched:', amr.id)

    def test_traverse(self):
        reader = AMR_Reader()
        amrs = reader.load(TEST_FILE1, quiet=True)
        amrs2 = reader.load(TEST_FILE2, quiet=True)

        # test run
        for amr in amrs:
            for e in traverse_graph(amr):
                pass

        # test ordering
        correct = [(1, ('j', ':ARG0', 'f')), (1, ('j', ':ARG2', 'd')), (2, ('f', ':ARG1-of', 'q')),
                   (2, ('f', ':mod', 'b')), (2, ('d', ':mod', 'l')),]
        # (j/jump-03 :ARG0 (f/fox
        # 		:ARG1-of (q/quick-02)
        # 		:mod (b/brown))
        # 	:ARG2 (d/dog :mod (l/lazy)))
        test = [e for e in traverse_graph(amrs[1])]
        if test != correct:
            raise Exception('Incorrect order')
        correct = [(1, ('f', ':ARG0-of', 'j')), (1, ('f', ':ARG1-of', 'q')), (1, ('f', ':mod', 'b')),
                   (2, ('j', ':ARG2', 'd')), (3, ('d', ':mod', 'l'))]
        # (j/jump-03 :ARG0 (f/fox
        # 		:ARG1-of (q/quick-02)
        # 		:mod (b/brown))
        # 	:ARG2 (d/dog :mod (l/lazy)))
        test = [e for e in traverse_graph(amrs[1], root='f')]
        if test != correct:
            raise Exception('Incorrect order')

        # alphabetical edges
        correct = [(1, ('l', ':ARG0', 'p')), (1, ('l', ':ARG1', 'p')), (2, ('p', ':mod', 'e'))]
        # (l/love-01
        # 	:ARG1 (p/person
        #         :mod (e/every))
        #     :ARG0 p)
        test = [e for e in traverse_graph(amrs2[4], alphabetical_edges=True)]
        if test != correct:
            raise Exception('Incorrect order')

        # cycles
        correct = [(1, ('l', ':ARG0', 'i')), (1, ('l', ':ARG1', 'p')), (1, ('l', ':ARG1-of', 'l2')),
                   (2, ('p', ':ARG0-of', 'l2'))]
        # (l/love-01 :ARG0 (i/i)
        # 	:ARG1 (p/person
        # 	    :ARG0-of (l2/love-01
        # 	        :ARG1 l)))
        test = [e for e in traverse_graph(amrs[3])]
        if test != correct:
            raise Exception('Mishandled cycle')
        correct = [(1, ('l2', ':ARG0', 'p')), (1, ('l2', ':ARG1', 'l')), (2, ('p', ':ARG1-of', 'l')),
                   (2, ('l', ':ARG0', 'i'))]
        # (l/love-01 :ARG0 (i/i)
        # 	:ARG1 (p/person
        # 	    :ARG0-of (l2/love-01
        # 	        :ARG1 l)))
        test = [e for e in traverse_graph(amrs[3], root='l2')]
        if test != correct:
            raise Exception('Mishandled cycle')

        # thorough number test
        for amr in self.ldc_amrs:
            edges_ = []
            for _, e in traverse_graph(amr):
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
        # (j/jump-03 :ARG0 (f/fox
        # 		:ARG1-of (q/quick-02)
        # 		:mod (b/brown))
        # 	:ARG2 (d/dog :mod (l/lazy)))
        test = [n for n in nodes(amrs[1], breadth_first=True)]
        if test != correct:
            raise Exception('Incorrect order')

        # test ordering, depth_first
        correct = ['j', 'f', 'q', 'b', 'd', 'l']
        # (j/jump-03 :ARG0 (f/fox
        # 		:ARG1-of (q/quick-02)
        # 		:mod (b/brown))
        # 	:ARG2 (d/dog :mod (l/lazy)))
        test = [n for n in nodes(amrs[1], depth_first=True)]
        if test != correct:
            raise Exception('Incorrect order')

        # test ignore_attributes
        correct = ['w', 'b', 'g', 'c', 'n']
        # (w/want-01 :ARG0 (b/boy)
        # 	:ARG1 (g/go-02 :ARG0 b
        # 		:ARG4 (c/city :name (n/name :op1 "New"
        # 			:op2 "York"
        # 			:op3 "City"))))
        test = [n for n in nodes(amrs[0], ignore_attributes=True, depth_first=True)]
        if test != correct:
            raise Exception('Incorrect output')

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
                   ('d', ':mod', 'l'),]
        # (j/jump-03 :ARG0 (f/fox
        # 		:ARG1-of (q/quick-02)
        # 		:mod (b/brown))
        # 	:ARG2 (d/dog :mod (l/lazy)))
        test = [e for e in edges(amrs[1], breadth_first=True)]
        if test != correct:
            raise Exception('Incorrect order')

        # test ordering, depth_first
        correct = [('j', ':ARG0', 'f'), ('f', ':ARG1-of', 'q'), ('f', ':mod', 'b'), ('j', ':ARG2', 'd'),
                  ('d', ':mod', 'l'), ]
        # (j/jump-03 :ARG0 (f/fox
        # 		:ARG1-of (q/quick-02)
        # 		:mod (b/brown))
        # 	:ARG2 (d/dog :mod (l/lazy)))
        test = [e for e in edges(amrs[1], depth_first=True)]
        if test != correct:
            raise Exception('Incorrect order')

        # test ignore_attributes
        correct = [('w', ':ARG0', 'b'), ('w', ':ARG1', 'g'), ('g', ':ARG0', 'b'), ('g', ':ARG4', 'c'),
                   ('c', ':name', 'n'),]
        # (w/want-01 :ARG0 (b/boy)
        # 	:ARG1 (g/go-02 :ARG0 b
        # 		:ARG4 (c/city :name (n/name :op1 "New"
        # 			:op2 "York"
        # 			:op3 "City"))))
        test = [e for e in edges(amrs[0], ignore_attributes=True, depth_first=True)]
        if test != correct:
            raise Exception('Incorrect output')

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
        # (w/want-01 :ARG0 (b/boy)
        # 	:ARG1 (g/go-02 :ARG0 b
        # 		:ARG4 (c/city :name (n/name :op1 "New"
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
        correct = [('b', ('w', ':ARG0', 'b')), ('b', ('g', ':ARG0', 'b'))]
        # (w/want-01 :ARG0 (b/boy)
        # 	:ARG1 (g/go-02 :ARG0 b
        # 		:ARG4 (c/city :name (n/name :op1 "New"
        # 			:op2 "York"
        # 			:op3 "City"))))
        test = [(n, e) for n, e in reentrancies(amrs[0], depth_first=True)]
        if test != correct:
            raise Exception('Incorrect order')

        # test artifacts
        correct = [('p', ('l', ':ARG1', 'p')), ('p', ('l', ':ARG0', 'p'))]
        # (l/love-01
        #     :ARG0 p
        # 	:ARG1 (p/person
        #         :mod (e/every)))
        test = [(n, e) for n, e in reentrancies(amrs[4])]
        if test != correct:
            raise Exception('Incorrect output')

        # test cycle
        correct = [('l', ('l2', ':ARG1', 'l'))]
        # (l/love-01 :ARG0 (i/i)
        # 	:ARG1 (p/person
        # 	    :ARG0-of (l2/love-01
        # 	        :ARG1 l)))
        test = [(n, e) for n, e in reentrancies(amrs[3])]
        if test != correct:
            raise Exception('Mishandled cycle')

    def test_triples(self):
        reader = AMR_Reader()
        amrs = reader.load(TEST_FILE1, quiet=True)

        # test run
        for amr in amrs:
            for triple in triples(amr):
                pass

        # test ordering, breadth_first
        correct = [('j', ':instance', 'jump-03'), ('j', ':ARG0', 'f'), ('f', ':instance', 'fox'),
                   ('j', ':ARG2', 'd'), ('d', ':instance', 'dog'), ('f', ':ARG1-of', 'q'),
                   ('q', ':instance', 'quick-02'), ('f', ':mod', 'b'), ('b', ':instance', 'brown'),
                   ('d', ':mod', 'l'), ('l', ':instance', 'lazy'), ]
        # (j/jump-03 :ARG0 (f/fox
        # 		:ARG1-of (q/quick-02)
        # 		:mod (b/brown))
        # 	:ARG2 (d/dog :mod (l/lazy)))
        test = [triple for triple in triples(amrs[1], breadth_first=True)]
        if test != correct:
            raise Exception('Incorrect order')

        # test ordering, depth_first
        correct = [('j', ':instance', 'jump-03'), ('j', ':ARG0', 'f'), ('f', ':instance', 'fox'),
                   ('f', ':ARG1-of', 'q'), ('q', ':instance', 'quick-02'), ('f', ':mod', 'b'),
                   ('b', ':instance', 'brown'), ('j', ':ARG2', 'd'), ('d', ':instance', 'dog'),
                   ('d', ':mod', 'l'), ('l', ':instance', 'lazy')]
        # (j/jump-03 :ARG0 (f/fox
        # 		:ARG1-of (q/quick-02)
        # 		:mod (b/brown))
        # 	:ARG2 (d/dog :mod (l/lazy)))
        test = [triple for triple in triples(amrs[1], depth_first=True)]
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
        test = [e for e in triples(amrs[0], depth_first=True)]
        if test != correct:
            raise Exception('Incorrect output')

        # handle artifacts
        correct = [('l', ':instance', 'love-01'), ('l', ':ARG0', 'p'), ('l', ':ARG1', 'p'),
                   ('p', ':instance', 'person'), ('p', ':mod', 'e'), ('e', ':instance', 'every')]
        # (l/love-01
        #     :ARG0 p
        # 	:ARG1 (p/person
        #         :mod (e/every)))
        test = [e for e in triples(amrs[4])]
        if test != correct:
            raise Exception('Incorrect output')



if __name__ == '__main__':
    unittest.main()