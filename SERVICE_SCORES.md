# Service scores of the scoring model

Section 3 of the paper gives the coverage score in full. The six other service
scores are built in the same way (weighted sum of normalized KPIs, minus
penalties). Their KPIs, levels, weights and penalties are the authors' judgment.
Only the coverage score has been evaluated.

## Levels and logistic parameters

`L` is the level regarded as bad and `U` the level regarded as good. `a` and `b`
are the slope and the 0.5-point of the logistic normalization. A dash means that
no logistic parameters are set. KPIs that appear below without a row here have
no levels fixed yet.

| KPI | Bad L | Good U | a | b |
|---|---|---|---|---|
| Downlink throughput (Mbps) | 1 | 20 | 0.25 | 5 |
| Uplink throughput (Mbps) | 0.5 | 10 | 0.40 | 3 |
| Round-trip time (ms) | 150 | 30 | 0.04 | 75 |
| TCP retransmission (%) | 10 | 0.5 | 0.30 | 3 |
| Session success rate (%) | 80 | 99 | 0.30 | 92 |
| VoLTE drop rate (%) | 5 | 0 | - | - |
| Call setup time (ms) | 3000 | 500 | - | - |
| Mean opinion score | 2.5 | 4.3 | 2.00 | 3.4 |
| RSRP (dBm) | -110 | -80 | 0.10 | -95 |
| RSRQ (dB) | -15 | -8 | 0.50 | -11.5 |
| SINR (dB) | 0 | 20 | 0.25 | 10 |
| Attach success rate (%) | 85 | 99 | 0.40 | 94 |

Distance to the serving cell is normalized linearly with L = 5 km and U = 0.

## Weights and penalties

A penalty marked "severe" is triggered beyond the bad level above. "Coverage
bad" means RSRP below -110 dBm. The other triggers must be fixed at deployment.
SR = success rate.

| Service | KPI weights | Penalties (points) |
|---|---|---|
| Coverage | RSRP 0.35, RSRQ 0.25, SINR 0.30, distance 0.10 | RSRP < -110 dBm: 15; RSRQ < -15 dB: 10; SINR < 0 dB: 10 |
| PS data | downlink throughput 0.25, uplink throughput 0.10, round-trip time 0.20, TCP retransmission 0.15, session SR 0.20, coverage utility 0.10 | round-trip time severe: 10; retransmission severe: 10; coverage bad: 15; session failure: 15 |
| VoLTE | SIP SR 0.25, drop rate 0.20, call setup time 0.15, mean opinion score 0.20, jitter 0.10, packet loss 0.10 | drop: 25; SIP failure: 15; mean opinion score < 3.0: 15; packet loss severe: 10 |
| Mobility | attach SR 0.25, tracking-area update SR 0.20, service request SR 0.20, handover SR 0.25, delay 0.10 | attach failure: 20; registration failure: 20; handover failure: 15; repeated update failures: 10 |
| CS voice | call setup SR 0.30, call drop rate 0.35, call setup time 0.20, handover SR 0.15 | call drop: 30; setup failure: 20 |
| SMS | delivery SR 0.65, delivery delay 0.35 | delivery failure: 20; delay > 60 s: 10 |
| 5G NR | downlink throughput 0.40, uplink throughput 0.20, NR time rate 0.20, SS-RSRP 0.10, latency 0.10 | none |

## Per-subscriber aggregation

Default weights: PS data 0.30, coverage 0.20, mobility 0.15, VoLTE 0.15, 5G NR
0.10, CS voice 0.05, SMS 0.05, rescaled to sum to one over the services active
in the scoring period.
