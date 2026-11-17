# PET-Aeye NPU Camera  
# ODM Development & Mass-Production Request for Quotation (RFQ)

| | |
|--|--|
| Document No. | **PAW-RFQ-CAM-2026-001** |
| Version | **v1.0** (for vendor release) |
| Language | **English (master)** · Chinese translation also available |
| Request date | ______________ |
| Quotation due | **15 business days** from request date |
| Prospective buyer | **PAWKOREA** (PET-Aeye business) |
| Currency | **USD preferred** (or KRW) · Separate VAT / duties / logistics lines |
| Confidentiality | Detailed BOM / drawings after **mutual NDA** |

> This RFQ is **not a purchase order**. State quotation validity, payment terms, MOQ, and Incoterms.  
> **Scope = NPU (+ vital) IP camera ODM only.** Do **not** quote BLE tags/gateways, site servers, or developer PCs/laptops (sourced separately).

---

## 0. Cover summary

PAWKOREA requests quotation for ODM development and mass production of an  
**NPU-embedded IP camera (primary SKU: integrated 60 GHz FMCW vital sensing)**  
for pet **hotels, resorts, and homes** on a **single shared SKU**.

| Item | Requirement |
|------|-------------|
| Product | Fixed ceiling/wall camera · **on-device NPU inference** |
| Connectivity | **Wi-Fi + Ethernet + PoE (802.3af) in one SKU** |
| SKU | **Vital SKU only** (NPU + 60 GHz FMCW) · ~**1,000 units** over Phase 1+2 |
| Firmware | Buyer AI models · **OTA mandatory** · send results/events only (not continuous raw video by default) |
| Channels | Yeongjong pet hotel · Hoengseong pet resort · home cam (same PCB) |

We are PoC’ing on MaixCAM2 / Axera **AX630C** class boards.  
**Same or equivalent-or-better SoC** proposals are welcome; if substituting, state performance, toolchain, unit cost, and country of origin.

---

## 1. Business context

| Channel | Role | Typical link |
|---------|------|----------------|
| **Yeongjong pet hotel** (~112 rooms) | Boarding room / common-area monitoring (PET-Aeye) | Mostly **Wi-Fi** + reuse power · some PoE |
| **Hoengseong pet resort** | Guest rooms / indoor commons (new build) | Mostly **PoE** |
| **Home cam** | Consumer subscription · hotel history link | **Wi-Fi + DC adapter** |

Goal: one model/firmware OTA rollout across all three channels; only event rules/alert tone differ.

**Out of ODM scope**

- VMS / GPU servers / NAS / NVR  
- BLE tags (e.g. Minew) / BLE gateways (e.g. MOKO)  
- Developer laptops / workstations  
- Full guardian app & cloud (device talks to **buyer APIs only**)

---

## 2. Volumes & phases

| Phase | Target timing | Qty | Use |
|-------|---------------|-----|-----|
| EVT / DVT samples | After contract | Vital **20–50** | FOV, night, AI, OTA, radar, API |
| **Phase-1 MP** | **2027** | **~500** all vital | Yeongjong hotel + early home |
| **Phase-2 MP** | Before Hoengseong opening (TBD) | **~500** all vital | Resort + home / spares |
| **Total** | | **~1,000** | Same SKU / same PCB |
| Later | On demand | Reorders | Same vital SKU |

**Channel guide (internal plan; adjustable at PO)**

| Channel | Approx. | Notes |
|---------|---------|-------|
| Yeongjong indoor | ~150 | Rooms/commons (outdoor commodity cams out of scope) |
| Hoengseong indoor | ~310 | Rooms/commons |
| Home / spares | Remainder to 1,000 | Split across Phase 1–2 |

Please quote unit prices at **lot 500** / **cumulative 1,000** / **3,000**.  
Confirm split delivery (~500+500) and whether cumulative discount applies.  
If MOQ &lt; 500 only, state MOQ and surcharge.  
**Non-radar “standard” unit price is optional (reference only; not obligated).**

---

## 3. Hardware requirements

Propose equal-or-better alternatives with a **delta table** vs this RFQ.

| Item | Requirement | Notes |
|------|-------------|-------|
| AI SoC | Axera **AX630C** class (≥ ~3 TOPS) · RAM **≥1 GB** | Alt chip: bench + toolchain |
| Storage | eMMC **≥32 GB** (64 GB preferred) | A/B / rollback headroom |
| Sensor | **≥4 MP** · **1/1.8"** low-light preferred · ~F1.6 | PoC: SC850SL-class |
| Lens / FOV | Indoor ceiling/upper-wall · state FOV | Confirm with samples |
| Night | **850 nm IR** + **IR-Cut** | IR in finished goods |
| Network | **Wi-Fi 6** (or Wi-Fi 5+) + Ethernet | |
| Power | **PoE 802.3af** + **DC adapter** (home) | **Both required** |
| Audio | Mic required · speaker recommended (home) | Recording default OFF |
| Privacy | **Physical lens shutter** (strongly preferred) · recording LED | Or alternative + delta cost |
| Slot | microSD | Cards may be buyer-supplied |
| Mechanics | Ceiling/wall bracket · fixed as default | PTZ optional |
| Temp | Indoor 0–40 °C or better | |
| Cert design | Korea **KC** (RF/EMC) · home IoT security readiness | Agency cost as separate line |

