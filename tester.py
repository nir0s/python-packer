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
# validation = p.validate(syntax_only=True)
# print(validation.succeeded)
# print(validation.error)
# result = p.inspect(mrf=True)
# print result.parsed_output
# print(p.fix('TEST.json').fixed)
# print(p.build())
