material = pmx.model.materials['XSTEEL']
properties = material.get_properties()
properties[0] = pmx.create.elastic(105000, 0.3)
pmx.model.materials.replace('XSTEEL', properties=properties)
pmx.model.steps['Step-1'].loads.replace_concentrated_force('Concentrated_force-1', f1=50)
pmx.save('definitions-edited.pmx')
pmx.export_to_calculix('definitions-edited-export.inp')
