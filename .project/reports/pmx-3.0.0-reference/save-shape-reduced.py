pmx.model.properties.model_space = 'ThreeD'
pmx.model.properties.unit_system = 'MM_TON_S_C'
pmx.import_file('shape-reduced.inp')
pmx.save('shape-reduced.pmx')
pmx.export_to_calculix('shape-reduced-export.inp')
