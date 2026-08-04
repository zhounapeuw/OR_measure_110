# Drug-class crosswalk (SDUD product names → analysis buckets)

How raw Medicaid prescription product names (`sdud_or.product_name`) are mapped to
the addiction-treatment / harm-reduction classes used in `sql/20_rx_by_class.sql`
(table `mart_rx_by_class`).

## Why a crosswalk is needed

- SDUD `product_name` is **truncated to ~10 characters** and **inconsistently cased**
  (e.g. both `BUPRENORPH` and `Buprenorph` appear) → we match with **`ILIKE`**
  (case-insensitive) on name prefixes.
- The same drug is recorded under both its **generic name and brand names**, as
  separate products → each class must union several name patterns to avoid undercounting.

## The classes

All four act on the brain's **µ-opioid receptor**. *Agonist* = activates it;
*antagonist* = blocks it.

| Class (`drug_class`) | `ILIKE` patterns | Names captured (generic / brand) | Pharmacology | Clinical role |
|---|---|---|---|---|
| `buprenorphine_moud` | `BUPRENOR%`, `BUPREN&%`, `BUP/NAL%`, `SUBOX%`, `ZUBSOLV%`, `SUBLOCAD%`, `BRIXADI%` | buprenorphine and buprenorphine/naloxone (generic, incl. the later `BUPREN&NAL` / `BUP/NAL` spellings); Suboxone, Zubsolv, Sublocade, Brixadi (brands) | **partial** agonist (activates partway, has a ceiling, blocks other opioids) | first-line **medication for opioid use disorder (MOUD)** — treatment |
| `naltrexone_moud` | `NALTREX%`, `VIVITROL%` | naltrexone (generic); Vivitrol (brand, monthly injection) | full **antagonist** (blocks the receptor) | MOUD; requires prior detox. Also used for alcohol use disorder |
| `naloxone` | `NALOX%`, `NARCAN%`, `KLOXXADO%` | naloxone (generic); Narcan, Kloxxado (brands, nasal spray) | full **antagonist**, fast-acting | **emergency overdose reversal** — harm reduction, *not* a treatment |
| `methadone` | `METHADON%` | methadone (generic) | **full** agonist (long-acting, oral) | see caveat — pharmacy methadone is mostly for pain |

## ⚠️ Two traps found the hard way (2026-07-13)

**1. Product names changed over time — the crosswalk must catch the new spellings.**
Generic buprenorphine/naloxone was recorded as `Buprenorph`/`BUPRENORPH` in early years, but by
2024 much of the volume had moved to **`BUPREN&NAL`** and **`BUP/NAL 2M`/`BUP/NAL 8M`**, plus the
newer **`BRIXADI`** injectable. The original patterns missed all of these, undercounting recent
years by ~18k prescriptions in 2024 alone. **Always re-check distinct product names in the latest
year before trusting a trend.**

Correctly *excluded* (they contain "BUP" but are unrelated): **BUPROPION** (an antidepressant),
**IBUPROFEN**, **BUPIVACAINE** (an anesthetic), **NALBUPHINE**. This is why we match on name
prefixes, not a naive `%BUP%`.

**2. Use `units_reimbursed`, NOT `number_of_prescriptions`, for trends.**
`number_of_prescriptions` counts **fills**. Buprenorphine dispensing shifted from weekly to
monthly fills — units per prescription rose from **9.3 (2018) to 47.7 (2025)** — so prescription
counts fell ~5x while the **quantity actually dispensed stayed flat**. Counting fills would have
shown treatment "collapsing 6x" when it did no such thing (SAMHSA client counts confirm it was
flat). `units_reimbursed` is immune to fill-frequency changes and is the analysis metric.

Generic vs brand matters: matching only `BUPRENOR%` would miss every prescription
recorded as "Suboxone"/"Sublocade", undercounting treatment. The crosswalk reunites
all spellings of the same therapy.

## Caveats / limitations

- **Methadone**: methadone *for opioid use disorder* is dispensed at specialized clinics
  (Opioid Treatment Programs), **not** retail pharmacies, so it does not appear in SDUD
  pharmacy claims. Methadone here is therefore **mostly for pain**, not OUD — interpret
  with care.
- **Suboxone / Zubsolv contain naloxone** but are classified as `buprenorphine_moud`,
  not `naloxone`. The naloxone in these combos is an inactive abuse-deterrent when taken
  as directed; the therapeutic agent is buprenorphine and the product is a **treatment**,
  not a rescue kit. Classification follows clinical purpose.
- **Name-based classification can't perfectly separate indication/formulation.** Low-dose
  buprenorphine *pain* products (e.g. Butrans, Belbuca) use different brand names and are
  not captured by `BUPRENOR%`, so this bucket is predominantly OUD sublingual generics
  plus combo brands — reasonable, but not a clinical adjudication.
- Truncated names mean a pattern could in principle catch an unintended product; the
  patterns above were checked against the actual distinct names present in `sdud_or`.

## Source

- Mapping implemented in [`sql/20_rx_by_class.sql`](../sql/20_rx_by_class.sql).
- Verify the names present: `SELECT DISTINCT product_name FROM sdud_or WHERE product_name ILIKE 'BUPRENOR%' ...`
