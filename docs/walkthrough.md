# UNITBRIDGE Studio walkthrough

Deploy UnitBridge.py (no args), then SensorFusion.py (anchor_address = new UnitBridge address). Use Studionet.
1. A register_source("air-c","room-1","C","Absolute temperature of room air")
2. B register_source("air-f","room-1","F","Absolute temperature of room air")
3. A open_round("agreement",'["air-c","air-f"]',2)
4. A submit_reading("agreement","air-c",20000,500)
5. B submit_reading("agreement","air-f",68900,900)
6. Read get_round("agreement"): AGREEMENT, interval [2638350,2642850] ticks (20–20.5 C).
7. A open_round("conflict",'["air-c","air-f"]',2)
8. A submit_reading("conflict","air-c",20000,500)
9. B submit_reading("conflict","air-f",90000,900)
10. Read get_round("conflict"): CONFLICT, interval null.
11. B register_source("unclear","room-1","C","Temperature change or apparent temperature")
12. Read get_source("unclear"): REVIEW. This source must be rejected from fusion.
All JSON array input is one line; no newline escapes.
