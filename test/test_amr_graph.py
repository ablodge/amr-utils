import random
import unittest

from amr_utils import amr_graph
from amr_utils.amr import AMR
from amr_utils.amr_iterators import depth_first_edges
from amr_utils.amr_readers import AMR_Reader

TEST_FILE1 = 'test_data/test_amrs.txt'
TEST_FILE2 = 'test_data/test_amrs2.txt'

LDC_DIR = '../../LDC_2020/data/amrs/unsplit'


class Test_Graph_Utils(unittest.TestCase):
    reader = AMR_Reader()
    ldc_amrs = reader.load_dir(LDC_DIR, quiet=True)

    def test_reachable_nodes(self):

        amr = AMR.from_string('''
        (w / want-01 :ARG0 (b / boy)
            :ARG1 (g / go-02 :ARG0 b
                :ARG4 (c / city :name (n / name :op1 "New" 
                    :op2 "York" 
                    :op3 "City"))))
        ''')
        test = amr_graph._get_reachable_nodes(amr)
        correct = {'w': {'w', 'x0', 'c', 'x1', 'n', 'x2', 'b', 'g'},
                   'b': {'b'}, 'g': {'x0', 'c', 'x1', 'n', 'x2', 'b', 'g'},
                   'c': {'x0', 'c', 'x1', 'n', 'x2'},
                   'n': {'x1', 'n', 'x2', 'x0'}, 'x0': {'x0'}, 'x1': {'x1'}, 'x2': {'x2'}}
        if test != correct:
            raise Exception('Failed to find reachable nodes')
        test = amr_graph._get_reachable_nodes(amr, undirected_graph=True)
        correct = {'w', 'x0', 'c', 'x1', 'n', 'x2', 'b', 'g'}
        for n in test:
            if test[n] != correct:
                raise Exception('Failed to find reachable nodes')

        # test cycle
        amr = AMR.from_string('''
        (l / love-01
            :ARG0 (i / i)
            :ARG1 (p / person
                :ARG0-of (l2 / love-01
                    :ARG1 l)))
        ''')
        test = amr_graph._get_reachable_nodes(amr)
        correct = {'l': {'l', 'i', 'p', 'l2'},
                   'i': {'i'},
                   'p': {'l', 'i', 'p', 'l2'},
                   'l2': {'l', 'i', 'p', 'l2'}}
        if test != correct:
            raise Exception('Failed to find reachable nodes')
        test = amr_graph._get_reachable_nodes(amr, undirected_graph=True)
        correct = {'l', 'i', 'p', 'l2'}
        for n in test:
            if test[n] != correct:
                raise Exception('Failed to find reachable nodes')

        # through test
        for amr in self.ldc_amrs:
            amr_graph._get_reachable_nodes(amr)
            random.shuffle(amr.edges)
            test = amr_graph._get_reachable_nodes(amr, undirected_graph=True)
            correct = set(amr.nodes)
            for n in test:
                if test[n] != correct:
                    raise Exception()

    def test_process_subgraph(self):
        amr = AMR.from_string('''
            (w / want-01 :ARG0 (b / boy)
                :ARG1 (g / go-02 :ARG0 b
                    :ARG4 (c / city :name (n / name :op1 "New" 
                        :op2 "York" 
                        :op3 "City"))))
            ''')
        # default output
        root, nodes, edges = amr_graph.process_subgraph(amr)
        correct = (amr.root, set(amr.nodes), amr.edges)
        if (root, nodes, edges) != correct:
            raise Exception('Failed to process subgraph')
        # root only
        root, nodes, edges = amr_graph.process_subgraph(amr, subgraph_root='g')
        correct = ('g', {'g', 'c', 'b', 'n', 'x0', 'x1', 'x2'},
                   [('g', ':ARG0', 'b'), ('g', ':ARG4', 'c'), ('c', ':name', 'n'), ('n', ':op1', 'x0'),
                    ('n', ':op2', 'x1'), ('n', ':op3', 'x2')])
        if (root, nodes, edges) != correct:
            raise Exception('Failed to process subgraph')
        # nodes only
        root, nodes, edges = amr_graph.process_subgraph(amr, subgraph_nodes=['g', 'c'])
        correct = ('g', {'g', 'c'},
                   [('g', ':ARG4', 'c')])
        if (root, nodes, edges) != correct:
            raise Exception('Failed to process subgraph')
        # disconnected nodes
        root, nodes, edges = amr_graph.process_subgraph(amr, subgraph_nodes=['g', 'n'])
        correct = ({'g', 'n'}, [])
        if (nodes, edges) != correct:
            raise Exception('Failed to process subgraph')
        # edges only
        root, nodes, edges = amr_graph.process_subgraph(amr, subgraph_edges=[('g', ':ARG0', 'b'), ('g', ':ARG4', 'c'),
                                                                             ('c', ':name', 'n')])
        correct = ('g', {'g', 'c', 'b', 'n'},
                   [('g', ':ARG0', 'b'), ('g', ':ARG4', 'c'), ('c', ':name', 'n')])
        if (root, nodes, edges) != correct:
            raise Exception('Failed to process subgraph')
        # nodes and edges
        root, nodes, edges = amr_graph.process_subgraph(amr, subgraph_nodes=['g', 'n'],
                                                        subgraph_edges=[('g', ':ARG0', 'b'), ('g', ':ARG4', 'c'),
                                                                        ('c', ':name', 'n')])
        correct = ({'g', 'n'},
                   [('g', ':ARG0', 'b'), ('g', ':ARG4', 'c'), ('c', ':name', 'n')])
        if (nodes, edges) != correct:
            raise Exception('Failed to process subgraph')
        # root and nodes
        root, nodes, edges = amr_graph.process_subgraph(amr, subgraph_nodes=['g', 'c'], subgraph_root='c')
        correct = ('c', {'g', 'c'},
                   [('g', ':ARG4', 'c')])
        if (root, nodes, edges) != correct:
            raise Exception('Failed to process subgraph')
        # root and edges
        root, nodes, edges = amr_graph.process_subgraph(amr, subgraph_root='c',
                                                        subgraph_edges=[('g', ':ARG0', 'b'), ('g', ':ARG4', 'c'),
                                                                        ('c', ':name', 'n')])
        correct = ('c', {'c', 'b', 'g', 'n'},
                   [('g', ':ARG0', 'b'), ('g', ':ARG4', 'c'), ('c', ':name', 'n')])
        if (root, nodes, edges) != correct:
            raise Exception('Failed to process subgraph')
        # handle cycles
        amr = AMR.from_string('''
            (l / love-01
                :ARG0 (i / i)
                :ARG1 (p / person
                    :ARG0-of (l2 / love-01
                        :ARG1 l)))
            ''')
        root, nodes, edges = amr_graph.process_subgraph(amr, subgraph_root='p')
        correct = ('p', {'p', 'l', 'l2', 'i'},
                   [('l', ':ARG0', 'i'), ('l', ':ARG1', 'p'), ('p', ':ARG0-of', 'l2'), ('l2', ':ARG1', 'l')])
        if (root, nodes, edges) != correct:
            raise Exception('Failed to process subgraph')
        root, nodes, edges = amr_graph.process_subgraph(amr, subgraph_nodes=['p', 'l', 'l2'])
        correct = ({'p', 'l', 'l2'},
                   [('l', ':ARG1', 'p'), ('p', ':ARG0-of', 'l2'), ('l2', ':ARG1', 'l')])
        if (nodes, edges) != correct:
            raise Exception('Failed to process subgraph')
        root, nodes, edges = amr_graph.process_subgraph(amr, subgraph_nodes=['p', 'l', 'l2', 'i'])
        correct = ({'p', 'l', 'l2', 'i'},
                   [('l', ':ARG0', 'i'), ('l', ':ARG1', 'p'), ('p', ':ARG0-of', 'l2'), ('l2', ':ARG1', 'l')])
        if (nodes, edges) != correct:
            raise Exception('Failed to process subgraph')

    def test_find_cycles(self):
        amr = AMR.from_string('''
                (l / love-01
                    :ARG0 (i / i)
                    :ARG1 (p / person
                        :ARG0-of (l2 / love-01
                            :ARG1 l)))
                ''')
        correct = [{'l', 'p', 'l2'}]
        test = amr_graph.find_cycles(amr)
        if test != correct:
            raise Exception('Failed to find cycles')
        # subgraph no cycle
        correct = []
        test = amr_graph.find_cycles(amr, subgraph_edges=[('l', ':ARG1', 'p'), ('p', ':ARG0-of', 'l2')])
        if test != correct:
            raise Exception('Failed to find cycles')

        # through test
        for amr in self.ldc_amrs:
            cycles = amr_graph.find_cycles(amr)
            for cycle in cycles:
                nodes = [n for n in cycle]
                start_node = nodes[0]
                edges = [(s, r, t) for s, r, t in amr.edges if s in nodes and t in nodes]
                reached_nodes = set()
                for _, e in depth_first_edges(amr, subgraph_root=start_node, subgraph_edges=edges):
                    s, r, t = e
                    reached_nodes.add(t)
                if reached_nodes != cycle:
                    raise Exception('Failed to traverse cycle')

    def test_is_directed_acyclic_graph(self):
        # has cycle
        amr = AMR.from_string('''
            (l / love-01
                :ARG0 (i / i)
                    :ARG1 (p / person
                        :ARG0-of (l2 / love-01
                            :ARG1 l)))
            ''')
        if amr_graph.is_directed_acyclic_graph(amr):
            raise Exception('AMR is not a DAG!')
        # wrong root
        amr = AMR.from_string('''
            (w / want-01 :ARG0 (b / boy)
                :ARG1 (g / go-02 :ARG0 b
                    :ARG4 (c / city :name (n / name :op1 "New" 
                        :op2 "York" 
                        :op3 "City"))))
        ''')
        amr.root = 'g'
        if amr_graph.is_directed_acyclic_graph(amr):
            raise Exception('AMR is not a DAG!')
        # disconnected
        amr = AMR.from_string('''
            (w / want-01 :ARG0 (b / boy)
                :ARG1 (g / go-02 :ARG0 b
                    :ARG4 (c / city :name (n / name :op1 "New" 
                        :op2 "York" 
                        :op3 "City"))))
            ''')
        amr.nodes['a'] = 'aardvark'
        amr.nodes['z'] = 'zebra'
        amr.edges.append(('a', ':prep-to', 'z'))
        if amr_graph.is_directed_acyclic_graph(amr):
            raise Exception('AMR is not a DAG!')
        # multiple roots
        amr = AMR.from_string('''
            (w / want-01 :ARG0 (b / boy)
                :ARG1 (g / go-02 :ARG0 b
                    :ARG4 (c / city :name (n / name :op1 "New" 
                        :op2 "York" 
                        :op3 "City"))))
            ''')
        amr.nodes['a'] = 'aardvark'
        amr.edges.append(('a', ':mod', 'b'))
        if amr_graph.is_directed_acyclic_graph(amr):
            raise Exception('AMR is not a DAG!')
        # DAG
        amr = AMR.from_string('''
            (w / want-01 :ARG0 (b / boy)
                :ARG1 (g / go-02 :ARG0 b
                    :ARG4 (c / city :name (n / name :op1 "New" 
                        :op2 "York" 
                        :op3 "City"))))
            ''')
        if not amr_graph.is_directed_acyclic_graph(amr):
            raise Exception('AMR is a DAG!')
        # subgraph non-DAG
        amr = AMR.from_string('''
            (l / love-01
                :ARG0 (i / i)
                :ARG1 (p / person
                    :ARG0-of (l2 / love-01
                        :ARG1 l)))
            ''')
        if amr_graph.is_directed_acyclic_graph(amr, subgraph_root='p', subgraph_edges=[('l', ':ARG1', 'p'),
                                                                                       ('p', ':ARG0-of', 'l2'),
                                                                                       ('l2', ':ARG1', 'l')]):
            raise Exception('AMR is not a DAG!')
        # subgraph DAG
        if not amr_graph.is_directed_acyclic_graph(amr, subgraph_root='p', subgraph_edges=[('l2', ':ARG1', 'l'),
                                                                                           ('p', ':ARG0-of', 'l2')]):
            raise Exception('AMR is a DAG!')
        if not amr_graph.is_directed_acyclic_graph(amr, subgraph_nodes=['p', 'l2']):
            raise Exception('AMR is a DAG!')

        # through test
        for amr in self.ldc_amrs:
            cycles = amr_graph.find_cycles(amr)
            if not amr_graph.is_directed_acyclic_graph(amr):
                if not cycles:
                    raise Exception('Failed to evaluate DAG')
            elif cycles:
                raise Exception('Failed to evaluate DAG')

    def test_has_cycles(self):
        # has cycle
        amr = AMR.from_string('''
            (l / love-01
                :ARG0 (i / i)
                    :ARG1 (p / person
                        :ARG0-of (l2 / love-01
                            :ARG1 l)))
            ''')
        if not amr_graph.has_cycles(amr):
            raise Exception('AMR has a cycle!')
        # no cycle
        amr = AMR.from_string('''
            (w / want-01 :ARG0 (b / boy)
                :ARG1 (g / go-02 :ARG0 b
                    :ARG4 (c / city :name (n / name :op1 "New" 
                        :op2 "York" 
                        :op3 "City"))))
            ''')
        if amr_graph.has_cycles(amr):
            raise Exception('AMR does not have a cycle!')
        # subgraph cycle
        amr = AMR.from_string('''
                    (l / love-01
                        :ARG0 (i / i)
                            :ARG1 (p / person
                                :ARG0-of (l2 / love-01
                                    :ARG1 l)))
                    ''')
        if not amr_graph.has_cycles(amr, subgraph_edges=[('l', ':ARG1', 'p'), ('p', ':ARG0-of', 'l2'),
                                                         ('l2', ':ARG1', 'l')]):
            raise Exception('AMR has a cycle!')
        # subgraph no cycle
        if amr_graph.has_cycles(amr, subgraph_edges=[('l', ':ARG1', 'p'), ('p', ':ARG0-of', 'l2')]):
            raise Exception('AMR does not have a cycle!')
        # through test
        for amr in self.ldc_amrs:
            cycles = amr_graph.find_cycles(amr)
            if amr_graph.has_cycles(amr):
                if not cycles:
                    raise Exception('Failed to test cycles')
            elif cycles:
                raise Exception('Failed to test cycles')

    def test_get_subgraph(self):
        amr = AMR.from_string('''
                    (w / want-01 :ARG0 (b / boy)
                        :ARG1 (g / go-02 :ARG0 b
                            :ARG4 (c / city :name (n / name :op1 "New" 
                                :op2 "York" 
                                :op3 "City"))))
                    ''')
        # empty subgraph
        sg_amr = amr_graph.get_subgraph(amr, subgraph_nodes=[], subgraph_edges=[])
        if sg_amr.root or sg_amr.nodes or sg_amr.edges:
            raise Exception('Failed to get subgraph')
        # root only
        sg_amr = amr_graph.get_subgraph(amr, subgraph_root='g')
        correct = ('g', {'g', 'c', 'b', 'n', 'x0', 'x1', 'x2'},
                   [('g', ':ARG0', 'b'), ('g', ':ARG4', 'c'), ('c', ':name', 'n'), ('n', ':op1', 'x0'),
                    ('n', ':op2', 'x1'), ('n', ':op3', 'x2')])
        if sg_amr.root != correct[0] or set(sg_amr.nodes) != correct[1] or sg_amr.edges != correct[2]:
            raise Exception('Failed to get subgraph')
        # nodes only
        sg_amr = amr_graph.get_subgraph(amr, subgraph_nodes=['g', 'c'])
        correct = ('g', {'g', 'c'},
                   [('g', ':ARG4', 'c')])
        if sg_amr.root != correct[0] or set(sg_amr.nodes) != correct[1] or sg_amr.edges != correct[2]:
            raise Exception('Failed to get subgraph')

    def test_find_best_root(self):
        # cycle
        amr = AMR.from_string('''
            (l / love-01
                :ARG0 (i / i)
                :ARG1 (p / person
                    :ARG0-of (l2 / love-01
                        :ARG1 l)))
            ''')
        if amr_graph.find_best_root(amr) not in ['l', 'p', 'l2']:
            raise Exception('Failed to find root')
        if amr_graph.find_best_root(amr, subgraph_edges=[('p', ':ARG0-of', 'l2'), ('l2', ':ARG1', 'l')]) != 'p':
            raise Exception('Failed to find root')

        amr = AMR.from_string('''
            (w / want-01 :ARG0 (b / boy)    
                :ARG1 (g / go-02 :ARG0 b
                    :ARG4 (c / city :name (n / name :op1 "New" 
                        :op2 "York" 
                        :op3 "City"))))
            ''')
        if amr_graph.find_best_root(amr, subgraph_nodes=['g', 'b', 'n']) != 'g':
            raise Exception('Failed to find root')
        amr.nodes['a'] = 'aardvark'
        amr.nodes['z'] = 'zebra'
        amr.edges.append(('a', ':mod', 'z'))
        if amr_graph.find_best_root(amr) != 'w':
            raise Exception('Failed to find root')
        if amr_graph.find_best_root(amr, subgraph_nodes=['w', 'a', 'z']) != 'a':
            raise Exception('Failed to find root')

    def test_is_connected(self):
        # disconnected
        amr = AMR.from_string('''
            (w / want-01 :ARG0 (b / boy)
                :ARG1 (g / go-02 :ARG0 b
                    :ARG4 (c / city :name (n / name :op1 "New" 
                        :op2 "York" 
                        :op3 "City"))))
            ''')
        amr.nodes['a'] = 'aardvark'
        amr.nodes['z'] = 'zebra'
        amr.edges.append(('a', ':prep-to', 'z'))
        if amr_graph.is_connected(amr):
            raise Exception('AMR is not connected!')

        # undirected graph disconnected
        if amr_graph.is_connected(amr):
            raise Exception('AMR is not connected!')

        # disconnected subgraph
        amr = AMR.from_string('''
            (w / want-01 :ARG0 (b / boy)
                :ARG1 (g / go-02 :ARG0 b
                    :ARG4 (c / city :name (n / name :op1 "New" 
                        :op2 "York" 
                        :op3 "City"))))
            ''')
        if amr_graph.is_connected(amr, subgraph_nodes=['b', 'c']):
            raise Exception('AMR is not connected!')

        # connected subgraph
        if not amr_graph.is_connected(amr, subgraph_nodes=['b', 'g', 'c']):
            raise Exception('AMR is connected!')

        # multiple roots
        amr = AMR.from_string('''
            (w / want-01 :ARG0 (b / boy)
                :ARG1 (g / go-02 :ARG0 b
                    :ARG4 (c / city :name (n / name :op1 "New" 
                        :op2 "York" 
                        :op3 "City"))))
            ''')
        amr.nodes['a'] = 'aardvark'
        amr.edges.append(('a', ':mod', 'b'))
        if amr_graph.is_connected(amr):
            raise Exception('AMR is not connected!')

        # undirected graph connected
        if not amr_graph.is_connected(amr, undirected_graph=True):
            raise Exception('AMR is connected!')

        # cycle connected
        amr = AMR.from_string('''
            (l / love-01
                :ARG0 (i / i)
                :ARG1 (p / person
                    :ARG0-of (l2 / love-01
                        :ARG1 l)))
            ''')
        if not amr_graph.is_connected(amr, subgraph_nodes=['i', 'l', 'l2']):
            raise Exception('AMR is connected!')

    def test_find_connected_components(self):
        # connected
        amr = AMR.from_string('''
            (w / want-01 :ARG0 (b / boy)
                :ARG1 (g / go-02 :ARG0 b
                    :ARG4 (c / city :name (n / name :op1 "New" 
                        :op2 "York" 
                        :op3 "City"))))
            ''')
        correct = [[n for n in amr.nodes]]
        test = amr_graph.find_connected_components(amr)
        if len(correct) != len(test):
            raise Exception('Failed to find connected components.')
        for t, c in zip(test, correct):
            if not t[0] == c[0]:
                raise Exception('Failed to find connected components.')
            if set(t) != set(c):
                raise Exception('Failed to find connected components.')
        # disconnected
        amr = AMR.from_string('''
            (w / want-01 :ARG0 (b / boy)
                :ARG1 (g / go-02 :ARG0 b
                    :ARG4 (c / city :name (n / name :op1 "New" 
                        :op2 "York" 
                        :op3 "City"))))
            ''')
        amr.nodes['a'] = 'aardvark'
        amr.nodes['z'] = 'zebra'
        amr.edges.append(('a', ':prep-to', 'z'))
        correct = [['w', 'b', 'g', 'c', 'n', 'x0', 'x1', 'x2'], ['a', 'z']]
        test = amr_graph.find_connected_components(amr)
        if len(correct) != len(test):
            raise Exception('Failed to find connected components.')
        for t, c in zip(test, correct):
            if not t[0] == c[0]:
                raise Exception('Failed to find connected components.')
            if set(t) != set(c):
                raise Exception('Failed to find connected components.')
        test = amr_graph.find_connected_components(amr, undirected_graph=True)
        if len(correct) != len(test):
            raise Exception('Failed to find connected components.')
        for t, c in zip(test, correct):
            if set(t) != set(c):
                raise Exception('Failed to find connected components.')
        # multiple roots
        amr = AMR.from_string('''
            (w / want-01 :ARG0 (b / boy)
                :ARG1 (g / go-02 :ARG0 b
                    :ARG4 (c / city :name (n / name :op1 "New" 
                        :op2 "York" 
                        :op3 "City"))))
            ''')
        amr.nodes['a'] = 'aardvark'
        amr.edges.append(('a', ':mod', 'b'))
        correct = [['w', 'b', 'g', 'c', 'n', 'x0', 'x1', 'x2'], ['a']]
        test = amr_graph.find_connected_components(amr)
        if len(correct) != len(test):
            raise Exception('Failed to find connected components.')
        for t, c in zip(test, correct):
            if not t[0] == c[0]:
                raise Exception('Failed to find connected components.')
            if set(t) != set(c):
                raise Exception('Failed to find connected components.')
        correct = [['w', 'b', 'g', 'c', 'n', 'x0', 'x1', 'x2', 'a']]
        test = amr_graph.find_connected_components(amr, undirected_graph=True)
        if len(correct) != len(test):
            raise Exception('Failed to find connected components.')
        for t, c in zip(test, correct):
            if set(t) != set(c):
                raise Exception('Failed to find connected components.')
        # wrong root
        amr = AMR.from_string('''
            (w / want-01 :ARG0 (b / boy)
                :ARG1 (g / go-02 :ARG0 b
                    :ARG4 (c / city :name (n / name :op1 "New" 
                        :op2 "York" 
                        :op3 "City"))))
            ''')
        amr.root = 'g'
        correct = [['g', 'b', 'c', 'n', 'x0', 'x1', 'x2'], ['w']]
        test = amr_graph.find_connected_components(amr)
        if len(correct) != len(test):
            raise Exception('Failed to find connected components.')
        for t, c in zip(test, correct):
            if not t[0] == c[0]:
                raise Exception('Failed to find connected components.')
            if set(t) != set(c):
                raise Exception('Failed to find connected components.')
        # subgraph
        amr = AMR.from_string('''
            (w / want-01 :ARG0 (b / boy)
                :ARG1 (g / go-02 :ARG0 b
                    :ARG4 (c / city :name (n / name :op1 "New" 
                        :op2 "York" 
                        :op3 "City"))))
            ''')
        correct = [['w', 'g'], ['n', 'x0', 'x1', 'x2']]
        test = amr_graph.find_connected_components(amr, subgraph_nodes=['w', 'g', 'n', 'x0', 'x1', 'x2'])
        if len(correct) != len(test):
            raise Exception('Failed to find connected components.')
        for t, c in zip(test, correct):
            if not t[0] == c[0]:
                raise Exception('Failed to find connected components.')
            if set(t) != set(c):
                raise Exception('Failed to find connected components.')

    def test_break_into_connected_components(self):
        # disconnected
        amr = AMR.from_string('''
                    (w / want-01 :ARG0 (b / boy)
                        :ARG1 (g / go-02 :ARG0 b
                            :ARG4 (c / city :name (n / name :op1 "New" 
                                :op2 "York" 
                                :op3 "City"))))
                    ''')
        amr.nodes['a'] = 'aardvark'
        amr.nodes['z'] = 'zebra'
        amr.edges.append(('a', ':prep-to', 'z'))
        correct = [['w', 'b', 'g', 'c', 'n', 'x0', 'x1', 'x2'], ['a', 'z']]
        correct_edges2 = [('a',':prep-to','z')]
        amr_components = amr_graph.break_into_connected_components(amr)
        if len(correct) != len(amr_components):
            raise Exception('Failed to find connected components.')
        for sg_amr, c in zip(amr_components, correct):
            if sg_amr.root != c[0]:
                raise Exception('Failed to find connected components.')
            if set(sg_amr.nodes) != set(c):
                raise Exception('Failed to find connected components.')
        if amr_components[1].edges != correct_edges2:
            raise Exception('Failed to find connected components.')
        amr_components = amr_graph.break_into_connected_components(amr, undirected_graph=True)
        if len(correct) != len(amr_components):
            raise Exception('Failed to find connected components.')
        for sg_amr, c in zip(amr_components, correct):
            if sg_amr.root != c[0]:
                raise Exception('Failed to find connected components.')
            if set(sg_amr.nodes) != set(c):
                raise Exception('Failed to find connected components.')
        if amr_components[1].edges != correct_edges2:
            raise Exception('Failed to find connected components.')
        # multiple roots
        amr = AMR.from_string('''
                    (w / want-01 :ARG0 (b / boy)
                        :ARG1 (g / go-02 :ARG0 b
                            :ARG4 (c / city :name (n / name :op1 "New" 
                                :op2 "York" 
                                :op3 "City"))))
                    ''')
        amr.nodes['a'] = 'aardvark'
        amr.edges.append(('a', ':mod', 'b'))
        correct = [['w', 'b', 'g', 'c', 'n', 'x0', 'x1', 'x2'], ['a']]
        correct_edges2 = [('a', ':mod', 'b')]
        amr_components = amr_graph.break_into_connected_components(amr)
        if len(correct) != len(amr_components):
            raise Exception('Failed to find connected components.')
        for sg_amr, c in zip(amr_components, correct):
            if sg_amr.root != c[0]:
                raise Exception('Failed to find connected components.')
            if set(sg_amr.nodes) != set(c):
                raise Exception('Failed to find connected components.')
        if amr_components[1].edges != correct_edges2:
            raise Exception('Failed to find connected components.')
        correct = [['w', 'b', 'g', 'c', 'n', 'x0', 'x1', 'x2', 'a']]
        amr_components = amr_graph.break_into_connected_components(amr, undirected_graph=True)
        if len(correct) != len(amr_components):
            raise Exception('Failed to find connected components.')
        for sg_amr, c in zip(amr_components, correct):
            if sg_amr.root != c[0]:
                raise Exception('Failed to find connected components.')
            if set(sg_amr.nodes) != set(c):
                raise Exception('Failed to find connected components.')
        # wrong root
        amr = AMR.from_string('''
                    (w / want-01 :ARG0 (b / boy)
                        :ARG1 (g / go-02 :ARG0 b
                            :ARG4 (c / city :name (n / name :op1 "New" 
                                :op2 "York" 
                                :op3 "City"))))
                    ''')
        amr.root = 'g'
        correct = [['g', 'b', 'c', 'n', 'x0', 'x1', 'x2'], ['w']]
        correct_edges2 = [('w',':ARG0','b'), ('w',':ARG1','g')]
        amr_components = amr_graph.break_into_connected_components(amr)
        if len(correct) != len(amr_components):
            raise Exception('Failed to find connected components.')
        for sg_amr, c in zip(amr_components, correct):
            if sg_amr.root != c[0]:
                raise Exception('Failed to find connected components.')
            if set(sg_amr.nodes) != set(c):
                raise Exception('Failed to find connected components.')
        if amr_components[1].edges != correct_edges2:
            raise Exception('Failed to find connected components.')

        # thorough test
        for amr in self.ldc_amrs:
            amr = amr.copy()
            for _ in range(3):
                if amr.edges:
                    i = random.randint(0, len(amr.edges)-1)
                    amr.edges.pop(i)
            amr_components = amr_graph.break_into_connected_components(amr)
            total_edges = 0
            total_nodes = 0
            all_edges = set()
            all_nodes = set()
            for sg_amr in amr_components:
                total_edges += len(sg_amr.edges)
                total_nodes += len(sg_amr.nodes)
                all_edges.update(sg_amr.edges)
                all_nodes.update(sg_amr.nodes)
            if total_nodes != len(amr.nodes):
                raise Exception('Failed to find connected components.')
            if total_edges != len(amr.edges):
                raise Exception('Failed to find connected components.')
            if set(amr.nodes) != all_nodes:
                raise Exception('Failed to find connected components.')
            if set(amr.edges) != all_edges:
                raise Exception('Failed to find connected components.')

    def test_find_shortest_path(self):
        amr = AMR.from_string('''
            (w / want-01 :ARG0 (b / boy)
                :ARG1 (g / go-02 :ARG0 b
                    :ARG4 (c / city :name (n / name :op1 "New" 
                        :op2 "York" 
                        :op3 "City"))))
            ''')
        correct = ['g', 'c', 'n', 'x0']
        test = amr_graph.find_shortest_path(amr, 'g', 'x0')
        if test != correct:
            raise Exception('Failed to find path')
        test = amr_graph.find_shortest_path(amr, 'x0', 'g')
        if test is not None:
            raise Exception('Failed to find path')
        correct = ['b', 'g', 'c', 'n', 'x0']
        test = amr_graph.find_shortest_path(amr, 'b', 'x0', undirected_graph=True)
        if test != correct:
            raise Exception('Failed to find path')
        # cycle
        amr = AMR.from_string('''
            (l / love-01
                :ARG0 (i / i)
                :ARG1 (p / person
                    :ARG0-of (l2 / love-01
                        :ARG1 l)))
            ''')
        correct = ['p', 'l2', 'l', 'i']
        test = amr_graph.find_shortest_path(amr, 'p', 'i')
        if test != correct:
            raise Exception('Failed to find path')
        correct = ['p', 'l', 'i']
        test = amr_graph.find_shortest_path(amr, 'p', 'i', undirected_graph=True)
        if test != correct:
            raise Exception('Failed to find path')
        correct = ['p', 'l2', 'l', 'i']
        test = amr_graph.find_shortest_path(amr, 'p', 'i', undirected_graph=True,
                                            subgraph_edges=[('l', ':ARG0', 'i'), ('p', ':ARG0-of', 'l2'),
                                                            ('l2', ':ARG1', 'l')])
        if test != correct:
            raise Exception('Failed to find path')


if __name__ == '__main__':
    unittest.main()
