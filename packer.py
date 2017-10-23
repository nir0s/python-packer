import copy
import json
import os
import subprocess
import zipfile

from collections import namedtuple

DEFAULT_PACKER_PATH = 'packer'


class Packer(object):
    """A packer client
    """

    def __init__(self,
                 packerfile,
                 exc=None,
                 only=None,
                 vars=None,
                 var_file=None,
                 exec_path=DEFAULT_PACKER_PATH,
                 out_iter=None,
                 err_iter=None):
        """
        :param string packerfile: Path to Packer template file
        :param list exc: List of builders to exclude
        :param list only: List of builders to include
        :param dict vars: key=value pairs of template variables
        :param string var_file: Path to variables file
        :param string exec_path: Path to Packer executable
        """
        self.packerfile = self._validate_argtype(packerfile, str)
        self.var_file = var_file
        if not os.path.isfile(self.packerfile):
            raise OSError(
                'packerfile not found at path: {0}'.format(self.packerfile))
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

        command = []
        command.append(exec_path)
        command.extend(self.dict_to_command(kwargs))
        self.packer = command

    def dict_to_command(self, kwargs):
        """Convert dict to '--key=value' command parameters"""
        param = []
        for parameter, value in kwargs.items():
            param.append('--{}={}'.format(parameter, value))
        return param

    def build(self,
              parallel=True,
              debug=False,
              force=False,
              machine_readable=False):
        """Executes a `packer build`

        :param bool parallel: Run builders in parallel
        :param bool debug: Run in debug mode
        :param bool force: Force artifact output even if exists
        :param bool machine_readable: Make output machine-readable
        """
        cmd = copy.copy(self.packer)
        cmd.append('build')
        self.packer_cmd = cmd

        self._add_opt('-parallel=true' if parallel else None)
        self._add_opt('-debug' if debug else None)
        self._add_opt('-force' if force else None)
        self._add_opt('-machine-readable' if machine_readable else None)
        self._append_base_arguments()
        self._add_opt(self.packerfile)

        return subprocess.run(self.packer_cmd)

    def fix(self, to_file=None):
        """Implements the `packer fix` function

        :param string to_file: File to output fixed template to
        """
        cmd = copy.copy(self.packer)
        cmd.append('fix')
        self.packer_cmd = cmd

        self._add_opt(self.packerfile)

        result = subprocess.run(cmd, stdout=subprocess.PIPE)
        if to_file:
            with open(to_file, 'w') as f:
                f.write(result.stdout.decode())
        result.fixed = json.loads(result.stdout.decode())
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
        cmd = copy.copy(self.packer)
        cmd.append('inspect')
        self.packer_cmd = cmd

        self._add_opt('-machine-readable' if mrf else None)
        self._add_opt(self.packerfile)

        result = subprocess.run(self.packer_cmd)
        # if mrf:
        #     result.parsed_output = self._parse_inspection_output(
        #         result.stdout.decode())
        # else:
        #     result.parsed_output = None
        return result

    def push(self, create=True, token=False):
        """Implmenets the `packer push` function

        UNTESTED! Must be used alongside an Atlas account
        """
        cmd = copy.copy(self.packer)
        cmd.append('push')
        self.packer_cmd = cmd

        self._add_opt('-create=true' if create else None)
        self._add_opt('-tokn={0}'.format(token) if token else None)
        self._add_opt(self.packerfile)

        return subprocess.run(cmd)

    def validate(self, syntax_only=False):
        """Validates a Packer Template file (`packer validate`)

        If the validation failed, an `sh` exception will be raised.
        :param bool syntax_only: Whether to validate the syntax only
        without validating the configuration itself.
        """
        cmd = copy.copy(self.packer)
        cmd.append('validate')
        self.packer_cmd = cmd

        self._add_opt('-syntax-only' if syntax_only else None)
        self._append_base_arguments()
        self._add_opt(self.packerfile)

        # as sh raises an exception rather than return a value when execution
        # fails we create an object to return the exception and the validation
        # state
        # try:
        #     validation = subprocess.run(self.packer_cmd)
        #     validation.succeeded = validation.exit_code == 0
        #     validation.error = None
        # except Exception as ex:
        #     validation = ValidationObject()
        #     validation.succeeded = False
        #     validation.failed = True
        #     validation.error = ex.message
        return subprocess.run(self.packer_cmd)

    def version(self):
        """Returns Packer's version number (`packer version`)

        As of v0.7.5, the format shows when running `packer version`
        is: Packer vX.Y.Z. This method will only returns the number, without
        the `packer v` prefix so that you don't have to parse the version
        yourself.
        """
        cmd = copy.copy(self.packer)
        cmd.append('version')
        output = subprocess.run(cmd, stdout=subprocess.PIPE)
        version = output.stdout.decode().split('\n')[0].split('v')[1]
        return version

    def _add_opt(self, option):
        if option:
            self.packer_cmd.append(option)

    def _validate_argtype(self, arg, argtype):
        if not isinstance(arg, argtype):
            raise PackerException(
                '{0} argument must be of type {1}'.format(arg, argtype))
        return arg

    def _append_base_arguments(self):
        """Appends base arguments to packer commands.

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

    def _join_comma(self, lst):
        """Returns a comma delimited string from a list"""
        return str(','.join(lst))

    def _parse_inspection_output(self, output):
        """Parses the machine-readable output `packer inspect` provides.

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

    def _run_command(self, command):
        """Wrapper to execute command"""
        PackerCommand = namedtuple('PackerCommand', ['stdout', 'stderr'])
        executed = subprocess.run(
            command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        packer_command = PackerCommand(executed.stdout.decode(),
                                       executed.stderr.decode())
        return packer_command


class ValidationObject():
    pass


class PackerException(Exception):
    pass
