pmx.model.properties.model_space = 'ThreeD'
pmx.model.properties.unit_system = 'MM_TON_S_C'
pmx.import_file('definitions.inp')
pmx.save('definitions.pmx')
pmx.export_to_calculix('definitions-export.inp')
