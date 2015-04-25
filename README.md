python-packer
=============

* Master Branch [![Build Status](https://travis-ci.org/nir0s/python-packer.svg?branch=master)](https://travis-ci.org/nir0s/python-packer)
* PyPI [![PyPI](http://img.shields.io/pypi/dm/python-packer.svg)](http://img.shields.io/pypi/dm/python-packer.svg)
* Version [![PypI](http://img.shields.io/pypi/v/python-packer.svg)](http://img.shields.io/pypi/v/python-packer.svg)


A Python client for [packer.io](http://www.packer.io)

The client has been developed vs. Packer v0.7.5.

## Installation

You must have Packer installed prior to using this client (DUH!)

```shell
 pip install python-packer
 # or, for dev:
 pip install https://github.com/nir0s/python-packer/archive/master.tar.gz
```

## Usage Example

```python
import packer

packerfile = 'packer/tests/resources/packerfile.json'
packer_exec_path = '/usr/bin/packer'
exc = []
only = []
vars = {"variable1": "y", "variable2": "value"}
vars_file = 'path/to/vars/file'

p = packer.Packer(packerfile, exc=exc, only=only, vars=vars,
                  vars_file=vars_file, exec_path=packer_exec_path)
print(p.version())  # `packer version`
p.validate(syntax_only=False)  # `packer validate`
result = p.inspect()  # `packer inspect`
print(result.parsed_output)
p.build(parallel=True, debug=False, force=False)  # `packer build`
```

The `inspect` method will return a dictionary containing the components:

```python
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
