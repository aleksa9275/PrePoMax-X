pmx.model.properties.model_space = 'ThreeD'
pmx.model.properties.unit_system = 'MM_TON_S_C'
pmx.import_file('cube.inp')
pmx.save('cube.pmx')
pmx.export_to_calculix('cube-export.inp')
