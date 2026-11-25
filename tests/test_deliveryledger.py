import hashlib
import json
from genlayer.types import Address


def seal(data,cert):
    data=dict(data)
    data["input_sha256"]=hashlib.sha256(json.dumps(data,sort_keys=True).encode("utf-8")).hexdigest()
    return data,dict(cert,case_id=data["case_id"],input_sha256=data["input_sha256"])


def mock_view(monkeypatch, records, protocol):
    import genlayer as gl
    class View:
        def view(self): return self
        def get_protocol_version(self): return protocol
        def get_case(self,cid): return json.dumps(records[cid][0]) if cid in records else ""
        def get_certificate(self,cid): return json.dumps(records[cid][1]) if cid in records else ""
    monkeypatch.setattr(gl.contract,"get_at",lambda _:View())

def setup(vm,deploy,alice,bob,monkeypatch):
    owner=Address(alice).as_hex.lower()
    other=Address(bob).as_hex.lower()
    c=deploy("contracts/DeliveryLedger.py","0x"+"9"*40)
    records={}
    for cid,rid,amount,order in (("part1","R1",3000000,"Order: PO1"),("part2","R2",3000000,"Order: PO1"),("duplicate","R1",3000000,"Order: PO1"),("wrong","R3",3000000,"Order: OTHER")):
        records[cid]=seal({"case_id":cid,"owner":owner,"order_id":"PO1","receipt_id":rid,"sku":"SKU-A","order":order,"receipt":"Receipt: "+rid,"spec":"spec"},{"sku":"SKU-A","status":"SHORTFALL","delta_mg":amount-5500000,"facts":{"status":"READY","required_mg":5500000,"delivered_mg":amount}})
    mock_view(monkeypatch,records,"unitbridge-v2")
    vm.sender=alice
    c.open_order("ledger","part1",other)
    return c,records,other


def test_partial_to_fulfilled_and_replay(direct_vm,direct_deploy,direct_alice,direct_bob,direct_charlie,monkeypatch):
    vm=direct_vm
    c,records,other=setup(vm,direct_deploy,direct_alice,direct_bob,monkeypatch)
    with vm.expect_revert("Supplier"):
        c.accept_order("ledger")
    vm.sender=direct_bob
    c.accept_order("ledger")
    vm.sender=direct_alice
    c.propose_delivery("ledger","b1","part1")
    assert json.loads(c.get_order("ledger"))["received_mg"]==0
    with vm.expect_revert("Supplier must"):
        c.resolve_delivery("ledger","b1",True)
    vm.sender=direct_charlie
    with vm.expect_revert("authorized"):
        c.resolve_delivery("ledger","b1",True)
    vm.sender=direct_bob
    c.resolve_delivery("ledger","b1",True)
    rec=json.loads(c.get_order("ledger"))
    assert rec["status"]=="PARTIAL" and rec["remaining_mg"]==2500000
    vm.sender=direct_alice
    with vm.expect_revert("Receipt ID already"):
        c.propose_delivery("ledger","replay","duplicate")
    with vm.expect_revert("Duplicate batch"):
        c.propose_delivery("ledger","replay","part1")
    with vm.expect_revert("does not match"):
        c.propose_delivery("ledger","wrong","wrong")
    c.propose_delivery("ledger","b2","part2")
    vm.sender=direct_bob
    c.resolve_delivery("ledger","b2",True)
    rec=json.loads(c.get_order("ledger"))
    assert rec["status"]=="FULFILLED" and rec["received_mg"]==6000000 and rec["remaining_mg"]==0 and rec["overage_mg"]==500000
    assert rec["accepted_batches"]==2
    with vm.expect_revert("authorized"):
        c.resolve_delivery("ledger","b2",True)


def test_declined_receipt_reserved_and_no_credit(direct_vm,direct_deploy,direct_alice,direct_bob,monkeypatch):
    vm=direct_vm
    c,records,other=setup(vm,direct_deploy,direct_alice,direct_bob,monkeypatch)
    with vm.expect_revert("Duplicate order"):
        c.open_order("other","part2",other)
    vm.sender=direct_bob
    c.accept_order("ledger")
    vm.sender=direct_alice
    c.propose_delivery("ledger","b1","part1")
    c.resolve_delivery("ledger","b1",False)
    assert json.loads(c.get_batch("b1"))["status"]=="DECLINED"
    assert json.loads(c.get_order("ledger"))["received_mg"]==0
    with vm.expect_revert("Receipt ID already"):
        c.propose_delivery("ledger","again","duplicate")


def test_certificate_binding_and_review(direct_vm,direct_deploy,direct_alice,direct_bob,monkeypatch):
    c,records,other=setup(direct_vm,direct_deploy,direct_alice,direct_bob,monkeypatch)
    data={k:v for k,v in records["part1"][0].items() if k!="input_sha256"}
    records["review"]=seal(dict(data,case_id="review",order_id="NEW"),{"sku":"SKU-A","status":"REVIEW","facts":{"status":"REVIEW"}})
    with direct_vm.expect_revert("Grounded quantity"):
        c.open_order("review","review",other)
    records["part2"][1]["input_sha256"]="forged"
    with direct_vm.expect_revert("binding mismatch"):
        c.open_order("forged","part2",other)
