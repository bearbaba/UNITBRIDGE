import json

def test_freeze_delivery_binds_document_headers(direct_vm,direct_deploy,direct_alice):
    c=direct_deploy("contracts/UnitBridge.py")
    direct_vm.sender=direct_alice
    with direct_vm.expect_revert("Document IDs"):
        c.freeze_delivery("case","SKU-A","PO-1","R-1","Order: WRONG\nSKU-A: minimum 5.5 kg net mass required.","Receipt: R-1\nSKU-A: delivered 1 carton.","")
    c.freeze_delivery("case","SKU-A","PO-1","R-1","Order: PO-1\nSKU-A: minimum 5.5 kg net mass required.","Receipt: R-1\nSKU-A: delivered 1 carton.","")
    data=json.loads(c.get_case("case"))
    assert data["order_id"]=="PO-1" and data["receipt_id"]=="R-1"
    assert c.get_protocol_version()=="unitbridge-v2"
