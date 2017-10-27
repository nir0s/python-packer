import os

import packer
import testtools

TEST_RESOURCES_DIR = 'tests/resources'
TEST_PACKERFILE = os.path.join(TEST_RESOURCES_DIR, 'simple-test.json')
TEST_BAD_PACKERFILE = os.path.join(TEST_RESOURCES_DIR, 'badpackerfile.json')

PACKER = packer.Packer(TEST_PACKERFILE)


def test_dict_to_command():
    """Validate dict is converted to a command properly"""
    kwargs = {'test': 'value'}
    cmd = PACKER.dict_to_command(kwargs)
    assert cmd == ['--test=value']


def test_join_comma():
    """Validate list concatination is correct"""
    output = PACKER._join_comma(['hello', 'world'])
    assert output == 'hello,world'


def test_run_command():
    """Check returned output from executed command"""
    cmd = ['packer', 'version']
    output = PACKER._run_command(cmd)

    assert 'Packer v' in output.stdout
    assert '' in output.stderr
    assert 0 == output.returncode


def test_parse_inspection_output():
    """Check returned output from executed command"""
    output = '''1508999535,,ui,say,Variables:
    1508999535,,ui,say,  <No variables>
    1508999535,,ui,say,
    1508999535,,ui,say,Builders:
    1508999535,,template-builder,docker,docker
    1508999535,,ui,say,  docker
    1508999535,,ui,say,
    1508999535,,ui,say,Provisioners:
    1508999535,,template-provisioner,shell
    1508999535,,ui,say,  shell
    1508999535,,ui,say,Note: If your build names contain user variables or template functions such as 'timestamp'%!(PACKER_COMMA) these are processed at build time%!(PACKER_COMMA) and therefore only show in their raw form here.'''

    output = PACKER._parse_inspection_output(output)

    assert {
        'builders': [{
            'name': 'docker',
            'type': 'docker'
        }],
        'provisioners': [{
            'type': 'shell'
        }],
        'variables': []
    } == output
