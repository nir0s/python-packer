import sh
import os
import json
import zipfile

__version__ = '0.0.2'

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
        self.packer = sh.Command(exec_path)

    def build(self, parallel=True, debug=False, force=False):
        """Executes a Packer build (`packer build`)

        :param bool parallel: Run builders in parallel
        :param bool debug: Run in debug mode
        :param bool force: Force artifact output even if exists
        """
        self.ccmd = self.packer.build
        self._add_opt('-parallel=true' if parallel else None)
        self._add_opt('-debug' if debug else None)
        self._add_opt('-force' if force else None)
        self._append_base_arguments()
        self._add_opt(self.packerfile)
        return self.ccmd()

    def fix(self, to_file=None):
        """Implements the `packer fix` function

        :param string to_file: File to output fixed template to
        """
        self.ccmd = self.packer.fix
        self._add_opt(self.packerfile)
        result = self.ccmd()
        if to_file:
            with open(to_file, 'w') as f:
                f.write(result.stdout)
        result.fixed = json.loads(result.stdout)
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
        :param bool mrf: output in machine-readable form.
        """
        self.ccmd = self.packer.inspect
        self._add_opt('-machine-readable' if mrf else None)
        self._add_opt(self.packerfile)
        result = self.ccmd()
        if mrf:
            result.parsed_output = self._parse_inspection_output(
                result.stdout)
        return result

    def push(self, create=True, token=False):
        """Implmenets the `packer push` function

        UNTESTED! Must be used alongside an Atlas account
        """
        self.ccmd = self.packer.push
        self._add_opt('-create=true' if create else None)
        self._add_opt('-tokn={0}'.format(token) if token else None)
        self._add_opt(self.packerfile)
        return self.ccmd()

    def validate(self, syntax_only=False):
        """Validates a Packer Template file (`packer validate`)

        If the validation failed, an `sh` exception will be raised.
        :param bool syntax_only: Whether to validate the syntax only
        without validating the configuration itself.
        """
        self.ccmd = self.packer.validate
        self._add_opt('-syntax-only' if syntax_only else None)
        self._append_base_arguments()
        self._add_opt(self.packerfile)
        # as sh raises an exception rather than return a value when execution
        # fails we create an object to return the exception and the validation
        # state
        try:
            validation = self.ccmd()
            validation.succeeded = True if validation.exit_code == 0 else False
            validation.error = None
        except Exception as ex:
            validation = ValidationObject()
            validation.succeeded = False
            validation.failed = True
            validation.error = ex.message
        return validation

    def version(self):
        """Returns Packer's version number (`packer version`)

        As of v0.7.5, the format shows when running `packer version`
        is: Packer vX.Y.Z. This method will only returns the number, without
        the `packer v` prefix so that you don't have to parse the version
        yourself.
        """
        return self.packer.version().split('v')[1].rstrip('\n')

    def _add_opt(self, option):
        if option:
            self.ccmd = self.ccmd.bake(option)

    def _validate_argtype(self, arg, argtype):
        if not isinstance(arg, argtype):
            raise PackerException('{0} argument must be of type {1}'.format(
                arg, argtype))
        return arg

    def _append_base_arguments(self):
        """Appends base arguments to packer commands.

        -except, -only, -var and -vars-file are appeneded to almost
        all subcommands in packer. As such this can be called to add
        these flags to the subcommand.
        """
        if self.exc and self.only:
            raise PackerException('Cannot provide both "except" and "only"')
        elif self.exc:
            self._add_opt('-except={0}'.format(self._joinc(self.exc)))
        elif self.only:
            self._add_opt('-only={0}'.format(self._joinc(self.only)))
        for var, value in self.vars.items():
            self._add_opt('-var')
            self._add_opt('{0}={1}'.format(var, value))
        if self.vars_file:
            self._add_opt('-vars-file={0}'.format(self.vars_file))

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


class Installer():
    def __init__(self, packer_path, installer_path):
        self.packer_path = packer_path
        self.installer_path = installer_path

    def install(self):
        with open(self.installer_path, 'rb') as f:
            zip = zipfile.ZipFile(f)
            for path in zip.namelist():
                zip.extract(path, self.packer_path)
        exec_path = os.path.join(self.packer_path, 'packer')
        if not self._verify(exec_path):
            raise PackerException('packer installation failed. '
                                  'Executable could not be found under: '
                                  '{0}'.format(exec_path))
        else:
            return exec_path

    def _verify(self, packer):
        return True if os.path.isfile(packer) else False


class ValidationObject():
    pass


class PackerException(Exception):
    pass
