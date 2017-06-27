import packer

import testtools
import os

PACKER_PATH = '/usr/bin/packer'
TEST_RESOURCES_DIR = 'tests/resources'
TEST_PACKERFILE = os.path.join(TEST_RESOURCES_DIR, 'packerfile.json')
TEST_BAD_PACKERFILE = os.path.join(TEST_RESOURCES_DIR, 'badpackerfile.json')
TEST_VARFILE = 'var/amazon-linux.json')


class TestBase(testtools.TestCase):

    def test_build(self):
        p = packer.Packer(TEST_PACKERFILE, var_file=TEST_VARFILE)
        p.build()

    def test_fix(self):
        p = packer.Packer(TEST_PACKERFILE, var_file=TEST_VARFILE)
        p.fix()

    def test_inspect(self):
        p = packer.Packer(TEST_PACKERFILE, var_file=TEST_VARFILE)
        p.inspect()

    def test_validate(self):
        p = packer.Packer(TEST_PACKERFILE, var_file=TEST_VARFILE)
        p.validate()

    def test_version(self):
        p = packer.Packer(TEST_PACKERFILE)
        p.version()
