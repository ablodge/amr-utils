import unittest

from amr_utils.amr import AMR
from amr_utils.amr_alignments import AMR_Alignment

TEST_FILE1 = 'test_data/test_amrs.txt'
TEST_FILE2 = 'test_data/test_amrs2.txt'

LDC_DIR = '../../LDC_2020/data/amrs/unsplit'


class Test_AMR_Alignments(unittest.TestCase):

    def test_alignment(self):
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
        # print()

    def test_to_json(self):
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
        test = []
        for a in [align1,align2,align3,align4,align5,align6,align7]:
            test.append(a.to_json())
        test2 = []
        for a in [align1, align2, align3, align4, align5, align6, align7]:
            test2.append(a.to_json(amr))
        # print()

    def test_description(self):
        raise NotImplementedError()

    def test_str(self):
        raise NotImplementedError()

    def test_get_subgraph(self):
        raise NotImplementedError()

    def test_ordering(self):
        raise NotImplementedError()

    def test_alignment_set(self):
        raise NotImplementedError()

    def test_add(self):
        raise NotImplementedError()

    def test_remove(self):
        raise NotImplementedError()

    def test_get(self):
        raise NotImplementedError()

    def test_get_all(self):
        raise NotImplementedError()

    def test_from_json(self):
        raise NotImplementedError()

    def test_anonymize(self):
        raise NotImplementedError()

    def test_unanonymize(self):
        raise NotImplementedError()

    def test_isi_alignments(self):
        raise NotImplementedError()

if __name__ == '__main__':
    unittest.main()
