# { "Depends": "py-genlayer:kzybg95x1gn21dw72m7hyg0maaap04n4nx55j9yt6fkdqxtz6bz0" }
import genlayer as gl
from genlayer.storage import TreeMap
from genlayer.types import Address
import json
import re

def valid_id(value):
    return isinstance(value,str) and bool(re.fullmatch(r"[A-Za-z0-9_-]{1,64}",value))

def aggregate(reports, quorum):
    # Closed integer intervals. Sweep changes at lower and upper+1.
    events={}
    for r in reports:
        lo,hi=r["lower_ticks"],r["upper_ticks"]
        events[lo]=events.get(lo,0)+1
        events[hi+1]=events.get(hi+1,0)-1
    keys=sorted(events)
    support=0
    peak=0
    segments=[]
    for i in range(len(keys)-1):
        x=keys[i]
        support+=events[x]
        end=keys[i+1]-1
        if support>peak:
            peak=support
            segments=[[x,end]]
        elif support==peak and support>0:
            if segments and segments[-1][1]+1==x:
                segments[-1][1]=end
            else:
                segments.append([x,end])
    out={"peak_support":peak,"quorum":quorum,"ticks_per_kelvin":9000}
    if peak<quorum:
        return dict(out,status="CONFLICT",interval=None)
    if len(segments)!=1:
        return dict(out,status="REVIEW",interval=None)
    lo,hi=segments[0]
    # Only readings containing the entire reported interval are supporters.
    supporters=[r["source_id"] for r in reports if r["lower_ticks"]<=lo and r["upper_ticks"]>=hi]
    if len(supporters)<quorum:
        return dict(out,status="REVIEW",interval=None)
    return dict(out,status="AGREEMENT",interval=[lo,hi],supporters=sorted(supporters),
                excluded=sorted(r["source_id"] for r in reports if r["source_id"] not in supporters))

class SensorFusion(gl.contract.Contract):
    anchor: Address
    rounds: TreeMap[str,str]

    def __init__(self, anchor_address: str):
        self.anchor=Address(anchor_address)
        if self.anchor.as_hex.lower()=="0x"+"0"*40:
            raise gl.vm.UserError("Zero anchor")

    def _view(self):
        view=gl.contract.get_at(self.anchor).view()
        if view.get_protocol_version()!="sensor-interop-1":
            raise gl.vm.UserError("Incompatible registry")
        return view

    @gl.public.write
    def open_round(self, round_id: str, source_ids_json: str, quorum: int) -> None:
        if not valid_id(round_id) or self.rounds.get(round_id,"") or len(source_ids_json)>400:
            raise gl.vm.UserError("Invalid or duplicate round")
        try:
            ids=json.loads(source_ids_json)
        except (ValueError,TypeError):
            raise gl.vm.UserError("Use JSON source array")
        if not isinstance(ids,list) or not 2<=len(ids)<=5 or not all(valid_id(x) for x in ids) or len(set(ids))!=len(ids):
            raise gl.vm.UserError("Use 2 to 5 distinct sources")
        if type(quorum) is not int or not len(ids)//2<quorum<=len(ids):
            raise gl.vm.UserError("Strict majority quorum required")
        view=self._view()
        profiles={}
        owners=set()
        kind=""
        site=""
        for sid in sorted(ids):
            raw=view.get_source(sid)
            if not raw:
                raise gl.vm.UserError("Unknown source")
            src=json.loads(raw)
            if src["source_id"]!=sid or src["status"]!="ACTIVE" or src["kind"] not in ("AIR","SURFACE","LIQUID") or src["unit"] not in ("C","F","K"):
                raise gl.vm.UserError("Source not eligible")
            if src["owner"] in owners:
                raise gl.vm.UserError("Distinct source owners required")
            if kind and (src["kind"]!=kind or src["site"]!=site):
                raise gl.vm.UserError("Incompatible measurement context")
            kind,site=src["kind"],src["site"]
            owners.add(src["owner"])
            profiles[sid]=src
        rec={"round_id":round_id,"site":site,"kind":kind,"quorum":quorum,"profiles":profiles,
             "reports":{},"status":"OPEN","result":None}
        self.rounds[round_id]=json.dumps(rec,sort_keys=True)

    @gl.public.write
    def submit_reading(self, round_id: str, source_id: str, value_milli: int, uncertainty_milli: int) -> None:
        raw=self.rounds.get(round_id,"")
        if not raw:
            raise gl.vm.UserError("Unknown round")
        rec=json.loads(raw)
        src=rec["profiles"].get(source_id)
        if rec["status"]!="OPEN" or not src or source_id in rec["reports"] or src["owner"]!=gl.message.sender_address.as_hex.lower():
            raise gl.vm.UserError("Unauthorized or duplicate reading")
        view=self._view()
        if json.loads(view.get_source(source_id))!=src:
            raise gl.vm.UserError("Registry profile changed")
        normalized=json.loads(view.normalize(source_id,value_milli,uncertainty_milli))
        lo,hi,center=normalized["lower_ticks"],normalized["upper_ticks"],normalized["center_ticks"]
        if normalized["ticks_per_kelvin"]!=9000 or any(type(x) is not int for x in (lo,hi,center)) or not 0<=lo<=center<=hi<=4500000 or center-lo!=hi-center or hi-center>90000:
            raise gl.vm.UserError("Invalid normalized reading")
        rec["reports"][source_id]=dict(normalized,source_id=source_id,value_milli=value_milli,uncertainty_milli=uncertainty_milli)
        if len(rec["reports"])==len(rec["profiles"]):
            rec["result"]=aggregate(list(rec["reports"].values()),rec["quorum"])
            rec["status"]=rec["result"]["status"]
        self.rounds[round_id]=json.dumps(rec,sort_keys=True)

    @gl.public.view
    def get_round(self, round_id: str) -> str:
        return self.rounds.get(round_id,"")

    @gl.public.view
    def get_anchor_address(self) -> str:
        return self.anchor.as_hex
