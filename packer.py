# Copyright 2015,2016 Nir Cohen
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sh
import os
import json
import zipfile

DEFAULT_PACKER_PATH = 'packer'


class Packer(object):
    """A Hashicorp packer client
    """

    def __init__(self,
                 packerfile,
                 exc=None,
                 only=None,
                 vars=None,
                 var_file=None,
                 exec_path=DEFAULT_PACKER_PATH,
                 out_iter=None,
                 err_iter=None,
                 validate=False):
        """Initialize a packer instance

        :param string packerfile: Path to Packer template file
        :param list exc: List of builders to exclude
        :param list only: List of builders to include
        :param dict vars: key=value pairs of template variables
        :param string var_file: Path to variables file
        :param string exec_path: Path to Packer executable
        :param bool validate: Whether to validate the packerfile on init
        """
        # TODO: redo type validation. This is nasty
        self.packerfile = self._validate_argtype(packerfile, str)
        if not os.path.isfile(packerfile):
            raise OSError('packerfile not found at path: {0}'.format(
                packerfile))
        self.validate(syntax_only=True)
        self.var_file = var_file
        self.exc = self._validate_argtype(exc or [], list)
        self.only = self._validate_argtype(only or [], list)
        self.vars = self._validate_argtype(vars or {}, dict)

        kwargs = dict()
        if out_iter is not None:
            kwargs["_out"] = out_iter
            kwargs["_out_bufsize"] = 1
        if err_iter is not None:
            kwargs["_err"] = err_iter
            kwargs["_out_bufsize"] = 1

        self.packer = sh.Command(exec_path)
        self.packer = self.packer.bake(**kwargs)

    def build(self,
              parallel=True,
              debug=False,
              force=False,
              machine_readable=False):
        """Return the result of a `packer build` execution

        :param bool parallel: Run builders in parallel
        :param bool debug: Run in debug mode
        :param bool force: Force artifact output even if exists
        :param bool machine_readable: Make output machine-readable
        """
        self.packer_cmd = self.packer.build

        self._add_opt('-parallel=true' if parallel else None)
        self._add_opt('-debug' if debug else None)
        self._add_opt('-force' if force else None)
        self._add_opt('-machine-readable' if machine_readable else None)
        self._append_base_arguments()
        self._add_opt(self.packerfile)

        return self.packer_cmd()

    def fix(self, to_file=None):
        """Return a fixed packerfile as provided by the `packer fix` command

        v0.2.0: `result.fixed` is deprecated and will be removed sometime in
         the future. `result` will instead return the fixed packerfile.

        :param string to_file: File to output fixed template to
        """
        self.packer_cmd = self.packer.fix

        self._add_opt(self.packerfile)

        result = self.packer_cmd()
        if to_file:
            with open(to_file, 'w') as fixed_packerfile:
                fixed_packerfile.write(result.stdout)
        result = json.loads(result.stdout)
        # Deprecated in v0.2.0
        result.fixed = result
        return result

    def inspect(self, machine_readable=True, mrf=True):
        """Return the result of a packerfile inspection

        v0.2.0: `mrf` is deprecated and will be removed sometime in the
         future. It is replaced with `machine_readable` Same goes for
         `result.parsed_output` which will be put in `result`.

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

        DEPRECATED: param bool mrf: output in machine-readable form.
        :param bool machine_readable: output in machine-readable form.
        """
        self.packer_cmd = self.packer.inspect

        self._add_opt('-machine-readable' if mrf or machine_readable else None)
        self._add_opt(self.packerfile)

        result = self.packer_cmd()
        if machine_readable or mrf:
            if mrf:
                print(
                    '`mrf` is deprecated starting with v0.2.0. Please use '
                    '`machine_readable` instead.')
            # `parsed_output` is deprecated in 0.2.0v
            result.parsed_output = self._parse_inspection_output(result.stdout)
            result = result.parsed_output
        else:
            result.parsed_output = None
        return result

    def push(self, create=True, token=False):
        """Return the result of a `packer push` execution

        UNTESTED! Must be used alongside an Atlas account
        """
        self.packer_cmd = self.packer.push

        self._add_opt('-create=true' if create else None)
        self._add_opt('-tokn={0}'.format(token) if token else None)
        self._add_opt(self.packerfile)

        return self.packer_cmd()

    def validate(self, syntax_only=False):
        """Return the result of a packerfile validation

        If the validation failed, an `sh` exception will be raised.

        :param bool syntax_only: Whether to validate the syntax only
        without validating the configuration itself.
        """
        self.packer_cmd = self.packer.validate

        self._add_opt('-syntax-only' if syntax_only else None)
        self._append_base_arguments()
        self._add_opt(self.packerfile)

        # as sh raises an exception rather than return a value when execution
        # fails we create an object to return the exception and the validation
        # state
        try:
            validation = self.packer_cmd()
            validation.succeeded = validation.exit_code == 0
            validation.failed = not validation.succeeded
            validation.error = None
        except Exception as ex:
            validation = ValidationObject()
            validation.succeeded = False
            validation.failed = True
            validation.error = ex.message
        return validation

    def version(self):
        """Return Packer's version number

        As of v0.7.5, the format shows when running `packer version`
        is: Packer vX.Y.Z. This method will only return the number, without
        the `packer v` prefix so that you don't have to parse the version
        yourself.
        """
        return self.packer.version().split('v')[1].rstrip('\n')

    def _add_opt(self, option):
        if option:
            self.packer_cmd = self.packer_cmd.bake(option)

    def _validate_argtype(self, argument, required_argtype):
        """Return an argument if it passed type validation
        """
        if not isinstance(argument, required_argtype):
            raise PackerException('{0} argument must be of type {1}'.format(
                argument, required_argtype))
        return argument

    def _append_base_arguments(self):
        """Append base arguments to packer commands.

        -except, -only, -var and -var-file are appeneded to almost
        all subcommands in packer. As such this can be called to add
        these flags to the subcommand.
        """
        if self.exc and self.only:
            raise PackerException('Cannot provide both "except" and "only"')
        elif self.exc:
            self._add_opt('-except={0}'.format(self._join_comma(self.exc)))
        elif self.only:
            self._add_opt('-only={0}'.format(self._join_comma(self.only)))
        for var, value in self.vars.items():
            self._add_opt("-var")
            self._add_opt("{0}={1}".format(var, value))
        if self.var_file:
            self._add_opt('-var-file={0}'.format(self.var_file))

    def _join_comma(self, a_list):
        """Return a comma delimited string from a list
        """
        return str(','.join(a_list))

    def _parse_inspection_output(self, output):
        """Return a dictionary containing the parts of an inspected packerfile

        See the inspect method for more info.
        This has been tested vs. Packer v0.7.5
        """
        parts = {'variables': [], 'builders': [], 'provisioners': []}
        for line in output.splitlines():
            line = line.split(',')
            if line[2].startswith('template'):
                del line[0:2]
                component = line[0]
                if component == 'template-variable':
                    variable = {"name": line[1], "value": line[2]}
                    parts['variables'].append(variable)
                elif component == 'template-builder':
                    builder = {"name": line[1], "type": line[2]}
                    parts['builders'].append(builder)
                elif component == 'template-provisioner':
                    provisioner = {"type": line[1]}
                    parts['provisioners'].append(provisioner)
        return parts


class Installer(object):
    def __init__(self, packer_path, installer_path):
        self.packer_path = packer_path
        self.installer_path = installer_path

    def install(self):
        with open(self.installer_path, 'rb') as f:
            zip = zipfile.ZipFile(f)
            for path in zip.namelist():
                zip.extract(path, self.packer_path)
        exec_path = os.path.join(self.packer_path, 'packer')
        if not self._verify_packer_installed(exec_path):
            raise PackerException('packer installation failed. '
                                  'Executable could not be found under: '
                                  '{0}'.format(exec_path))
        else:
            return exec_path

    def _verify_packer_installed(self, packer_path):
        return os.path.isfile(packer_path)


class ValidationObject():
    pass


class PackerException(Exception):
    pass
