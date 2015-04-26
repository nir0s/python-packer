import sh
import os

__version__ = '0.0.1'

DEFAULT_PACKER_PATH = 'packer'


class Packer():
    """Packer interface using the `sh` module (http://amoffat.github.io/sh/)
    """
    def __init__(self, packerfile, exc=None, only=None, vars=None,
                 vars_file=None, exec_path=DEFAULT_PACKER_PATH):
        """
        :param string packerfile: Path to Packer template file
        :param list exc: List of builders to exclude
        :param list only: List of builders to include
        :param dict vars: Key Value pairs of template variables
        :param string vars_file: Path to variables file
        :param string exec_path: Path to Packer executable
        """
        self.packerfile = self._validate_argtype(packerfile, str)
        self.vars_file = vars_file
        if not os.path.isfile(self.packerfile):
            raise OSError('packerfile not found at path: {0}'.format(
                self.packerfile))
        self.exc = self._validate_argtype(exc if exc else [], list)
        self.only = self._validate_argtype(only if only else [], list)
        self.vars = self._validate_argtype(vars if vars else {}, dict)
        if not os.path.isfile(self.packerfile):
            raise OSError('packerfile not found at path: {0}'.format(
                self.packerfile))
        self.packer = sh.Command(exec_path)

    def build(self, parallel=True, debug=False, force=False):
        """Executes a Packer build (`packer build`)

        :param bool parallel: Run builders in parallel
        :param bool debug: Run in debug mode
        :param bool force: Force artifact output even if exists
        """
        cmd = self.packer.build
        cmd = self._add_opt(cmd, '-parallel=true' if parallel else None)
        cmd = self._add_opt(cmd, '-debug' if debug else None)
        cmd = self._add_opt(cmd, '-force' if force else None)
        cmd = self._append_base_arguments(cmd)
        cmd = cmd.bake(self.packerfile)
        return cmd()

    def fix(self, to_file=None):
        """Implements the `packer fix` function
        """
        cmd = self.packer.fix
        cmd = cmd.bake(self.packerfile)
        result = cmd()
        if to_file:
            with open(to_file, 'w') as f:
                f.write(result.stdout)
        return result

    def inspect(self, mrf=True):
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
        :param bool machine_readable: output in machine-readable form.
        """
        cmd = self.packer.inspect
        cmd = self._add_opt(cmd, '-machine-readable' if mrf else None)
        cmd = cmd.bake(self.packerfile)
        result = cmd()
        if mrf:
            result.parsed_output = self._parse_inspection_output(
                result.stdout)
        return result

    def push(self, create=True, token=False):
        """Implmenets the `packer push` function

        UNTESTED!
        """
        command = self.packer.push
        if create:
            command = command.bake('-create=true')
        if token:
            command = command.bake('-token={0}'.format(token))
        command = command.bake(self.packerfile)
        return command()

    def validate(self, syntax_only=False):
        """Validates a Packer Template file (`packer validate`)

        If the validation failed, an `sh` exception will be raised.
        :param bool syntax_only: Whether to validate the syntax only
        without validating the configuration itself.
        """
        command = self.packer.validate
        if syntax_only:
            command = command.bake('-syntax-only')
        command = self._append_base_arguments(command)
        command = command.bake(self.packerfile)
        return command()
        # err.. need to return normal values with validation result
        # validated.succeeded = True if validated.exit_code == 0 else False
        # validated.failed = not validated.succeeded

    def version(self):
        """Returns Packer's version number (`packer version`)

        As of v0.7.5, the format shows when running `packer version`
        is: Packer vX.Y.Z. This method will only returns the number, without
        the `packer v` prefix so that you don't have to parse the version
        yourself.
        """
        return self.packer.version().split('v')[1].rstrip('\n')

    def _add_opt(self, command, option):
        if option:
            return command.bake(option)
        return command

    def _validate_argtype(self, arg, argtype):
        if not isinstance(arg, argtype):
            raise PackerException('{0} argument must be of type {1}'.format(
                arg, argtype))
        return arg

    def _append_base_arguments(self, command):
        """Appends base arguments to packer commands.

        -except, -only, -var and -vars-file are appeneded to almost
        all subcommands in packer. As such this can be called to add
        these flags to the subcommand.
        """
        if self.exc and self.only:
            raise PackerException('Cannot provide both "except" and "only"')
        elif self.exc:
            command = command.bake('-except={0}'.format(self._joinc(self.exc)))
        elif self.only:
            command = command.bake('-only={0}'.format(self._joinc(self.only)))
        for var, value in self.vars.items():
            command = command.bake("-var '{0}={1}'".format(var, value))
        if self.vars_file:
            command = command.bake('-vars-file={0}'.format(self.vars_file))
        return command

    def _joinc(self, lst):
        """Returns a comma delimited string from a list"""
        return str(','.join(lst))

    def _joins(self, lst):
        """Returns a space delimited string from a list"""
        return str(' '.join(lst))

    def _parse_inspection_output(self, output):
        """Parses the machine-readable output `packer inspect` provides.

        See the inspect method for more info.
        This has been tested vs. Packer v0.7.5
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


class PackerException(Exception):
    pass
