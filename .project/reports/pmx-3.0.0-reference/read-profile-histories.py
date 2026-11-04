import json

histories = pmx.results.history_outputs
selected = (
    ('From_Field-1', 'STRESS', 'MISES'),
    ('From_Field-1_STRESS_MISES_x2', 'TABLE', 'VALUE'),
)
summary = {}
for set_name, field, component in selected:
    data = histories[set_name].fields[field].components[component].entries['51'].get_data()
    summary[set_name] = {'time': list(data.time), 'values': list(data.values), 'unit': data.unit}
print('PMX_HISTORY_REFERENCE=' + json.dumps(summary, sort_keys=True))
