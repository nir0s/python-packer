import packer

packerfile = 'packer/tests/resources/packerfile.json'
# exc = ['z', 't']
exc = []
# only = ['x', 'y']
only = []
# vars = {"variable1": "y", "variable2": "value"}
vars = {}
vars_file = '/x'

p = packer.Installer('packer_executables/', 'packer_0.7.5_linux_amd64.zip')
# If we installed packer using the provided installer, it will return
# packer's executable path. We can use it below:
# packer_exec = p.install()
packer_exec = 'packer'
p = packer.Packer(packerfile, exc=exc, only=only, vars=vars,
                  exec_path=packer_exec)
# print(p.version())
# validation = p.validate(syntax_only=True)
# print(validation.succeeded)
# print(validation.error)
# result = p.inspect(mrf=True)
# print result.parsed_output
# print(p.fix('TEST.json').fixed)
# print(p.build())