**Target landed unit cost (non-binding, vital SKU)**  
At lot 500 and cumulative 1,000: about **USD 85–110** landed Korea (ex-VAT).  
Explain if outside this band.

---

## 4. Firmware · AI · integration

### 4.1 Responsibilities

| Area | Buyer (PAWKOREA) | ODM |
|------|------------------|-----|
| AI models | YOLO-class · NPU `.axmodel` (or agreed format) | Runtime integration / tuning support |
| Application | Events, VMS, app, servers | Device agent/SDK · streaming · OTA |
| OTA server | **Built & operated by buyer** | **Device OTA agent** deliverable |
| Cloud | Buyer | Device only · **no mandatory ODM cloud** |

### 4.2 Must-have (P0)

| Feature | Requirement |
|---------|-------------|
| Inference | On-device NPU · detect/pose · **multi-object per frame** |
| Output | Boxes / IDs / events to **buyer API** · no always-on raw upload (configurable) |
| Video | **RTSP** (H.265 preferred) · main/sub · ONVIF is a plus |
| Smart record | High bitrate on event · low bitrate when idle |
| Buffer | microSD or eMMC offline buffer |
| Security | Per-device cert (or equiv.) · no default password · **no always-on SSH in production** |
| Provisioning | Serial/QR · Wi-Fi (home) · buyer enrollment API |

### 4.3 OTA (mandatory)

Quote **with-OTA** and **without-OTA** unit prices separately.

| Item | Requirement |
|------|-------------|
| Model OTA | Replace AI model without full OS reflash |
| Firmware OTA | OS / app / agent |
| Protocol | HTTPS · `/ota/check` · `/ota/report` (or agreed) |
| Signing | Buyer (or designated) key · **signed packages only** |
| Rollback | Auto revert on failed apply/boot |
| Report | Success/fail · version · device_id |
| Acceptance | **Canary deploy + rollback demo** at DVT before MP |

Treat PoC USB/SSH flash and **production OTA as separate milestones**.

### 4.4 Vital SKU (primary · all units) — 60 GHz FMCW

**Phase-1 500 + Phase-2 500 = 1,000 units, all vital.**  
Mechanics, PCB, firmware, KC (incl. radar band), and API below are **in scope**.

Vitals are **wellness reference values (non-medical)**. No diagnosis / disease / medical-device claims in FW or docs.

#### Hardware

| Item | Requirement |
|------|-------------|
| Sensor | **60 GHz-class FMCW mmWave** (COTS module or nominated BOM) |
| Link | **UART or SPI** to SoC · power from camera board |
| Mechanics | RF window · minimize IR/FOV interference · ceiling/upper wall |
| Functions | **Presence** · **breathing rhythm / RPM (reference)** · micro-motion · (HR optional; state limits) |
| Target | Near-range indoor · single subject first (multi-subject not mandatory) |

#### API (camera firmware is the gateway)

Apps must **not** talk to the radar chip directly. **Firmware → buyer servers only.**

- Protocols: MQTT and/or HTTPS POST  
- Payload: JSON (field names finalized at kickoff)

```json
{
  "device_id": "string",
  "ts": "ISO-8601",
  "radar": {
    "presence": true,
    "breath_rpm": 18.5,
    "breath_confidence": 0.0,
    "motion_level": 0.0,
    "heart_bpm": null
  },
  "vision": {
    "pets": 0,
    "persons": 0
  }
}
```

| Requirement | Detail |
|-------------|--------|
| Periodic | Configurable (e.g. 1–5 s) · backoff when idle |
| Events | Presence change · breathing anomaly trend · prolonged no-motion |
| Raw data | **No** always-on radar ADC bulk upload |
| Docs | UART map · JSON schema · error codes · sample logs before DVT |

#### Privacy (recommended · P1 / plus)

- Real-time **person ROI blur** on stream/record  
- No store/transmit of pre-blur frames (configurable)  
- State whether radar can run with physical shutter closed  

---

## 5. Certification · quality · deliverables

