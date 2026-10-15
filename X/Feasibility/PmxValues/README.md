# Private engineering-record scalar comparison

Task 0012, research only. Python 3/.NET 10 SDK; no packages/application projects,
payload type loading, BinaryFormatter or array materialization. Uses the trusted
SDK NRBF decoder, as does the earlier inventory probe. Original PMX files stay
outside Git. Temporary bounded graphs are cleaned up.

```sh
python3 X/Feasibility/PmxValues/compare-values.py /private/old.pmx /private/saved.pmx --output /path/to/metadata.json
python3 X/Feasibility/PmxValues/test-values.py
```

Selects CaeModel class records, EquationContainer, UnitSystem and AnalysisJob.
Compares exact member/value bindings within each shallow record, then the
multiset of those records per exact serialized type identity. Floating values
use exact bits. References contribute only serialized type/array shape. Values
and ephemeral keyed fingerprints never appear in output; the report contains
type/member names, equality outcomes, counts and an allowlisted environment-key
classification (unknown keys redacted). No type-version normalization.

This does **not** compare array contents, record-target identity/aliasing,
dictionary order, entity associations, custom mesh/results, document reconstruction
or history replay. Identical multisets cannot prove a material is assigned to the
same section/region. These remain Windows snapshot/reference gates. Three
synthetic controls check equality, scalar mutation and swapped member bindings.

Observed private reference comparison: 27 of 29 selected types match; AnalysisJob
settings and FeModel's new keyword-override reference differ. Do not call the
round-trip fully equivalent. See [local evidence](../../../.project/reports/local-preparation-completion.md).
