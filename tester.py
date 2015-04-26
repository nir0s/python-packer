import packer

packerfile = 'packer/tests/resources/packerfile.json'
# exc = ['z', 't']
exc = []
# only = ['x', 'y']
only = []
# vars = {"variable1": "y", "variable2": "value"}
vars = {}
vars_file = '/x'

p = packer.Packer(packerfile, exc=exc, only=only, vars=vars)
# print(p.version())
# print(p.validate(syntax_only=False))
result = p.inspect(mrf=False)
print result.stdout
# print(p.fix('TEST.json'))
# print(p.build())
