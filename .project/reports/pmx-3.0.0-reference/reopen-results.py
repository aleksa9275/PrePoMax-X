names = pmx.results.get_names()
print(names)
if len(names) != 1:
    raise RuntimeError('Expected one embedded result')
pmx.export_to_calculix('definitions-results-reopened-export.inp')
