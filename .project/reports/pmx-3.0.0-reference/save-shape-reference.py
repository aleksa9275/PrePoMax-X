pmx.model.properties.model_space = 'ThreeD'
pmx.model.properties.unit_system = 'MM_TON_S_C'
pmx.import_file('shape-reference.inp')
pmx.save('shape-reference.pmx')
pmx.export_to_calculix('shape-reference-export.inp')
