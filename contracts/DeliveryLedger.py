# { "Depends": "py-genlayer:kzybg95x1gn21dw72m7hyg0maaap04n4nx55j9yt6fkdqxtz6bz0" }
"""Cross-contract, two-party state machine; no caller-supplied certificate."""
import genlayer as gl
from genlayer.types import Address
from genlayer.storage import TreeMap
import hashlib
import json
import re


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()


def require_id(value):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value):
        raise gl.vm.UserError("Invalid ID")


def sender():
    return gl.message.sender_address.as_hex.lower()


def checked_address(value):
    addr = Address(value)
    if addr.as_hex.lower() == "0x" + "0" * 40:
        raise gl.vm.UserError("Zero address prohibited")
    return addr


def pair_member(rec, actor):
    return actor in (rec["owner"], rec["counterparty"])


def source_pair(anchor, protocol, case_id):
    require_id(case_id)
    view = gl.contract.get_at(anchor).view()
    if view.get_protocol_version() != protocol:
        raise gl.vm.UserError("Incompatible anchor protocol")
    raw = view.get_case(case_id)
    proof = view.get_certificate(case_id)
    if not raw or not proof:
        raise gl.vm.UserError("Missing frozen case or certificate")
    data, cert = json.loads(raw), json.loads(proof)
    actual = digest({k:v for k,v in data.items() if k != "input_sha256"})
    if data.get("case_id") != case_id or cert.get("case_id") != case_id or data.get("input_sha256") != actual or cert.get("input_sha256") != actual:
        raise gl.vm.UserError("Certificate binding mismatch")
    return data, cert

MAX_MG=10**18


