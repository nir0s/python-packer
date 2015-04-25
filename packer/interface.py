import logger
import logging
import sh
import sys
# import re

DEFAULT_PACKER_PATH = 'packer'

lgr = logger.init()
verbose_output = False


def _set_global_verbosity_level(is_verbose_output=False):
    """sets the global verbosity level for console and the lgr logger.

    :param bool is_verbose_output: should be output be verbose
    """
    global verbose_output
    # TODO: (IMPRV) only raise exceptions in verbose mode
    verbose_output = is_verbose_output
    if verbose_output:
        lgr.setLevel(logging.DEBUG)
    else:
        lgr.setLevel(logging.INFO)
    # print 'level is: ' + str(lgr.getEffectiveLevel())


class Packer():

    def __init__(self, packerfile, exc=None, only=None, vars=None,
                 vars_file=None, exec_path=DEFAULT_PACKER_PATH):
        self.packerfile = packerfile
        self.exc = exc if exc else []
        self.only = only if only else []
        self.vars = vars if vars else {}
        self.packer = sh.Command(exec_path)
        self.vars_file = vars_file
        # p = self.packer
        # self.packer = p

    def _append_base_arguments(self, cmd):
        if self.exc and self.only:
            lgr.error('Cannot provide both "except" and "only".')
            sys.exit(1)
        if self.exc:
            cmd = cmd.bake('-except={0}'.format(self._joinc(self.exc)))
        if self.only:
            cmd = cmd.bake('-only={0}'.format(self._joinc(self.only)))
        for var, value in self.vars.iteritems():
            cmd = cmd.bake("-var '{0}={1}'".format(var, value))
        if self.vars_file:
            cmd = cmd.bake('-vars-file={0}'.format(self.vars_file))
        return cmd

    def _joinc(self, lst):
        return str(','.join(lst))

    def _join(self, lst):
        return str(' '.join(lst))

    def version(self):
        return self.packer.version().split('v')[1].rstrip('\n')

    def validate(self, syntax_only=False):
        validator = self.packer.validate
        if syntax_only:
            lgr.info('syntax-only check active...')
            validator = validator.bake('-syntax-only')
        validator = self._append_base_arguments(validator)
        validator = validator.bake(self.packerfile)
        lgr.info('Validating packerfile: {0}'.format(self.packerfile))
        # lgr.info('Executing: {0}'.format(self._join(validator().cmd)))
        return validator()

    def build(self, parallel=True, debug=False, force=False):
        builder = self.packer.build
        if parallel:
            lgr.info('parallel build active...')
            builder = builder.bake('-parallel=true')
        if debug:
            lgr.info('debug mode active...')
            builder = builder.bake('-debug')
        if force:
            lgr.info('force mode active...')
            builder = builder.bake('-force')
        builder = self._append_base_arguments(builder)
        builder = builder.bake(self.packerfile)
        lgr.info('Running build: {0}'.format(self.packerfile))
        lgr.info('Executing: {0}'.format(self._join(builder().cmd)))
        return builder()

    def inspect(self):
        inspector = self.packer.inspect
        inspector = inspector.bake('-machine-readable', self.packerfile)
        lgr.info('Inspecting packerfile: {0}'.format(self.packerfile))
        result = inspector()
        result.parsed_output = self._parse_inspection_output(result.stdout)
        return result

    def _parse_inspection_output(self, output):
        parts = {'variables': [], 'builders': [], 'provisioners': []}
        for l in output.splitlines():
            l = l.split(',')
            if l[2].startswith('template'):
                del l[0:2]
                component = l[0]
                if component == 'template-variable':
                    variable = {"name": l[1], "value": l[2]}
                    parts['variables'].append(variable)
                elif component == 'template-builder':
                    builder = {"name": l[1], "type": l[2]}
                    parts['builders'].append(builder)
                elif component == 'template-provisioner':
                    provisioner = {"type": l[1]}
                    parts['provisioners'].append(provisioner)
        return parts
