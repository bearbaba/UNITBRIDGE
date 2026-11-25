# UNITBRIDGE — Consensus-verified quantity reconciliation

A reusable GenLayer primitive for reconciling minimum **net mass** obligations against delivery documents with inconsistent units and nested package sizes. AI extracts material facts; exact integer arithmetic decides the result. No frontend, model API key, payment or oracle required.

## V2: two linked Intelligent Contracts

**UnitBridge** reconciles each evidence bundle using independent validator extraction and exact mg arithmetic. **DeliveryLedger** reads actual certificates and source from the configured UnitBridge contract, checks protocol and SHA-256 input binding, and anchors a single order/SKU and packaging specification. Supplier accepts the order; buyer proposes individually reconciled deliveries; supplier confirms each before any quantity is credited. Cumulative received, remaining and overage are deterministic. Order, certificate and receipt IDs cannot be reused; declined batches reserve their IDs; max 256 batches. No additional batches after fulfillment. Receipt IDs are unique per buyer, and source headers bind them. These protections cannot establish physical delivery or detect colluding parties inventing fresh receipt identifiers. No custody or payments.

Deploy UnitBridge first, then DeliveryLedger with its actual address. Use V2 `freeze_delivery` for ledger-eligible cases. See [V2 walkthrough](docs/v2-walkthrough.md).

## Example (synthetic)
Deploy `contracts/UnitBridge.py` in [GenLayer Studio](https://studio.genlayer.com/), no constructor args. Use Studionet test tokens.
1. `freeze_case("unit-01", "SKU-A", "SKU-A: minimum 5.5 kg net mass required.", "SKU-A: delivered 2 cartons.", "SKU-A: 12 packs per carton.\\nSKU-A: 250 g net per pack.")` — use an actual newline between the two spec lines.
2. `reconcile("unit-01")` from the same wallet; wait for finality and successful execution.
3. Read `get_case("unit-01")` and `get_certificate("unit-01")`.
Expected: 2 × 12 × 250 g = 6,000,000 mg; required 5,500,000 mg; delta +500,000 mg; MEETS_MINIMUM. Exact source lines and conversion trail appear in certificate.
4. New case with receipt "SKU-A: delivered 5400 g net." and empty spec → SHORTFALL, delta -100,000 mg.
5. New case with only gross mass or missing packaging factor → REVIEW (or invalid model extraction rejected; no false certificate).

## State and consensus
The wallet freezes item ID, order, receipt and packaging specification. SHA-256 binds the exact input; only that wallet may reconcile, once. Each validator independently extracts obligation, actual receipt and conversion path from the same frozen documents. The deterministic normalizer validates exact full evidence lines, SKU boundaries, numeric-unit tokens, ordered explicit per-package factors, no cycles and explicit net mass. Validators compare canonical fields including evidence and computed quantities. The contract applies exact milligram arithmetic; no float, model-generated verdict, or fabricated unit factor. Model disagreement prevents agreement; valid consensus REVIEW produces no delta.

## Bounds and trust
One SKU, one explicit minimum net mass requirement, one actual delivered quantity. Each cited line must contain SKU; use one item line in each order and receipt, explicit `minimum`/`at least` and `delivered`/`received` markers, and attach `net` to the mass token. Duplicate factors and conditional or negated evidence fail closed. Supports mg/g/kg; direct net mass or carton/pack/case/box/bag/pallet/unit counts with at most two nested factors. Packaging evidence uses explicit "12 packs per carton" and "250 g net per pack". Integers for packages, exact mg precision, positive quantities, maximum 10^18 mg. No density, net/gross inference, multi-lot aggregation, tolerance, exact/max order, legal settlement or proof of physical delivery. Source documents are caller-attested, not independently authenticated. Model consensus is not proof that documents are true.

## Reproduce tests
`python -m pip install genvm-linter==0.11.1rc2 genlayer-test==0.30.0 "pytest>=8,<9"`
`genvm-lint lint contracts/UnitBridge.py`
`genvm-lint check contracts/UnitBridge.py`
`pytest -q tests/`
Direct-mode tests mock model extraction and replay validators; actual AI consensus requires separate Studionet verification. See [evidence status](docs/evidence.md).
