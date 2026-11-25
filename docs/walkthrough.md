# UNITBRIDGE — Studionet walkthrough

Deploy UnitBridge.py (no args) and SensorFusion.py (anchor_address = UnitBridge address). [Live evidence](evidence.md).
All JSON array arguments are single-line strings. Execution Normal, testnet only.

| TX | Wallet | Method | Positional arguments |
|---|---|---|---|
| 01 | A | register_source | `"air-c","room-1","C","Absolute temperature of room air"` |
| 02 | B | register_source | `"air-f","room-1","F","Absolute temperature of room air"` |
| 03 | A | open_round | `"agreement",'["air-c","air-f"]',2` |
| 04 | A | submit_reading | `"agreement","air-c",20000,500` |
| 05 | B | submit_reading | `"agreement","air-f",68900,900` |
| 06 | A | open_round | `"conflict",'["air-c","air-f"]',2` |
| 07 | A | submit_reading | `"conflict","air-c",20000,500` |
| 08 | B | submit_reading | `"conflict","air-f",90000,900` |
| 09 | C | register_source | `"air-k","room-1","K","Absolute temperature of room air"` |
| 10 | A | open_round | `"majority",'["air-c","air-f","air-k"]',2` |
| 11 | A | submit_reading | `"majority","air-c",20000,500` |
| 12 | B | submit_reading | `"majority","air-f",68900,900` |
| 13 | C | submit_reading | `"majority","air-k",310000,500` |
| 14 | C | register_source | `"unclear","room-1","C","Temperature change or apparent temperature"` |
| 15 | C | submit_reading | `"majority","air-k",310000,500` (expected rollback) |

Read get_round("agreement") after TX05, get_round("conflict") after TX08, get_round("majority") after TX13 and TX15, get_source("unclear") after TX14. No signatures for reads. Compare with [captured readbacks](readbacks-2026-11-25.json).