class DeliveryLedger(gl.contract.Contract):
    anchor: Address
    orders: TreeMap[str,str]
    batches: TreeMap[str,str]
    used_cases: TreeMap[str,str]
    used_receipts: TreeMap[str,str]
    used_orders: TreeMap[str,str]

    def __init__(self, anchor_address: str):
        self.anchor=checked_address(anchor_address)

    @gl.public.view
    def get_anchor_address(self) -> str:
        return self.anchor.as_hex

    @gl.public.view
    def get_protocol_version(self) -> str:
        return "delivery-ledger-v2"

    def _load(self, ledger_id):
        raw=self.orders.get(ledger_id,"")
        if not raw:
            raise gl.vm.UserError("Unknown order")
        return json.loads(raw)

    def _save(self, rec):
        self.orders[rec["ledger_id"]]=json.dumps(rec,sort_keys=True)

    def _certificate(self, case_id):
        data,cert=source_pair(self.anchor,"unitbridge-v2",case_id)
        if not data.get("order_id") or not data.get("receipt_id"):
            raise gl.vm.UserError("Use freeze_delivery with bound document IDs")
        facts=cert.get("facts",{})
        target,amount=facts.get("required_mg"),facts.get("delivered_mg")
        if cert.get("sku")!=data.get("sku") or cert.get("status") not in ("MEETS_MINIMUM","SHORTFALL") or facts.get("status")!="READY" or type(target) is not int or type(amount) is not int or not 1<=target<=MAX_MG or not 1<=amount<=MAX_MG:
            raise gl.vm.UserError("Grounded quantity certificate required")
        if cert.get("delta_mg")!=amount-target or cert["status"]!=("MEETS_MINIMUM" if amount>=target else "SHORTFALL"):
            raise gl.vm.UserError("Certificate arithmetic mismatch")
        return data,cert

    @gl.public.write
    def open_order(self, ledger_id: str, first_case: str, supplier: str) -> None:
        require_id(ledger_id)
        data,cert=self._certificate(first_case)
        buyer=sender()
        other=checked_address(supplier).as_hex.lower()
        if buyer!=data["owner"] or other==buyer:
            raise gl.vm.UserError("Buyer and distinct supplier required")
        order_key=buyer+":"+data["order_id"]
        if self.orders.get(ledger_id,"") or self.used_orders.get(order_key,"") or self.used_cases.get(first_case,""):
            raise gl.vm.UserError("Duplicate order or source")
        target=cert["facts"]["required_mg"]
        rec={"ledger_id":ledger_id,"owner":buyer,"counterparty":other,"order_id":data["order_id"],"sku":data["sku"],
             "order_sha256":digest(data["order"]),"spec_sha256":digest(data["spec"]),
             "target_mg":target,"received_mg":0,"remaining_mg":target,"overage_mg":0,
             "accepted_batches":0,"batch_count":0,"pending_batch":"","initial_case":first_case,"status":"AWAITING_ACCEPTANCE"}
        self.used_orders[order_key]=ledger_id
        self._save(rec)

    @gl.public.write
    def accept_order(self, ledger_id: str) -> None:
        rec=self._load(ledger_id)
        if sender()!=rec["counterparty"] or rec["status"]!="AWAITING_ACCEPTANCE":
            raise gl.vm.UserError("Supplier must accept a new order")
        rec["status"]="OPEN"
        self._save(rec)

    @gl.public.write
    def propose_delivery(self, ledger_id: str, batch_id: str, case_id: str) -> None:
        require_id(batch_id)
        rec=self._load(ledger_id)
        if sender()!=rec["owner"] or rec["status"] not in ("OPEN","PARTIAL") or rec["pending_batch"]:
            raise gl.vm.UserError("Buyer must propose against an active order with no pending batch")
        if self.batches.get(batch_id,"") or self.used_cases.get(case_id,"") or rec["batch_count"]>=256:
            raise gl.vm.UserError("Duplicate batch or certificate, or batch cap")
        data,cert=self._certificate(case_id)
        if data["owner"]!=rec["owner"] or data["order_id"]!=rec["order_id"] or data["sku"]!=rec["sku"] or digest(data["order"])!=rec["order_sha256"] or digest(data["spec"])!=rec["spec_sha256"] or cert["facts"]["required_mg"]!=rec["target_mg"]:
            raise gl.vm.UserError("Certificate does not match frozen order")
        receipt_key=rec["owner"]+":"+data["receipt_id"]
        if self.used_receipts.get(receipt_key,""):
            raise gl.vm.UserError("Receipt ID already consumed or reserved")
        amount=cert["facts"]["delivered_mg"]
        if rec["received_mg"]+amount>MAX_MG:
            raise gl.vm.UserError("Cumulative quantity outside bounds")
        batch={"batch_id":batch_id,"ledger_id":ledger_id,"case_id":case_id,
               "receipt_id":data["receipt_id"],"input_sha256":cert["input_sha256"],
               "amount_mg":amount,"status":"PENDING","resolved_by":""}
        self.batches[batch_id]=json.dumps(batch,sort_keys=True)
        self.used_cases[case_id]=batch_id
        self.used_receipts[receipt_key]=batch_id
        rec["pending_batch"]=batch_id
        rec["batch_count"]+=1
        self._save(rec)

    @gl.public.write
    def resolve_delivery(self, ledger_id: str, batch_id: str, accept: bool) -> None:
        rec=self._load(ledger_id)
        if not pair_member(rec,sender()) or rec["pending_batch"]!=batch_id or rec["status"] not in ("OPEN","PARTIAL"):
            raise gl.vm.UserError("No matching authorized pending batch")
        if accept and sender()!=rec["counterparty"]:
            raise gl.vm.UserError("Supplier must confirm the batch")
        batch=json.loads(self.batches[batch_id])
        if batch["status"]!="PENDING":
            raise gl.vm.UserError("Batch already resolved")
        batch["status"]="ACCEPTED" if accept else "DECLINED"
        batch["resolved_by"]=sender()
        if accept:
            rec["received_mg"]+=batch["amount_mg"]
            rec["accepted_batches"]+=1
        rec["remaining_mg"]=max(0,rec["target_mg"]-rec["received_mg"])
        rec["overage_mg"]=max(0,rec["received_mg"]-rec["target_mg"])
        rec["status"]="FULFILLED" if rec["remaining_mg"]==0 else ("PARTIAL" if rec["received_mg"] else "OPEN")
        rec["pending_batch"]=""
        self.batches[batch_id]=json.dumps(batch,sort_keys=True)
        self._save(rec)

    @gl.public.view
    def get_order(self, ledger_id: str) -> str:
        return self.orders.get(ledger_id,"")

    @gl.public.view
    def get_batch(self, batch_id: str) -> str:
        return self.batches.get(batch_id,"")
