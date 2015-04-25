import packer.interface as packer
import os

packerfile = os.path.expanduser('~/repos/cloudify-packager/image-builder/quickstart-vagrantbox/packerfile.json')  # NOQA

# exc = ['z', 't']
exc = []
# only = ['x', 'y']
only = []
# vars = {"variable1": "y", "variable2": "value"}
vars = {}
vars_file = '/x'

p = packer.Packer(packerfile, exc=exc, only=only, vars=vars)
# print(p.version())

print(p.validate(syntax_only=True))
# print(p.build())
