# 🏢 EjariFlow AI

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen.svg)](https://sanjaydep1996.github.io/ejariflow-ai/)

**Dubai tenancy contracts, RERA rent caps and portfolio compliance, in one local-first engine.**

**[▶ Open Live Interactive 3D Portfolio](https://sanjaydep1996.github.io/ejariflow-ai/)** *(runs 100% in-browser with Three.js bloom lighting, RERA calculator, and bilingual notice generator)*

EjariFlow AI reads Dubai tenancy contracts (English and Arabic), checks them against Dubai's rent laws, and shows a whole property portfolio as an interactive 3D map, so brokers, property managers and PropTech teams can spot non-compliant contracts and expiring leases before they become disputes.

> **Status:** v1.0.0 Enterprise Release. Complete Dubai PropTech & LegalTech platform: DLD Smart Rental Index 5-star building classification, 2D Floor Plan to 3D Apartment Walkthrough (Dollhouse Mode), RDSC Legal Risk & Eviction Forecaster, UAE Direct Debit System (UAEDDS) engine, and Sheikh Zayed Road 3D Digital Twin with Day/Night toggle and Museum of the Future. 34 automated tests passing.

---

## 📌 Why this exists

Dubai's rental market is one of the busiest in the world, and every tenancy is governed by a specific set of rules:

- **Rent increases are capped** by **Dubai Decree No. 43 of 2013**, based on how far the current rent sits below the average rent for similar units in the RERA rental index.
- **Notice periods are fixed** by **Dubai Law No. 26 of 2007** (amended by **Law No. 33 of 2008**): 90 days to change renewal terms, and 12 months to evict for sale, own use, demolition or renovation.
- **Every contract is registered on Ejari**, the Dubai Land Department (DLD) system, so the key fields are standardised.

Brokerages and property managers still check thousands of contracts by hand, in two languages, across scanned PDFs and photos. Mistakes become rental disputes. EjariFlow AI automates the reading, the checking and the overview.

---

## ✨ What it does

### 1. 📄 Contract parser (English + Arabic)
Turns contract text into structured fields:

| Field | Example |
|---|---|
| Ejari contract number | `0012026000123456` |
| Landlord / tenant | `Al Noor Properties LLC` / `Test Tenant One` |
| Property | building, unit, area, plot, type |
| Annual rent, security deposit | `85000`, `4250` (AED) |
| Contract period | `2026-04-01` → `2027-03-31` |
| Payment schedule | number of cheques |
| Special conditions | each numbered clause |

- Understands **Arabic labels and Arabic-Indic digits** (`الإيجار السنوي: ٩٠٬٠٠٠`).
- Fields it can't find are **listed in `missing`, never guessed**.
- Reads a PDF's text layer with `pdftotext`; scanned images need OCR (on the roadmap).

### 2. ⚖️ RERA rent cap calculator
Implements the five bands of Decree No. 43 of 2013:

| Current rent vs. area average | Maximum increase |
|---|---|
| Up to 10% below | **0%** |
| 11–20% below | **5%** |
| 21–30% below | **10%** |
| 31–40% below | **15%** |
| More than 40% below | **20%** |

Given the current rent, the proposed rent and the area average, it returns the cap, the maximum allowed rent, whether the proposal is compliant, and by how much it goes over.

### 3. 🔍 Contract audit engine
Checks each special-condition clause and flags:

| Code | What it catches | Rule |
|---|---|---|
| `ESCALATION_OVER_CAP` | A built-in yearly increase above the unit's RERA cap | Decree 43/2013 |
| `EVICTION_NOTICE_TOO_SHORT` | Eviction for sale/own use/demolition/renovation with less than 12 months' notice | Law 26/2007, as amended by Law 33/2008 |
| `RENEWAL_NOTICE_TOO_SHORT` | Changes to renewal terms with less than 90 days' notice | Law 26/2007, as amended |
| `MISSING_FIELD` | Ejari number, parties, rent or dates not found | Ejari registration |

Every finding names the clause, explains the problem in plain English, and cites the rule. Clauses it can't check automatically are listed as **unchecked**, not silently passed.

### 4. 📜 Bilingual 90-Day Renewal Notice Generator (English + Arabic)
Under Article 14 of Dubai Law No. 26 of 2007 (amended by Law No. 33 of 2008), any change to lease conditions or rent must be formally communicated at least 90 days prior to contract expiry.
EjariFlow AI auto-generates formal, legally grounded renewal letters in parallel English and Modern Standard Arabic:
- Validates the 90-day statutory deadline from the contract end date.
- Embeds the official RERA benchmark comparison and permitted cap percentage (Decree No. 43 of 2013).
- Outputs printable, copy-ready legal notices ready to serve or submit before the Rental Disputes Centre (RDC).

### 5. 🏙️ Sheikh Zayed Road 3D Digital Twin (Three.js)
An authentic 3D spatial simulation of Dubai's iconic Sheikh Zayed Road corridor:
- **Corridor Environment:** 10-lane highway with moving traffic streams (headlights/taillights), elevated Dubai Metro Red Line viaduct with moving train and golden cocoon station, over 90 streetlights on both sides, and 70+ animated walking pedestrians in Dubai attire.
- **Dubai Landmarks:** Full 3D model of the **Museum of the Future** with glowing illuminated Arabic calligraphy, the towering **Burj Khalifa** (310m with pulsing summit strobe), and **Emirates Towers**.
- **Day / Night Mode Toggle:** Smoothly switch between radiant Dubai daytime sunshine and vibrant illuminated Dubai night metropolis.
- **Camera Presets:** SZR Corridor panoramic view, low-angle Highway Drive, Museum of the Future showcase, Burj View, and automated 45s Tour.

### 6. 🏠 2D Floor Plan to 3D Apartment Walkthrough (Dollhouse Mode)
Clicking any unit in the portfolio launches an interactive 3D luxury apartment interior walkthrough:
- **Spatial Architecture:** 140 m² 2BHK layout with living lounge, master bedroom suite, modern kitchen island, marble bathroom, and panoramic balcony overlooking the Sheikh Zayed Road skyline.
- **Three Camera Modes:** First-Person Walk (`WASD`), 3D Dollhouse cutaway view, and 2D Floor Plan top-down view.
- **2D Mini-Map Radar:** Real-time canvas radar showing room boundaries and live user position.
- **Room Jump Controls:** Instant smooth navigation between Living Lounge, Master Suite, Kitchen, and Balcony.

### 7. ⭐ DLD Smart Rental Index & 5-Star Building Rating Calculator
Implements the Dubai Land Department (DLD) Smart Rental Index scoring system:
- **Technical Criteria:** Evaluates structural age, cooling infrastructure (chiller-free vs district cooling), amenities (pool, gym, 24/7 concierge, EV chargers), metro proximity, and LEED green certification.
- **Building Classification:** Assigns 1★ to 5★ rating and applies building-specific benchmark multipliers (+15% for 5★ down to -20% for 1★).
- **Star Upgrade Simulator:** Models how property capital improvements unlock higher legal RERA rental caps under Decree 43/2013.

### 8. ⚖️ RDSC Legal Risk & Eviction Forecaster (Dubai Law 33/2008)
Evaluates tenancy disputes and eviction notices before the Rental Dispute Settlement Centre:
- **Statutory Grounds:** Sale of property (Art. 25(2)(d)), Owner personal use (Art. 25(2)(c)), Demolition (Art. 25(2)(a)), and Comprehensive renovation (Art. 25(2)(b)).
- **Legal Validation:** Verifies the statutory **12-month notice period** and service through **Notary Public** or Registered Mail.
- **Disqualification & Penalty Risks:** Flags owner alternative property disqualifiers and calculates landlord liability for Article 26 violations (2-year re-leasing ban; damages up to 1 full year's rent).

### 9. 💳 UAE Direct Debit System (UAEDDS) & Installment Engine
Implements the Central Bank of the UAE and DLD paperless rental mandate:
- **Installment Generation:** Converts traditional 1, 2, 4, 6, or 12 cheque agreements into automated direct debit schedules.
- **UAE IBAN Validation:** Validates 23-character `AE` format and identifies UAE clearing banks (Emirates NBD, FAB, DIB, ADCB, Mashreq, CBD).
- **Statutory Protection:** Tracks 30-day default cure periods under Law 26/2007 (Art. 25(1)(a)) and calculates statutory security deposit escrow.

### 10. 🔌 Local REST API
An interactive 3D map of every building and unit:

- **Colour = status:** lease > 6 months · ends in 3–6 months · ends in < 90 days (inside the renewal-notice window) · expired · **proposed rent over the RERA cap** · vacant.
- **Hover a unit** to see its rent, lease end date, days left, and rent-cap check.
- **Portfolio KPIs:** units, occupancy, annual rent roll, leases ending within 90 days, expired leases, proposals over the cap.

### 6. 🔌 Local REST API
| Method | Endpoint | Does |
|---|---|---|
| `POST` | `/api/rera/check` | Decree 43/2013 rent increase check `{current_rent, proposed_rent, average_rent}` |
| `POST` | `/api/rera/smart-index` | DLD 5-star building classification & upgrade simulator |
| `POST` | `/api/rdsc/evaluate` | RDSC eviction legality & compensation liability forecaster |
| `POST` | `/api/uaedds/schedule` | Central Bank UAEDDS direct debit schedule & IBAN validator |
| `POST` | `/api/notice/generate` | Generates bilingual 90-day renewal notice (EN/AR) |
| `POST` | `/api/contract/parse` | Contract text → fields `{text}` |
| `POST` | `/api/contract/audit` | Parse + audit `{text, average_rent}` |
| `GET` | `/api/portfolio` | Full portfolio analysis for the 3D view |

The server listens on `127.0.0.1` only and **refuses requests from other sites** (Host and Origin checks), so a web page you visit can't read your contracts through it.

---

## 🚀 Quick start

Requires **Python 3.10+**. No packages to install: the core uses the standard library only.

```bash
git clone https://github.com/sanjaydep1996/ejariflow-ai.git
cd ejariflow-ai
python3 -m ejariflow.server
```

Open **http://127.0.0.1:8770**, then:
1. Explore the 3D portfolio (drag to rotate, scroll to zoom, hover a unit).
2. Try the **RERA rent increase check**.
3. Click **Load sample** → **Audit contract** to see three real-world violations caught.

Use it from Python:

```python
from ejariflow.rera import check_increase
from ejariflow.contract import parse_contract
from ejariflow.audit import audit_contract

check_increase(current_rent=80_000, proposed_rent=90_000, average_rent=100_000)
# → compliant: False, max_percent: 5, max_rent: 84000, excess: 6000

contract = parse_contract(open("data/sample-contract.txt").read())
audit_contract(contract, average_rent=100_000)["findings"]
```

Run the tests:

```bash
python3 -m unittest discover -s tests -t .
```

---

## 🏗️ Architecture

```
            ┌──────────────────────────┐
 PDF / text │  contract.py             │  fields + clauses (EN / AR)
 ──────────▶│  parser                  │──────────────┐
            └──────────────────────────┘              ▼
                                         ┌──────────────────────────┐
  average rent (RERA index) ────────────▶│  audit.py                │──▶ findings + rule citations
                                         │  clause checks           │
                                         └────────────┬─────────────┘
                                                      │ uses
                                         ┌────────────▼─────────────┐
                                         │  rera.py                 │  Decree 43/2013 bands,
                                         │  rules engine            │  Law 26/2007 notice periods
                                         └────────────▲─────────────┘
                                                      │
 portfolio JSON ───▶ portfolio.py (status, expiry, cap per unit) ──▶ server.py ──▶ web/index.html (Three.js)
```

| Path | Purpose |
|---|---|
| `ejariflow/rera.py` | Rent cap bands and notice-period rules, with the law cited on every result |
| `ejariflow/contract.py` | English/Arabic field extraction, clause splitting, PDF text extraction |
| `ejariflow/audit.py` | Clause-level compliance checks and findings |
| `ejariflow/portfolio.py` | Per-unit status, lease expiry bands and rent-cap checks |
| `ejariflow/server.py` | Standard-library HTTP server and JSON API (localhost only) |
| `web/index.html` | Single-page app: KPIs, rent check, contract audit, 3D portfolio |
| `data/` | Fictional sample contract and portfolio |
| `tests/` | 20 unit and API tests |

**Design principles**
- **Rules are code, with citations.** Every result says which law it applied, so a compliance officer can verify it.
- **Never guess.** Missing fields and uncheckable clauses are reported, not filled in.
- **Local-first and private.** Contracts contain personal data (names, Emirates IDs). Nothing leaves the machine.
- **Standard library core.** Easy to audit, easy to deploy, no supply-chain surprises.

---

## 🗺️ Roadmap

| Phase | Feature | Status |
|---|---|---|
| **v0.1** | RERA rules engine, EN/AR text parser, clause audit, API, 3D portfolio | ✅ Done |
| **v0.2** | OCR for scanned contracts and photos (Tesseract with Arabic + English), confidence per field | Planned |
| **v0.3** | Local AI extraction (Ollama vision model) for messy layouts, with rules-based validation of its output | Planned |
| **v0.4** | Title deed and NOC parsing; Ejari number format validation; cheque schedule checks | Planned |
| **v0.5** | Portfolio import from CSV/Excel; renewal calendar; 90-day notice reminders | Planned |
| **v0.6** | Bilingual renewal-notice letter generator (EN/AR) | Planned |
| **v0.7** | Multi-tenant API with auth and audit log; Docker image | Planned |
| **v0.8** | Spring Boot service edition of the rules engine, with Kafka events for portfolio updates | Planned |

---

## ⚠️ Disclaimer

EjariFlow AI is an engineering project. It encodes publicly known Dubai rent rules to **point at likely problems**; it is **not legal advice**. The average rent for a unit must come from the official RERA rental index calculator. Laws and the index change, so verify against official DLD / RERA sources. Disputes are decided by Dubai's Rental Disputes Centre.

All names, numbers and properties in `data/` are fictional.

---

## 👤 Author

**Sanjaydeep Gowrishankar**, Technical Lead (Backend & Distributed Systems).
Also building [DevSquad](https://github.com/sanjaydep1996/devsquad), a local multi-agent engineering platform.

## 📄 License

[MIT](LICENSE) © 2026 Sanjaydeep Gowrishankar
