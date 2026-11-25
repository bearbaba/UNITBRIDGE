# V2 Studionet walkthrough (expected, not yet executed)

Deploy UnitBridge (no args); deploy DeliveryLedger(anchor_address=UnitBridge address). Use buyer A and supplier B.

Use the same exact order and spec for both cases:
Order (two lines):
```
Order: PO-001
SKU-A: minimum 5.5 kg net mass required.
```
Spec:
```
SKU-A: 12 packs per carton.
SKU-A: 250 g net per pack.
```
First receipt:
```
Receipt: R-001
SKU-A: delivered 1 carton.
```
Second receipt:
```
Receipt: R-002
SKU-A: delivered 12 packs.
```

1. A: freeze_delivery("ub-first","SKU-A","PO-001","R-001",order,first receipt,spec)
2. A: reconcile("ub-first"). Expect 3,000,000 mg delivered; SHORTFALL.
3. A: DeliveryLedger.open_order("ub-order","ub-first",B address)
4. B: accept_order("ub-order"). OPEN, zero credited.
5. A: propose_delivery("ub-order","ub-batch1","ub-first"). Pending, zero credited.
6. B: resolve_delivery("ub-order","ub-batch1",true). PARTIAL, 3,000,000 mg received and 2,500,000 mg remaining.
7. A: freeze_delivery("ub-second","SKU-A","PO-001","R-002",order,second receipt,spec)
8. A: reconcile("ub-second"). Expect 3,000,000 mg.
9. A: propose_delivery("ub-order","ub-batch2","ub-second")
10. B: resolve_delivery("ub-order","ub-batch2",true). FULFILLED, 6,000,000 mg received, 0 remaining, 500,000 mg overage.
11. Read get_order, get_batch for both batches, and source certificates. Record finalized hashes and readbacks.

Negative checks: duplicate receipt ID with fresh case, wrong order/spec/SKU, malformed source headers, REVIEW, unauthorized confirmation and repeated confirmation fail closed. Parties attest claims; physical delivery is not independently proven. Use public synthetic data.
