# UNITBRIDGE — Studionet evidence (25 November 2026)

## Evidence scope
Developer-captured Explorer transaction records and Studio readbacks, not an independent RPC verification, deployed bytecode comparison, or audit. All 15 calls reported FINALIZED / Accepted with five initial validators and Normal execution. TX01–TX14 returned SUCCESS; TX15 intentionally returned ERROR / Rollback ("Unauthorized or duplicate reading"). Deployment transaction hashes were not supplied. The readings are synthetic wallet-attested inputs, not actual sensor measurements. Three addresses are distinct, not proof of three independent persons.

Source: `9e1489e6e3ef7903c7b18b37e5281510ac2e33ff`. [CI run](https://github.com/bearbaba/UNITBRIDGE/actions/runs/45569760724): 7 tests passed; lint and SDK checks passed. CI mocks AI responses and registry reads.

## Contracts
- UnitBridge: [Studio](https://studio.genlayer.com/?import-contract=0xeCC2A2C9D1AeCAe3f9aE1E8aF2f7056D2e8C2dfE) / [Explorer address](https://explorer-studio.genlayer.com/address/0xeCC2A2C9D1AeCAe3f9aE1E8aF2f7056D2e8C2dfE)
- SensorFusion: [Studio](https://studio.genlayer.com/?import-contract=0xe423938e5928ca80E5c2D7aF6c7A613997a309FA) / [Explorer address](https://explorer-studio.genlayer.com/address/0xe423938e5928ca80E5c2D7aF6c7A613997a309FA)

## All transaction hashes
Open [Studionet Explorer](https://explorer-studio.genlayer.com/txs) and search the full hash. Direct transaction URL routing was not independently confirmed.

| TX | Contract | Wallet | Method | Input | Hash | GenVM result |
|---|---|---|---|---|---|---|
| 01 | UnitBridge | A | register_source | air-c | `0xfb5a9fb54764bb7a14cc2dd9afff85bbfb0967dd43fdca7758fcdede5bc5cabd` | SUCCESS |
| 02 | UnitBridge | B | register_source | air-f | `0xd2dc18ec4c1f0278716f02a393064c92663634eb74652e24f15e2c02bcf583f1` | SUCCESS |
| 03 | SensorFusion | A | open_round | agreement | `0x4a7833e60f0564890b4f6cc4ce8eaebb73364ec0a3715a1af3e960dc0bffe579` | SUCCESS |
| 04 | SensorFusion | A | submit_reading | agreement / air-c | `0xc5a1495ec3a045117c76c744fd14a2cc3071fc1d8ac03b3ce8aa0cb0d000fb60` | SUCCESS |
| 05 | SensorFusion | B | submit_reading | agreement / air-f | `0x0aea9036d9422eecbd8b410d562a5a4707fe47342bbeef5aa31bd29e80f19f21` | SUCCESS |
| 06 | SensorFusion | A | open_round | conflict | `0x85ae4c8c1bcfeda8b39c42efdd85f0e6de75201b24a2a3fda4bb5c10a284e0b1` | SUCCESS |
| 07 | SensorFusion | A | submit_reading | conflict / air-c | `0x6da961d93d99e215431bdc1966002a2713ae86366ba6641222474ad6463bdd52` | SUCCESS |
| 08 | SensorFusion | B | submit_reading | conflict / air-f | `0xdfcd8275de89a572cf1858ee8359c23a854862c162f931542eb4c6795f203223` | SUCCESS |
| 09 | UnitBridge | C | register_source | air-k | `0x0f7d5ebeac4deca8cc2e002937d30a813d09148a40eb00e86b13d33488630b4e` | SUCCESS |
| 10 | SensorFusion | A | open_round | majority | `0xbcc17b4649b2b82ab19658b0506bb9867360864767454f03e5e5365b40c4e378` | SUCCESS |
| 11 | SensorFusion | A | submit_reading | majority / air-c | `0x63c0b64284cb31a283a758edbb2e7d72a78cd94c4b7cb2c6a1557b4d57c9281e` | SUCCESS |
| 12 | SensorFusion | B | submit_reading | majority / air-f | `0x50de23cf5630c1fd93ee10cbb2654cbd03632f552037433bb8f7287380b3a2c3` | SUCCESS |
| 13 | SensorFusion | C | submit_reading | majority / air-k | `0xbb191c5e6231e712a9d4cb39c31d93f47b9f8392cfc77cc0f5a77fb77f059978` | SUCCESS |
| 14 | UnitBridge | C | register_source | unclear | `0x71e0026a2bfb0665a13bee0193bb80dd4c5d12c8bd78780a944e0a6607000358` | SUCCESS |
| 15 | SensorFusion | C | submit_reading | majority / air-k replay | `0x3a6e4da153418ef1cec68337775dae140fe04420a34f0949cb51cdbafbc8db8b` | Expected rollback |

## Readback evidence
See [captured JSON](readbacks-2026-11-25.json) (parsed from developer-provided Studio strings).
- agreement: C and F, peak 2/2, interval [2638350,2642850] ticks = 20–20.5 °C.
- conflict: C and F, peak 1/2, no interval.
- majority: C/F/K, peak 2/3; air-k excluded; interval unchanged at 20–20.5 °C.
- unclear: AI consensus output REVIEW; persisted source kind and status REVIEW.
- replay: same air-k report submitted after majority round closed; expected rollback and subsequent get_round readback exactly matches pre-replay state. This shows post-finalization replay rejection; in-flight duplicates and incompatible profiles are covered in mocked CI tests.

## Historical experiment (not counted)
The abandoned delivery design had a failed Studio call (0x5d585351cabea66287bcd52aa49426246522bc720a1d276332a4bcc2e190fcf6) due to single-line input handling. That design and its deployments are obsolete; only sensor-interoperability contracts above are the submission.
