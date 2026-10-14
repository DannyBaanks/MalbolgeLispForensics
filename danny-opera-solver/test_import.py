from danny.dsl import parse_dannyscript
spec = parse_dannyscript('target "Hello"')
print(spec.target)