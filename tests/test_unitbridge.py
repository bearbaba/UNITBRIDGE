import json
import copy
import pytest

ORDER = "SKU-A: minimum 5.5 kg net mass required."
RECEIPT = "SKU-A: delivered 2 cartons."
SPEC = "SKU-A: 12 packs per carton.\nSKU-A: 250 g net per pack."
PATTERN = r"(?s).*Extract material quantity facts.*"
FACTS = {"status":"READY","requirement":{"line":0,"amount":"5.5","unit":"kg"},
         "receipt":{"line":0,"amount":"2","unit":"carton"},
         "conversions":[{"line":0,"amount":"12","child":"pack","parent":"carton"}],
         "mass":{"line":1,"amount":"250","unit":"g","per":"pack"}}

def mock(vm, data):
    vm.clear_mocks()
    vm.mock_llm(PATTERN,json.dumps(json.dumps(data)))

def setup(vm,deploy,alice,order=ORDER,receipt=RECEIPT,spec=SPEC):
    c=deploy("contracts/UnitBridge.py")
    vm.sender=alice
    c.freeze_case("case-a","SKU-A",order,receipt,spec)
    return c

def test_package_chain_exact_math_and_immutable(direct_vm,direct_deploy,direct_alice,direct_bob):
    c=setup(direct_vm,direct_deploy,direct_alice)
    frozen=c.get_case("case-a")
    direct_vm.sender=direct_bob
    with direct_vm.expect_revert("Only case owner"):
        c.reconcile("case-a")
    direct_vm.sender=direct_alice
    mock(direct_vm,FACTS)
    c.reconcile("case-a")
    assert direct_vm.run_validator() is True
    cert=json.loads(c.get_certificate("case-a"))
    assert cert["status"]=="MEETS_MINIMUM" and cert["delta_mg"]==500000
    assert cert["facts"]["delivered_mg"]==6000000
    assert cert["facts"]["required_mg"]==5500000
    assert cert["input_sha256"]==json.loads(frozen)["input_sha256"]
    with direct_vm.expect_revert("already exists"):
        c.reconcile("case-a")
    with direct_vm.expect_revert("duplicate"):
        c.freeze_case("case-a","SKU-A",ORDER,RECEIPT,SPEC)
    assert c.get_case("case-a")==frozen

def test_validator_rejects_forged_factor_mass_and_line(direct_vm,direct_deploy,direct_alice):
    c=setup(direct_vm,direct_deploy,direct_alice)
    mock(direct_vm,FACTS)
    c.reconcile("case-a")
    for key,field,value in (("requirement","amount","4"),("receipt","amount","3"),("mass","amount","500"),("mass","per","carton"),("mass","line",0)):
        bad=copy.deepcopy(FACTS)
        bad[key][field]=value
        mock(direct_vm,bad)
        assert direct_vm.run_validator() is False
    bad=copy.deepcopy(FACTS)
    bad["conversions"][0]["amount"]="24"
    mock(direct_vm,bad)
    assert direct_vm.run_validator() is False
    mock(direct_vm,{"status":"REVIEW"})
    assert direct_vm.run_validator() is False

def test_direct_mass_shortfall_and_review(direct_vm,direct_deploy,direct_alice):
    c=setup(direct_vm,direct_deploy,direct_alice,receipt="SKU-A: delivered 5400 g net.",spec="")
    facts=copy.deepcopy(FACTS)
    facts["receipt"]={"line":0,"amount":"5400","unit":"g"}
    facts["conversions"]=[]
    facts["mass"]=None
    mock(direct_vm,facts)
    c.reconcile("case-a")
    cert=json.loads(c.get_certificate("case-a"))
    assert cert["status"]=="SHORTFALL" and cert["delta_mg"]==-100000
    c.freeze_case("review","SKU-A",ORDER,"SKU-A: delivered 2 cartons.","SKU-A: 250 g gross per pack.")
    mock(direct_vm,{"status":"REVIEW"})
    c.reconcile("review")
    assert direct_vm.run_validator() is True
    assert json.loads(c.get_certificate("review"))["status"]=="REVIEW"

def test_wrong_sku_and_gross_fail_closed(direct_vm,direct_deploy,direct_alice):
    c=setup(direct_vm,direct_deploy,direct_alice,spec="SKU-B: 12 packs per carton.\nSKU-A: 250 g gross per pack.")
    mock(direct_vm,FACTS)
    with direct_vm.expect_revert("No valid grounded extraction"):
        c.reconcile("case-a")
    assert c.get_certificate("case-a")==""
