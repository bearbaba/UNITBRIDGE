import json

def setup(vm,deploy,alice,bob,charlie,monkeypatch):
    c=deploy("contracts/SensorFusion.py","0x"+"9"*40)
    from genlayer.types import Address
    import genlayer as gl
    profiles={}
    for sid,owner,unit,kind,site in [
        ("a",alice,"C","AIR","room"),("b",bob,"F","AIR","room"),("c",charlie,"K","AIR","room"),
        ("surface",bob,"C","SURFACE","room"),("other",bob,"C","AIR","other"),("same",alice,"F","AIR","room"),
        ("review",bob,"C","REVIEW","room")]:
        profiles[sid]={"source_id":sid,"owner":Address(owner).as_hex.lower(),"unit":unit,"kind":kind,"site":site,
                       "status":"REVIEW" if kind=="REVIEW" else "ACTIVE","label":sid}
    class View:
        def view(self): return self
        def get_protocol_version(self): return "sensor-interop-1"
        def get_source(self,sid): return json.dumps(profiles[sid]) if sid in profiles else ""
        def normalize(self,sid,v,u):
            unit=profiles[sid]["unit"]
            center=v*9+2458350 if unit=="C" else ((v-32000)*5+2458350 if unit=="F" else v*9)
            radius=u*(5 if unit=="F" else 9)
            return json.dumps({"center_ticks":center,"lower_ticks":center-radius,"upper_ticks":center+radius,"ticks_per_kelvin":9000})
    monkeypatch.setattr(gl.contract,"get_at",lambda _:View())
    vm.sender=alice
    return c,profiles

def get(c,r): return json.loads(c.get_round(r))

def test_agreement_conflict_and_replay(direct_vm,direct_deploy,direct_alice,direct_bob,direct_charlie,monkeypatch):
    vm=direct_vm
    c,_=setup(vm,direct_deploy,direct_alice,direct_bob,direct_charlie,monkeypatch)
    c.open_round("r",'["a","b"]',2)
    c.submit_reading("r","a",20000,500)
    assert get(c,"r")["status"]=="OPEN"
    with vm.expect_revert("Unauthorized"):
        c.submit_reading("r","a",20000,500)
    with vm.expect_revert("Unauthorized"):
        c.submit_reading("r","b",68900,900)
    vm.sender=direct_bob
    c.submit_reading("r","b",68900,900)
    r=get(c,"r")
    assert r["status"]=="AGREEMENT" and r["result"]["interval"]==[2638350,2642850]
    with vm.expect_revert("Unauthorized"):
        c.submit_reading("r","b",68900,900)
    c.open_round("conflict",'["a","b"]',2)
    c.submit_reading("conflict","b",90000,900)
    vm.sender=direct_alice
    c.submit_reading("conflict","a",20000,500)
    assert get(c,"conflict")["status"]=="CONFLICT"
    assert get(c,"conflict")["result"]["interval"] is None

def test_majority_excludes_outlier(direct_vm,direct_deploy,direct_alice,direct_bob,direct_charlie,monkeypatch):
    vm=direct_vm
    c,_=setup(vm,direct_deploy,direct_alice,direct_bob,direct_charlie,monkeypatch)
    c.open_round("r",'["a","b","c"]',2)
    c.submit_reading("r","a",20000,500)
    vm.sender=direct_bob
    c.submit_reading("r","b",68900,900)
    vm.sender=direct_charlie
    c.submit_reading("r","c",310000,500)
    result=get(c,"r")["result"]
    assert result["status"]=="AGREEMENT" and result["excluded"]==["c"] and result["peak_support"]==2

def test_ambiguous_disjoint_peak(direct_vm,direct_deploy,direct_alice,direct_bob,direct_charlie,monkeypatch):
    vm=direct_vm
    c,_=setup(vm,direct_deploy,direct_alice,direct_bob,direct_charlie,monkeypatch)
    c.open_round("r",'["a","b","c"]',2)
    c.submit_reading("r","a",20000,5000)
    vm.sender=direct_bob
    c.submit_reading("r","b",59000,0)
    vm.sender=direct_charlie
    c.submit_reading("r","c",298150,0)
    assert get(c,"r")["status"]=="REVIEW"

def test_context_quorum_and_owner_guards(direct_vm,direct_deploy,direct_alice,direct_bob,direct_charlie,monkeypatch):
    vm=direct_vm
    c,p=setup(vm,direct_deploy,direct_alice,direct_bob,direct_charlie,monkeypatch)
    for ids,reason in [('["a","surface"]',"Incompatible"),('["a","other"]',"Incompatible"),('["a","same"]',"Distinct"),('["a","review"]',"eligible"),('["a","a"]',"distinct")]:
        with vm.expect_revert(reason):
            c.open_round("r",ids,2)
    with vm.expect_revert("majority"):
        c.open_round("r",'["a","b"]',1)
    c.open_round("r",'["a","b"]',2)
    p["a"]["label"]="changed"
    with vm.expect_revert("profile changed"):
        c.submit_reading("r","a",20000,500)
