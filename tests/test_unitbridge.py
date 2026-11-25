import json
import pytest

PATTERN=r"(?s).*Classify sensor metadata.*"

def mock(vm, kind):
    vm.clear_mocks()
    vm.mock_llm(PATTERN,json.dumps(json.dumps({"kind":kind})))

def test_registration_exact_conversion_and_validator(direct_vm,direct_deploy,direct_alice):
    c=direct_deploy("contracts/UnitBridge.py")
    direct_vm.sender=direct_alice
    mock(direct_vm,"AIR")
    c.register_source("air-c","room-1","C","Absolute temperature of room air")
    assert direct_vm.run_validator() is True
    mock(direct_vm,"SURFACE")
    assert direct_vm.run_validator() is False
    p=json.loads(c.get_source("air-c"))
    assert p["status"]=="ACTIVE" and p["kind"]=="AIR"
    assert json.loads(c.normalize("air-c",20000,500))=={"center_ticks":2638350,"lower_ticks":2633850,"upper_ticks":2642850,"ticks_per_kelvin":9000}
    mock(direct_vm,"AIR")
    c.register_source("air-f","room-1","F","Absolute temperature of room air")
    assert json.loads(c.normalize("air-f",68900,900))["lower_ticks"]==2638350
    c.register_source("air-k","room-1","K","Absolute temperature of room air")
    assert json.loads(c.normalize("air-k",293150,500))==json.loads(c.normalize("air-c",20000,500))

def test_review_and_input_guards(direct_vm,direct_deploy,direct_alice):
    c=direct_deploy("contracts/UnitBridge.py")
    direct_vm.sender=direct_alice
    mock(direct_vm,"REVIEW")
    c.register_source("unknown","room-1","C","Temperature change or apparent temperature")
    assert json.loads(c.get_source("unknown"))["status"]=="REVIEW"
    with direct_vm.expect_revert("Source not active"):
        c.normalize("unknown",1000,0)
    with direct_vm.expect_revert("duplicate"):
        c.register_source("unknown","room-1","C","Room air")
    with direct_vm.expect_revert("single-line"):
        c.register_source("bad","room-1","C","A\nB")
    mock(direct_vm,"AIR")
    c.register_source("good","room-1","C","Room air")
    with direct_vm.expect_revert("Physical range"):
        c.normalize("good",-274000,0)
    with direct_vm.expect_revert("Physical range"):
        c.normalize("good",20000,11000)

def test_invalid_model_schema_fails(direct_vm,direct_deploy,direct_alice):
    c=direct_deploy("contracts/UnitBridge.py")
    direct_vm.sender=direct_alice
    mock(direct_vm,"FAKE")
    with direct_vm.expect_revert("No valid classification"):
        c.register_source("x","room-1","C","Room air")
    assert c.get_source("x")==""
