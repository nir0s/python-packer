import sh

__author__ = 'Gigaspaces'
__version__ = '0.1.2'

DEFAULT_PACKER_PATH = 'packer'


class Packer():

    def __init__(self, packerfile, exc=None, only=None, vars=None,
                 vars_file=None, exec_path=DEFAULT_PACKER_PATH):
        self.packerfile = packerfile
        self.exc = exc if exc else []
        self.only = only if only else []
        self.vars = vars if vars else {}
        self.vars_file = vars_file
        self.packer = sh.Command(exec_path)

    def _append_base_arguments(self, cmd):
        """Add base arguments to packer commands.

        -except, -only, -var and -vars-file are appeneded to almost
        all subcommands in packer. As such this can be called to add
        these flags to the subcommand.
        """
        if self.exc and self.only:
            raise PackerException('Cannot provide both "except" and "only"')
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
        """Returns a comma separated string from a list"""
        return str(','.join(lst))

    def _join(self, lst):
        """Returns a space separated string from a list"""
        return str(' '.join(lst))

    def version(self):
        """Returns Packer's version number (`packer version`)

        As of v0.7.5, the format shows when running `packer version`
        is: Packer vX.Y.Z. This only returns the number, without the
        `packer v` prefix so that you don't have to parse the version
        yourself.
        """
        return self.packer.version().split('v')[1].rstrip('\n')

    def validate(self, syntax_only=False):
        """Validates a Packer Template file (`packer validate`)
        """
        validator = self.packer.validate
        if syntax_only:
            validator = validator.bake('-syntax-only')
        validator = self._append_base_arguments(validator)
        validator = validator.bake(self.packerfile)
        return validator()

    def build(self, parallel=True, debug=False, force=False):
        """Executes a Packer build (`packer build`)
        """
        builder = self.packer.build
        if parallel:
            builder = builder.bake('-parallel=true')
        if debug:
            builder = builder.bake('-debug')
        if force:
            builder = builder.bake('-force')
        builder = self._append_base_arguments(builder)
        builder = builder.bake(self.packerfile)
        return builder()

    def inspect(self):
        """Inspects a Packer Templates file (`packer inspect -machine-readable`)

        To return the output in a readable form, the `-machine-readable` flag
        is appended automatically, afterwhich the output is parsed and returned
        as a dict of the following format:
          "variables": [
            {
              "name": "aws_access_key",
              "value": "{{env `AWS_ACCESS_KEY_ID`}}"
            },
            {
              "name": "aws_secret_key",
              "value": "{{env `AWS_ACCESS_KEY`}}"
            }
          ],
          "provisioners": [
            {
              "type": "shell"
            }
          ],
          "builders": [
            {
              "type": "amazon-ebs",
              "name": "amazon"
            }
          ]
        """
        inspector = self.packer.inspect
        inspector = inspector.bake('-machine-readable', self.packerfile)
        result = inspector()
        result.parsed_output = self._parse_inspection_output(result.stdout)
        return result

    def _parse_inspection_output(self, output):
        """Parses the machine-readable output `packer inspect` provides.

        See the inspect method for more info.
        """
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


class PackerException():
    pass
