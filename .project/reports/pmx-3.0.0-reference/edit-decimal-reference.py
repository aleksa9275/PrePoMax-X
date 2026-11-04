material = pmx.model.materials['XSTEEL']
properties = material.get_properties()
properties[0] = pmx.create.elastic(98765.5, 0.3)
pmx.model.materials.replace('XSTEEL', properties=properties)
pmx.model.steps['Step-1'].loads.replace_concentrated_force('Concentrated_force-1', f1=7.125)
pmx.save('official-decimal-edit.pmx')
pmx.export_to_calculix('official-decimal-edit.inp')
