# S3 Engineering Audit Log

## Audit scope

The audit covered execution paths, numerical configuration validation, topology and routing logic, stochastic benchmarking, measurement/readout handling, repository validation, notebook generation and CI.

## Findings and fixes

| Finding | Root cause | Fix |
|---|---|---|
| Dense local-operator construction could scale poorly | Full matrices were used for local gate application | Local RX, RZZ and CX operations now act directly on statevector amplitudes |
| Exact-state propagation could create dense matrices | Dense Hamiltonian/operator construction was used | Exact propagation now uses sparse operators and expm_multiply |
| Trotter inputs were weakly validated | Invalid, non-finite or extreme configuration could reach numerical code | Central validation rejects invalid numeric, probability, topology and trajectory inputs |
| Practice routing was topology-specific | Routing assumptions were tied to the illustrative 0-to-2 example | Routing now derives a shortest path from the coupling graph |
| Routing CX gates were indistinguishable from algorithmic CX gates | Resource accounting used names only | Gate roles distinguish routing from algorithmic operations |
| Practice benchmark stored every trajectory result | Memory scaled linearly with trajectory count | Online mean/variance accumulation is used |
| Bell benchmark did not apply configured readout error | Readout parameters existed but were not used in sampled measurements | An explicit validated readout channel is applied before sampling |
| Bell routing was hardcoded | The runner supplied a fixed routing count | Routing overhead is derived from processor connectivity and ports |
| Processor validation was shallow | Only a few fields were checked | Qubit indices, coupling edges, ports, basis gates and noise probabilities are validated |
| Notebook builder could replace the committed notebook with an incomplete structure | Builder and committed notebook were inconsistent | Builder now defines and generates all 23 required sections; CI checks generated output |
| CI did not validate generated figures or repository state | Tests ran without a complete artifact pipeline | CI now compiles, rebuilds and verifies the notebook, runs tests and both practice benchmarks, generates figures and validates outputs |
| Official validation could accept practice data conceptually | Static validation did not enforce kit provenance | Official validation now requires a Challenge Kit manifest, kit-derived status and official processor source markers |
| Root compliance documentation overstated completion | Kit-dependent requirements were treated as PASS | Engineering readiness and official scientific readiness are reported separately |

## Security and reliability posture

The Python application uses standard-library JSON parsing, explicit input validation and no dynamic eval/exec execution. GitHub Actions uses read-only repository permissions. The benchmark guards statevector memory and trajectory count to reduce accidental resource exhaustion.

## Remaining external dependency

The only remaining blocker to an official competition result is external to the codebase: the organizer-defined S3 Challenge Kit, exact Processor A/B definitions, S3 instance and required output schema. The repository is designed to fail closed until those inputs are integrated.
