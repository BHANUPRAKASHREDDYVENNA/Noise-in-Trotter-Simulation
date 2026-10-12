# Online A/B S3 Architecture Report

## Problem
S3 — Noise in Trotter Simulation is the selected workload.

## Contract
The repository treats `docs/source_document.md` as the sole specification.

## Processor A
5 qubits, fixed baseline graph, synthetic noise model.

## Processor B
7 qubits, heavy-hex-inspired graph, contemporary compilation baseline.

## Controlled experiment
The same logical Trotter workload, control parameters, trajectory count and deterministic seed are used for both processors. The benchmark records solution quality, uncertainty, depth, two-qubit gate count, routing/SWAP overhead, physical qubit count, noise assumptions and reproducibility fields.

## Interpretation
Routing is derived from the coupling graph. Architectural conclusions are tied to measured differences in circuit cost and the configured noise model.

## Bell correlation
The source document places Bell correlation and protection in the offline C/D stage; the repository keeps Bell tooling separate from the online A/B metric.
