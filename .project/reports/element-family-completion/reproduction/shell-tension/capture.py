pmx.model.properties.model_space = 'ThreeD'
pmx.model.properties.unit_system = 'MM_TON_S_C'
pmx.import_file('source.inp')
pmx.save('original.pmx')
pmx.export_to_calculix('original.inp')
