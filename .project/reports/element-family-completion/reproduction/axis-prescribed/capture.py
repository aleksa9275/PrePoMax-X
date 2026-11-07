pmx.model.properties.model_space = 'Axisymmetric'
pmx.model.properties.unit_system = 'MM_TON_S_C'
pmx.import_file('mesh.inp')
pmx.model.properties.model_space = 'Axisymmetric'
pmx.model.materials.add('Elastic',[pmx.create.elastic(1000,0)])
pmx.model.sections.add_solid('Section','Elastic',pmx.create.selection_by_ids('femodel','elements','elements',[1]),thickness=1)
step=pmx.model.steps.add_static('Static',solver_type='Default',incrementation_type='Automatic',initial_time_increment=1,time_period=1,min_time_increment=1e-5,max_time_increment=1,output_frequency=1)
step.bcs.add_displacement_rotation('Radial',pmx.create.region('NodeSetName','ALL'),u1=0)
step.bcs.add_displacement_rotation('Base',pmx.create.region('NodeSetName','ROOT'),u2=0)
step.bcs.add_displacement_rotation('Extension',pmx.create.region('NodeSetName','TIP'),u2=.001)
step.history_outputs.add_nodal('Tip-history',pmx.create.region('NodeSetName','TIP'),['U','RF'])
pmx.save('original.pmx')
pmx.export_to_calculix('original.inp')
