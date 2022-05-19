import unittest

from amr_utils.propbank_utils import PropBank


class Test_PropBank_Utils(unittest.TestCase):

    def test_get_frame_description(self):
        for frame in PropBank.FRAMES:
            desc = PropBank.frame_description(frame)

    def test_is_propbank_frame(self):
        for frame in PropBank.FRAMES:
            if not PropBank.is_propbank_frame(frame):
                raise Exception(f'{frame} is a PropBank frame!')
        for s in ['aa-01', 'abc']:
            if PropBank.is_propbank_frame(s):
                raise Exception(f'{s} is not a PropBank frame!')

    def test_is_valid_role(self):
        if not PropBank.is_valid_role('go-02', ':ARG1'):
            raise Exception('Failed to test valid role')
        if PropBank.is_valid_role('go-02', ':ARG2'):
            raise Exception('Failed to test valid role')

    def test_get_roles(self):
        test = PropBank.frame_roles('go-02')
        correct = [':ARG0', ':ARG1', ':ARG3', ':ARG4']
        if test != correct:
            raise Exception('Failed to get roles')

    def test_frame_definition(self):
        test = PropBank.frame_def('go-02')
        correct = 'self-directed motion, disapear or go away'
        if test!=correct:
            raise Exception('Failed to get definition')

    def test_frame_aliases(self):
        aliases = PropBank.frame_aliases('go-02')
        if 'FrameNet' not in aliases:
            raise Exception('Failed to get aliases')
        if 'VerbNet' not in aliases:
            raise Exception('Failed to get aliases')
        if 'ERE' not in aliases:
            raise Exception('Failed to get aliases')



if __name__ == '__main__':
    unittest.main()
