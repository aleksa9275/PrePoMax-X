pmx.model.properties.model_space = 'ThreeD'
pmx.model.properties.unit_system = 'MM_TON_S_C'
pmx.import_file('definitions.inp')
pmx.results.open('cube-results.frd')
print(pmx.results.get_names())
pmx.save('definitions-with-results.pmx')
