import unittest

from amr_utils import amr_graph
from amr_utils.amr_iterators import depth_first_edges
from amr_utils.amr_readers import AMR_Reader

TEST_FILE1 = 'test_data/test_amrs.txt'
TEST_FILE2 = 'test_data/test_amrs2.txt'

LDC_DIR = '../../LDC_2020/data/amrs/unsplit'


class Test_Graph_Utils(unittest.TestCase):
    reader = AMR_Reader()
    ldc_amrs = reader.load_dir(LDC_DIR, quiet=True)

    def test_reachable_nodes(self):
        # through test
        for amr in self.ldc_amrs:
            amr_graph._get_reachable_nodes(amr)
            amr_graph._get_reachable_nodes(amr, ignore_edge_direction=True)

    def test_is_directed_acyclic_graph(self):
        # through test
        for amr in self.ldc_amrs:
            cycles = amr_graph.find_cycles(amr)
            if not amr_graph.is_directed_acyclic_graph(amr):
                if not cycles:
                    raise Exception('Failed to evaluate rooted DAG')
            elif cycles:
                raise Exception('Failed to evaluate rooted DAG')

    def test_has_cycles(self):
        # through test
        for amr in self.ldc_amrs:
            cycles = amr_graph.find_cycles(amr)
            if amr_graph.has_cycles(amr):
                if not cycles:
                    raise Exception('Failed to test cycles')
            elif cycles:
                raise Exception('Failed to test cycles')

    def test_find_cycles(self):
        # through test
        for amr in self.ldc_amrs:
            cycles = amr_graph.find_cycles(amr)
            for cycle in cycles:
                start_node = cycle.pop()
                reached_nodes = set()
                for s,r,t in depth_first_edges(amr, ...):
                    reached_nodes.add(t)
                if reached_nodes != cycle:
                    raise Exception('Failed to traverse cycle')

    def test_get_subgraph(self):
        raise NotImplemented()

    def test_find_best_root(self):
        raise NotImplemented()

    def test_is_connected(self):
        raise NotImplemented()

    def test_find_connected_components(self):
        raise NotImplemented()

    def test_break_into_connected_components(self):
        raise NotImplemented()

    def test_find_shortest_path(self):
        raise NotImplemented()


if __name__ == '__main__':
    unittest.main()