| Item | Request |
|------|---------|
| KC | RF/EMC · **vital includes radar band** — cost/schedule as separate lines |
| IoT security cert | Feasibility / cost / schedule for home channel |
| Reliability | Temp/humidity · power · long soak plan |
| Warranty | AQL · **12–24 months** · RMA |
| Docs | Agreed schematics/mechanics · BOM · build/sign · OTA API · radar UART/JSON · install guide |
| Source | OTA agent / BSP: **source delivery** or **escrow / modification rights** |

---

## 6. Quotation structure (mandatory split)

### 6.1 NRE (one-time)

| # | Item | Amount | Lead time | Notes |
|---|------|--------|-----------|-------|
| 1 | Tooling / mold | | | State if reuse existing mold |
| 2 | PCB (Wi-Fi+PoE integrated) | | | |
| 3 | Base firmware (RTSP, security, provisioning) | | | |
| 4 | **OTA agent** | | | Separate if not included |
| 5 | NPU runtime · model integration support | | | |
| 6 | **Vital** (FMCW · §4.4 API) | | | **Required** |
| 7 | Person ROI blur (P1) | | | Optional line |
| 8 | EVT/DVT samples (vital 20–50) | | | |
| 9 | KC etc. (**incl. radar**) | | | Before Phase-1 MP |
| 10 | Other | | | |

### 6.2 Unit price (mass production)

State Incoterms (EXW/FOB/CIF/DDP), currency, validity.

| Qty | Vital (OTA incl.) | Vital (OTA excl., ref.) | (Ref.) non-radar delta | Lead time |
|-----|-------------------|-------------------------|------------------------|-----------|
| 500 | | | | |
| **1,000** | | | | |
| 3,000 | | | | |
| Your MOQ (___ pcs) | | | | |

Options as separate lines: shutter · blur · speaker · PTZ · adapter · bracket · microSD in/out.

### 6.3 Maintenance

| Item | Terms |
|------|-------|
| Bugfix via OTA | During warranty |
| OTA protocol changes | N times/year or T&M |
| EOL / alternate parts | Advance notice (prefer 12 months) |

---

## 7. Schedule (please propose)

| Milestone | Target (negotiable) | Deliverable |
|-----------|---------------------|-------------|
| Kickoff · spec freeze | +2 weeks after contract | Signed spec |
| EVT | +8–12 weeks | Vital samples · video/inference · radar UART |
| DVT + OTA/API demo | +4–8 weeks | OTA rollback · JSON presence/breathing |
| PVT · certification | TBD | KC (incl. radar) |
| Phase-1 MP inbound | Align to **2027** | ~**500** vital |
| Phase-2 MP | TBD | ~**500** vital |

Your standard timeline is welcome.

---

## 8. Response package checklist

Please reply as **one PDF or Excel+PDF**:

1. Company intro · IP cam / NPU / PoE MP track record  
2. Proposed spec vs this RFQ **compliance matrix**  
3. §6 quotation (currency · Incoterms · validity)  
4. MOQ · payment (deposit / progress / balance)  
5. Schedule  
6. OTA include/exclude delta · 1–2 page technical brief  
7. **Vital 1,000 pcs:** module P/N · prices · NRE · cert · §4.4 API (1–2 pp)  
8. Chip origin · export control · longevity  
9. After NDA: block diagram · mechanical renders  

Alternative proposals (PoE+Wi-Fi integration, shutter, OTA design) are **welcome**.

---

## 9. Contacts · NDA

| Item | Detail |
|------|--------|
| Commercial | (name · email · phone) |
| Technical | (name · email) |
| Sample ship-to | (address · who pays duties) |
| NDA | Mutual NDA before detailed sharing |

---

## Appendix A — Buyer BOM boundary (do not quote)

| Item | Sourcing | In this RFQ? |
|------|----------|--------------|
| NPU (+vital) camera | **This RFQ** | Yes |
| Outdoor commodity CCTV / edge box | Market / installer | No |
| BLE tags / GW / cases | Minew / MOKO etc. | No |
| Site network / servers / UPS | Installer | No |
| Dev RTX 5090 laptop | IT purchase | No |

---

## Appendix B — Minimum DVT acceptance

- [ ] Multi-object detect/pose · dual RTSP streams  
- [ ] Wi-Fi and PoE 24 h soak each  
- [ ] Smart record · microSD buffer · catch-up upload  
- [ ] Model + firmware OTA · failure rollback  
- [ ] Radar: presence + breathing reference via JSON  
- [ ] Security: no default password · signed packages only  
- [ ] (Optional) person blur · physical shutter  

---

*PAW-RFQ-CAM-2026-001 · v1.0 EN · PAWKOREA PET-Aeye · Send after legal/procurement review*  
*Master language for contract discussions: English. Chinese translation: `PET-Aeye_NPU相机_ODM询价书_v1.0_ZH.md`*
