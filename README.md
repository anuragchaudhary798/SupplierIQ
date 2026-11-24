# SupplierIQ Version 3 — Procurement Decision Lab

A small, local interactive Streamlit application for a KLU programming final project. It uses 12 **fictional** suppliers, five SKUs and 35 supplier offers. It is a transparent rule-based scoring tool, **not machine learning**.

## How to run on a Mac with VS Code and uv

1. Extract `SupplierIQ_V3.zip`.
2. Open **VS Code → File → Open Folder… → SupplierIQ_V3**.
3. Open **Terminal → New Terminal** and run:

   ```bash
   uv sync
   uv run streamlit run app.py
   ```

4. Open the local URL shown (usually `http://localhost:8501`).
5. To stop, return to the terminal and press **Control + C**.

This project requires Python 3.13, uv and internet for the initial package installation. Do not upload `.venv` to a shared repository.

## What changed from V2

- Preset business situations: Balanced, Cost reduction, Urgent delivery and Supplier disruption.
- A hypothetical supplier disruption temporarily removes the top **balanced** supplier for the selected SKU and recalculates the eligible ranking.
- Two-supplier comparison of raw KPIs and weighted scores.
- Order quantity input with purchasing cost comparison versus the lowest-price eligible supplier.
- Retains the V2 scoring algorithm, supplier CSV, SKU eligibility filtering, KPI sliders, sorted chart, ranking table and recommendation explanation.
- Replaces the deprecated `use_container_width=True` argument with `width='stretch'`.

## Scoring methodology

For a chosen SKU and scenario, compare only eligible suppliers:

- Price score = 100 × lowest eligible price / supplier price
- Delivery score = on-time delivery percentage
- Quality score = accepted-unit percentage
- Lead-time score = 100 × shortest eligible lead time / supplier lead time
- Weighted score = sum(weight × KPI score) / sum(weights)

At least one weight must be positive. All other raw KPI values are unchanged in the sample data. The disruption case makes a hypothetical supplier unavailable; it does **not** claim the supplier is actually disrupted. Cost impact = quantity × unit price; freight, taxes, discounts and capacity are out of scope.

## Two-minute demo path

1. Choose `PKG-001`. Start at **Balanced operations**.
2. Switch to **Cost reduction**: review why rankings change.
3. Switch to **Urgent delivery**: review supplier reliability/speed priorities.
4. Switch to **Supplier disruption**: see the temporarily unavailable supplier and replacement recommendation.
5. Compare the top two suppliers head to head.
6. Increase quantity from 5,000 to 10,000 units: see cost difference change.

## Code files

- `app.py`: Streamlit interface and the three new features.
- `scoring.py`: original V2 ranking and KPI calculation function, unchanged.
- `supplier_offers.csv`: same V2 sample supplier data, unchanged.
- `test_supplieriq.py`: automated model/data/scenario checks.
- `pyproject.toml`: dependency setup.

## Testing

Run from the project folder:

```bash
uv run python test_supplieriq.py
```

Keep this ZIP as a new version. Do not overwrite your working V2 project until V3 launches successfully on your Mac.
