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
        root, nodes, edge = amr_graph.process_subgraph(amr)
        correct = (amr.root, set(amr.nodes), amr.edges)
        if (root, nodes, edge) != correct:
            raise Exception('Failed to process subgraph')
        root, nodes, edge = amr_graph.process_subgraph(amr, subgraph_root='g')
        correct = ('g', {'g', 'c', 'b', 'n', 'x0', 'x1', 'x2'},
                   [('g', ':ARG0', 'b'), ('g', ':ARG4', 'c'), ('c', ':name', 'n'), ('n', ':op1', 'x0'),
                    ('n', ':op2', 'x1'), ('n', ':op3', 'x2')])
        if (root, nodes, edge) != correct:
            raise Exception('Failed to process subgraph')
        root, nodes, edge = amr_graph.process_subgraph(amr, subgraph_nodes=['g', 'c'])
        correct = ('g', {'g', 'c'},
                   [('g', ':ARG0', 'b'), ('g', ':ARG4', 'c'), ('c', ':name', 'n')])
        if (root, nodes, edge) != correct:
            raise Exception('Failed to process subgraph')
        root, nodes, edge = amr_graph.process_subgraph(amr, subgraph_nodes=['g', 'n'])
        correct = ({'g', 'n'},
                   [('g', ':ARG0', 'b'), ('g', ':ARG4', 'c'), ('n', ':op1', 'x0'),
                    ('n', ':op2', 'x1'), ('n', ':op3', 'x2')])
        if (nodes, edge) != correct:
            raise Exception('Failed to process subgraph')
        root, nodes, edge = amr_graph.process_subgraph(amr, subgraph_edges=[('g', ':ARG0', 'b'), ('g', ':ARG4', 'c'),
                                                                            ('c', ':name', 'n')])
        correct = ('g', {'g', 'c', 'b', 'n'},
                   [('g', ':ARG0', 'b'), ('g', ':ARG4', 'c'), ('c', ':name', 'n')])
        if (root, nodes, edge) != correct:
            raise Exception('Failed to process subgraph')
        root, nodes, edge = amr_graph.process_subgraph(amr, subgraph_nodes=['g', 'n'],
                                                       subgraph_edges=[('g', ':ARG0', 'b'), ('g', ':ARG4', 'c'),
                                                                       ('c', ':name', 'n')])
        correct = ({'g', 'n'},
                   [('g', ':ARG0', 'b'), ('g', ':ARG4', 'c'), ('c', ':name', 'n')])
        if (nodes, edge) != correct:
            raise Exception('Failed to process subgraph')
        root, nodes, edge = amr_graph.process_subgraph(amr, subgraph_nodes=['g', 'c'], subgraph_root='c')
        correct = ('c', {'g', 'c'},
                   [('g', ':ARG0', 'b'), ('g', ':ARG4', 'c'), ('c', ':name', 'n')])
        if (root, nodes, edge) != correct:
            raise Exception('Failed to process subgraph')
        root, nodes, edge = amr_graph.process_subgraph(amr, subgraph_root='c',
                                                       subgraph_edges=[('g', ':ARG0', 'b'), ('g', ':ARG4', 'c'),
                                                                       ('c', ':name', 'n')])
        correct = ('c', {'c', 'n', 'x0', 'x1', 'x2'},
                   [('g', ':ARG0', 'b'), ('g', ':ARG4', 'c'), ('c', ':name', 'n')])
        if (root, nodes, edge) != correct:
            raise Exception('Failed to process subgraph')

        print()
        amr = AMR.from_string('''
            (l / love-01
                :ARG0 (i / i)
                :ARG1 (p / person
                    :ARG0-of (l2 / love-01
                        :ARG1 l)))
            ''')
        raise NotImplementedError()

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
        amr.edges.append(('a', ':prep-to', 'g'))
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

        # through test
        for amr in self.ldc_amrs:
            cycles = amr_graph.find_cycles(amr)
            if amr_graph.has_cycles(amr):
                if not cycles:
                    raise Exception('Failed to test cycles')
            elif cycles:
                raise Exception('Failed to test cycles')

    def test_get_subgraph(self):
        raise NotImplementedError()

    def test_find_best_root(self):
        raise NotImplementedError()

    def test_is_connected(self):
        raise NotImplementedError()

    def test_find_connected_components(self):
        raise NotImplementedError()

    def test_break_into_connected_components(self):
        raise NotImplementedError()

    def test_find_shortest_path(self):
        raise NotImplementedError()


if __name__ == '__main__':
    unittest.main()
