import unittest

from amr_utils.propbank_utils import PropBank


class Test_PropBank_Utils(unittest.TestCase):

    def test_get_frame_description(self):
        desc = PropBank.frame_description('go-02')

    def test_is_propbank_frame(self):
        if PropBank.is_propbank_frame('go-02'):
            pass

    def test_is_valid_role(self):
        if PropBank.is_valid_role('go-02',':ARG1'):
            pass

    def test_get_roles(self):
        roles = PropBank.frame_roles('go-02')
        pass

    def test_frame_definition(self):
        definition = PropBank.frame_def('go-02')
        pass

    def test_frame_aliases(self):
        aliases = PropBank.frame_aliases('go-02')


if __name__ == '__main__':
    unittest.main()
