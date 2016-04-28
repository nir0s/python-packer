python-packer
=============

[![Build Status](https://travis-ci.org/nir0s/python-packer.svg?branch=master)](https://travis-ci.org/nir0s/python-packer)
[![PyPI](http://img.shields.io/pypi/dm/python-packer.svg)](http://img.shields.io/pypi/dm/python-packer.svg)
[![PypI](http://img.shields.io/pypi/v/python-packer.svg)](http://img.shields.io/pypi/v/python-packer.svg)


A Python interface for [packer.io](http://www.packer.io)

## Packer version

The interface has been developed vs. Packer v0.7.5.


## Installation

You must have Packer installed prior to using this client though as installer class is provided to install packer for you.

```shell
 pip install python-packer

 # or, for dev:
 pip install https://github.com/nir0s/python-packer/archive/master.tar.gz
```

## Usage Examples

### [Packer.build()](https://www.packer.io/docs/command-line/build.html)

```python
import packer

packerfile = 'packer/tests/resources/packerfile.json'
exc = []
only = ['my_first_image', 'my_second_image']
vars = {"variable1": "value1", "variable2": "value2"}
var_file = 'path/to/var/file'
packer_exec_path = '/usr/bin/packer'

p = packer.Packer(packerfile, exc=exc, only=only, vars=vars,
                  var_file=var_file, exec_path=packer_exec_path)
p.build(parallel=True, debug=False, force=False)
```


### [Packer.fix()](https://www.packer.io/docs/command-line/fix.html)

```python
...

p = packer.Packer(packerfile, ...)
output_file = 'packer/tests/resources/packerfile_fixed.json'
print(p.fix(output_file))
```

The `output_file` parameter will write the output of the `fix` function to a file.


### [Packer.inspect()](https://www.packer.io/docs/command-line/inspect.html)

A `-machine-readable` (mrf) argument is provided.

If the `mrf` argument is set to `True`, the output will be parsed and an object containing the parsed output will be exposed as a dictionary containing the components:

```python
...

p = packer.Packer(packerfile, ...)
result = p.inspect(mrf=True)
print(result.parsed_output)
# print(result.stdout) can also be used here

# output:
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
```

If the `mrf` argument is set to `False`, the output will not be parsed but rather returned as is:

```python
...

p = packer.Packer(packerfile, ...)
result = p.inspect(mrf=True)
print(result.stdout)

# output:
Optional variables and their defaults:

  aws_access_key          = {{env `AWS_ACCESS_KEY_ID`}}
  aws_secret_key          = {{env `AWS_ACCESS_KEY`}}

Builders:

  amazon                   (amazon-ebs)

Provisioners:

  shell

...

```


### [Packer.push()](https://www.packer.io/docs/command-line/push.html)

You must be logged into Atlas to use the `push` function:

```python
...

p = packer.Packer(packerfile, ...)
atlas_token = 'oi21mok3mwqtk31om51o2joj213m1oo1i23n1o2'
p.push(create=True, token=atlas_token)
```

### [Packer.validate()](https://www.packer.io/docs/command-line/validate.html)

```python
...

p = packer.Packer(packerfile, ...)
p.validate(syntax_only=False)
```

### Packer.version()

```python
...

p = packer.Packer(packerfile, ...)
print(p.version())
```

### PackerInstaller.install()

This installs packer to `packer_path` using the `installer_path` and verifies that the installation was successful.

```python

packer_path = '/usr/bin/'
installer_path = 'Downloads/packer_0.7.5_linux_amd64.zip'

p = packer.Installer(packer_path, installer_path)
p.install()
```

## Shell Interaction

The [sh](http://amoffat.github.io/sh/) Python module is used to execute Packer.
As such, return values from all functional methods (`validate`, `build`, etc..) other than the `version` method
will return an `sh` execution object. This is meant for you to be able to read stdout, stderr, exit codes and more after executing the commands. With the progression of `python-packer` less abstract objects will return and more concise return values will be provided.

Additionally, to verify that all errors return with as much info as possible, error handling is done gently. Most errors will raise an `sh` exception so that you're able to interact with them. Again, as this module progresses, these exceptions will be handled properly.


## Testing

Please contribute. Currently tests are not really developed.

```shell
git clone git@github.com:nir0s/python-packer.git
cd python-packer
pip install tox
tox
```

## Contributions..

..are always welcome.
