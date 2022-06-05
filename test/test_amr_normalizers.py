import unittest
from collections import Counter

from amr_utils.amr_readers import AMR_Reader
from amr_utils.amr_normalizers import *

TEST_FILE1 = 'test_data/test_amrs.txt'
TEST_FILE2 = 'test_data/test_amrs2.txt'

LDC_DIR = '../../LDC_2020/data/amrs/unsplit'


class Test_AMR_Normalizers(unittest.TestCase):
    reader = AMR_Reader()
    ldc_amrs = reader.load_dir(LDC_DIR, quiet=True)

    def test_rename_nodes(self):
        for amr_ in self.ldc_amrs:
            amr = amr_.copy()
            rename_nodes(amr, id_map=lambda i: f'a{i}')
            amr.graph_string(pretty_print=False)
            for n in amr.nodes:
                if not n.startswith('a') or not n[-1].isdigit():
                    raise Exception('Failed to rename nodes')
            for s, r, t in amr.edges:
                if s not in amr.nodes or t not in amr.nodes:
                    raise Exception('Failed to rename nodes')
        # TODO

    def test_remove_wiki(self):
        for amr_ in self.ldc_amrs:
            amr = amr_.copy()
            remove_wiki(amr)
            for s, r, t in amr.edges:
                if r == ':wiki':
                    raise Exception('Failed to remove wiki')

    def test_remove_duplicate_edges(self):
        for amr_ in self.ldc_amrs:
            amr = amr_.copy()
            remove_duplicate_edges(amr)
            edges = Counter()
            for s, r, t in amr.edges:
                if AMR_Notation.is_inverse_relation(r):
                    edges[(t, AMR_Notation.invert_relation(r), s)] += 1
                else:
                    edges[(s, r, t)] += 1
            if any(edges[e] > 1 for e in edges):
                raise Exception('Failed to remove duplicate edges')
            if set(AMR_Notation.normalize_edge(e) for e in amr.edges) != \
                    set(AMR_Notation.normalize_edge(e) for e in amr_.edges):
                raise Exception('Failed to remove duplicate edges')


    def test_normalize_shape(self):
        # TODO
        raise NotImplementedError()

    def test_reassign_root(self):
        # TODO
        raise NotImplementedError()

    def test_remove_cycles(self):
        # TODO
        raise NotImplementedError()

    def test_normalize_inverse_edges(self):
        # TODO
        raise NotImplementedError()

    def test_recategorize(self):
        for amr in self.ldc_amrs:
            recategorize_graph(amr)

    def test_decategorize(self):
        for amr in self.ldc_amrs:
            amr2 = amr.copy()
            recategorize_graph(amr2)
            decategorize_graph(amr2)
            if amr.graph_string(pretty_print=False) != amr2.graph_string(pretty_print=False):
                raise Exception('Failed to decategorize AMR')


if __name__ == '__main__':
    unittest.main()
