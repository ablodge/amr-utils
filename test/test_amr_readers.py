import unittest

from amr_utils.amr_readers import *

TEST_FILE1 = 'test_data/test_amrs.txt'
TEST_FILE2 = 'test_data/test_amrs2.txt'

JAMR_TEST_FILE = 'test_data/test_amrs_jamr.txt'

LDC_DIR = '../../LDC_2020/data/alignments/unsplit'


class Test_AMR_Readers(unittest.TestCase):

    def test_AMR_Reader(self):
        reader = AMR_Reader()
        amrs1 = reader.load(TEST_FILE1, quiet=True)
        amrs2 = reader.load(TEST_FILE2, quiet=True)

        # load string
        amr_string = '''
        The boy wants to go to New York.
        (w/want-01 :ARG0 (b/boy)
            :ARG1 (g/go-02 :ARG0 b
                :ARG4 (c/city :name (n/name :op1 "New" 
                    :op2 "York" 
                    :op3 "City"))))
        '''
        amr = reader.parse(amr_string)
        if not (len(amr.nodes) == 8 and len(amr.edges) == 8):
            raise Exception('Failed to correctly read AMR:', amr.id)
        # load dir
        amrs = reader.load_dir(LDC_DIR, quiet=True)
        if not amrs:
            raise Exception('Failed to correctly read AMRs')
        # load glob
        amrs = reader.load_glob(LDC_DIR+'/amr-release-3.0-alignments-w*.txt', quiet=True)
        if not amrs:
            raise Exception('Failed to correctly read AMRs')

    def test_ISI_AMR_Reader(self):
        # Check that alignment reader matches the LDC alignment release for all AMRs
        reader = AMR_Reader(id_style='isi')
        amrs, alignments = reader.load_dir(LDC_DIR, return_alignments=True, quiet=True)
        id_notation = ISI_Notation()
        for amr, aligns in zip(amrs, alignments):
            if 'alignments' in amr.metadata:
                aligns2 = id_notation.parse_alignments_from_line(amr, amr.metadata['alignments'])
                for align1, align2 in zip(aligns, aligns2):
                    if align1 != align2:
                        raise Exception('Alignments read incorrectly:', amr.id)
                if len(aligns) != len(aligns2):
                    raise Exception('Alignments read incorrectly:', amr.id)

        # Check reading alignments from graph
        reader = AMR_Reader()
        file = [os.path.join(LDC_DIR, filename) for filename in os.listdir(LDC_DIR)][0]
        amrs, alignments = reader.load(file, return_alignments=True, quiet=True)
        amr = amrs[0]
        aligns = alignments[0]
        correct = [([0], ['e'], []), ([1], ['m'], []), ([2], [], [('m', ':mod', 'i')]), ([3], ['i2'], []), ([4], ['i'], [])]
        # Establishing Models in Industrial Innovation
        # (e / establish-01~e.0
        #       :ARG1 (m / model~e.1
        #             :mod~e.2 (i / innovate-01~e.4
        #                   :ARG1 (i2 / industry~e.3))))
        test = [(align.tokens, align.nodes, align.edges) for align in aligns]
        if test!=correct:
            raise Exception('Alignments read incorrectly:', amr.id)

    def test_JAMR_AMR_Reader(self):
        reader = AMR_Reader('jamr')

        # reading graph metadata
        amrs, alignments = reader.load(JAMR_TEST_FILE, return_alignments=True, quiet=True)

        # test reading and writing graph metadata
        # amrs, alignments = reader.load(TEST_FILE1, return_alignments=True, quiet=True)
        # metadata_reader = Default_Metadata_Reader()
        # for amr in amrs:
        #     metadata_string = metadata_reader.write(amr)
        #     amr = reader.parse(metadata_string)




if __name__=='__main__':
    unittest.main()