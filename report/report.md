# Online A/B S3 Architecture Report

## Problem

S3 — Noise in Trotter Simulation is the selected workload.

## Processor contract

The executable benchmark loads the source-document processor definitions directly.

### Processor A

5 qubits, fixed baseline graph, synthetic noise.

### Processor B

7 qubits, heavy-hex-inspired graph, synthetic noise.

## Controlled experiment

The same logical 3-qubit Trotter workload, deterministic logical-to-physical layout, trajectory count and random seed are used for both processors. The A/B processor JSON files supply the physical qubit counts, coupling maps and noise rates.

Solution quality is measured by fidelity to the exact logical reference embedded into the physical register. Circuit depth, two-qubit gates, routing/SWAP overhead, physical qubits, noise rates and reproducibility fields are recorded.

The controlled benchmark enforces identical A/B synthetic error rates so topology/routing effects are not intentionally confounded with different noise parameters.

## Architecture interpretation

The selected workload interacts with logical qubits 0 and 2. With the documented layout, Processor A has a direct 0–2 coupling, while Processor B routes the same interaction through its coupling graph. Each routed interaction uses a forward and reverse SWAP sequence, so the four-step workload produces 0 routing SWAPs on A and 8 on B.

This is a finite-model comparison. It does not establish a universal hardware advantage.

## Bell correlation

The source document places Bell correlation, protection overhead and postselection analysis in the offline C/D stage. Those tools remain separate from the online A/B acceptance path.
