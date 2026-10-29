Geometry-aware
quantum cloud challenge

Hackathon overview


Qiskit Fall Fest 2026

Steven Rayan
quanTA, University of Saskatchewan

Connectivity, routing and noise

Quantum circuits often require
interactions between qubits that
are not directly connected.

Routing introduces extra operations to realize
those interactions. Under noise, these
operations can reduce the quality of the result.   Two designated ports


Qiskit Fall Fest 2026                                             QFF   02

quanTA research and the cloud context

 Geometry and error protection
 quanTA's research connects circuit diagrams and quantum error correction with
 questions about the geometry of physical implementations.

 Hyperbolic superconducting architectures
 Finite hyperbolic lattices motivate alternative patterns of connections and
 cycles. This challenge tests their consequences for routing and error-detection
 circuits.
 A decade of cloud access
 IBM opened its five-qubit cloud processor in 2016. Qiskit now provides a
 common framework for comparing historical, contemporary and hypothetical
 processor models.

Qiskit Fall Fest 2026                                                     QFF   03

Processor models across stages

         Processor A - Online      Processor B - Online      Processor C - Shortlisted
                   5 qubits                 7 qubits                  8-10 qubits


          Fixed baseline graph    Heavy-hex-inspired graph
          Synthetic noise model   Contemporary compilation
                                         baseline             Experimental coupling graph
                                                               Released after shortlisting
                                                                  Circuit-level model


Qiskit Fall Fest 2026                                                        QFF   04

Challenge objective

 Online Phase: benchmark your selected solution on Processor A
 and Processor B.

 Build both processors from the provided definitions, run the same controlled experiment, and
 compare architecture-aware metrics.

 After shortlisting, Processor C is introduced and teams design Processor D. The Bell-correlation
 challenge is completed offline using C and D.

Qiskit Fall Fest 2026                                                                        QFF   05

The Bell-correlation task

                                                                            Verification correlations
        |0⟩             H
                                                                            XX        YY         ZZ
                                          compile and route
                                                                          Together, these estimate
        |0⟩
                                                                         fidelity with the target Bell
                                                                                     state.

 The Bell-correlation experiment is reserved for the offline final. Shortlisted teams compare C and D using
 fidelity, circuit cost, routing overhead and protection results.

Qiskit Fall Fest 2026                                                                         QFF   06

Core comparison

    Stage / processor                                      Ideal / reference                 Noisy baseline                 Final analysis

    Processor A - Online                                        Case A1                          Case A2
                                                                                                                         A/B architecture metrics

    Processor B - Online                                        Case B1                          Case B2
                                                                                                                         A/B architecture metrics

    Processor C + D - Offline                                 Case C/D-1                        Case C/D-2
                                                                                                                         Bell + protection analysis

 Online: compare A/B using solution quality, circuit cost, routing and noise-aware architecture metrics. Offline: analyze C/D with Bell correlation
 and protection overhead.

Qiskit Fall Fest 2026                                                                                                                  QFF   07

Protection strategies

 Parity or stabilizer checks

 Additional measurements can reveal particular errors without directly
 measuring the encoded information.

 Syndrome postselection

 Keep outcomes that pass a specified check. Any improvement in
 conditional fidelity must be reported together with the fraction of accepted
 shots.

 Geometry-aware encodings

 More advanced teams can adapt an encoding or check network to the
 available connections, then measure its overhead.

Qiskit Fall Fest 2026                                                QFF   08

Challenge rules

 Stage the work as follows: online teams use only Processor A and Processor B. Shortlisted teams receive Processor C and design Processor D for the offline challenge.

 Choose the implementation, routing method and analysis strategy for the A/B benchmark.

 Use the same selected problem, controlled settings and reporting format on A and B. Submit reproducible results and architecture-aware metrics.

 After shortlisting, choose the Processor D topology and justify it using observations from A, B and the newly introduced C.

 Offline teams run the C/D experiment, perform Bell correlation, and report fidelity, circuit cost, routing overhead and protection results.

 Optional studies and QPU results may be included, but must remain separate from the common benchmark.

Qiskit Fall Fest 2026                                                                            QFF   09

Required measurements

 Online A/B benchmark
 Measure                     Report

 Solution quality            Problem-specific output / reference comparison

 Circuit cost                Depth and number of two-qubit gates

 Routing                     SWAP overhead and connectivity effects

 Qubit use                   Physical qubits, including ancillas

 Noise / reproducibility     Noise impact, assumptions and repeatability

 Offline C/D final: add Bell fidelity with uncertainty, XX, YY, ZZ, protection overhead and postselection yield.

Qiskit Fall Fest 2026                                                                                                           QFF   10

Approaches for different experience levels

    Experience                                 Suggested approach                                          Main comparison

    Explorer            Implement the selected PS and compare Processor A vs B.
                        A/B architecture metrics

    Builder             Improve placement, routing or noise-aware execution on A/B.
                        Fidelity / solution quality versus circuit cost

    Research            After shortlisting, study C and design D; analyze Bell correlation offline.
                        C/D architecture, Bell fidelity and protection overhead

Qiskit Fall Fest 2026                                                                                                         QFF   11

Interpreting the comparison

 Noise and compilation

 Relate changes in fidelity to the operations introduced by compilation and
 to the assumed noise model.

 Protection overhead

 Assess whether the protection method compensates for its extra gates,
 ancillas and discarded shots.

 Architectural conclusions

 Distinguish connectivity effects from differences in gate sets or noise. A
 result from one finite model does not establish a universal advantage.

Qiskit Fall Fest 2026                                                 QFF   12

Required submission materials

 01  Phase-1 reproducible notebook
     Qiskit code, assumptions, Processor A/B definitions and recorded results

 02  A/B graphs and circuits
     The two coupling graphs, transpiled circuits and architecture metrics

 03  Online quantitative comparison
     Problem-specific quality, circuit cost, routing, qubit use and noise-aware results

 04  Scientific interpretation
     An explanation of the A/B results, limitations and architecture trade-offs

 05  Offline final package
     C/D design, Bell-correlation results, protection analysis and final technical explanation

Qiskit Fall Fest 2026                                                                                  QFF   13

Evaluation criteria

 Scientific correctness and reproducibility
     Correct implementation, reproducible methods and trustworthy results.

 Quality of architecture comparison
     Evidence-based comparison of the required processor stages.

 Protection / Bell-correlation analysis
     For the offline final: Bell correlation, protection strategy and overhead.

 Effective use of Qiskit
     Appropriate use of Qiskit, transpilation and experiment tooling.

 Technical interpretation
     Clear explanation of results, limitations and engineering implications.

 Clarity of presentation
     Clear final communication, documentation and technical defense.

Qiskit Fall Fest 2026                                                                                                  QFF   14
