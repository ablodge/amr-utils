import unittest

from amr_utils.amr_readers import AMR_Reader

TEST_FILE1 = 'test_data/test_amrs.txt'
TEST_FILE2 = 'test_data/test_amrs2.txt'

LDC_DIR = '../../LDC_2020/data/amrs/unsplit'


class Test_AMR_Normalizers(unittest.TestCase):
    reader = AMR_Reader()
    ldc_amrs = reader.load_dir(LDC_DIR, quiet=True)

    def test_remove_wiki(self):
        pass

    def test_remove_duplicate_edges(self):
        pass

    def test_remove_artifacts(self):
        pass

    def test_normalize_shape(self):
        pass

    def test_rename_nodes(self):
        pass

    def test_reassign_root(self):
        pass

    def test_remove_cycles(self):
        pass

    def test_normalize_inverse_edges(self):
        pass


if __name__ == '__main__':
    unittest.main()
