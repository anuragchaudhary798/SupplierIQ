"""SupplierIQ V3 — transparent procurement decision laboratory."""
from pathlib import Path
import altair as alt
import pandas as pd
import streamlit as st
from scoring import rank_suppliers

st.set_page_config(page_title="SupplierIQ — Decision Lab", page_icon="📦", layout="wide")
DATA_FILE = Path(__file__).with_name("supplier_offers.csv")

@st.cache_data
def load_data():
    return pd.read_csv(DATA_FILE)

data = load_data()

# Presets describe procurement priorities, not probabilities or forecasts.
SCENARIOS = {
    "Balanced operations": {"price": 35, "delivery": 30, "quality": 25, "lead": 10},
    "Cost reduction": {"price": 85, "delivery": 5, "quality": 5, "lead": 5},
    "Urgent delivery": {"price": 10, "delivery": 50, "quality": 10, "lead": 30},
    "Supplier disruption": {"price": 15, "delivery": 45, "quality": 25, "lead": 15},
}

st.title("📦 SupplierIQ | Procurement Decision Lab")
st.caption("Interactive SKU-based supplier selection · Fictional demonstration data · Version 3")
st.write("Choose a material, simulate business conditions, and compare supplier trade-offs.")

sku_names = dict(zip(data["sku"], data["sku_name"]))
selected_sku = st.selectbox("Choose the material (SKU)", list(sku_names),
                            format_func=lambda sku: f"{sku} — {sku_names[sku]}")

st.subheader("1. What-if procurement scenario")
scenario = st.selectbox("Business situation", list(SCENARIOS),
                        help="Each scenario starts with an editable KPI weight preset.")
if scenario == "Supplier disruption":
    st.warning("Supply disruption: the top supplier under normal balanced priorities is temporarily unavailable for this SKU. This is a hypothetical scenario, not real supplier news.")
else:
    st.caption("Change the scenario to load suggested weights. You can still adjust every slider manually.")

preset = SCENARIOS[scenario]
col1, col2, col3, col4 = st.columns(4)
with col1:
    price = st.slider("Price", 0, 100, preset["price"], 5, key=f"{scenario}_price")
with col2:
    delivery = st.slider("On-time delivery", 0, 100, preset["delivery"], 5, key=f"{scenario}_delivery")
with col3:
    quality = st.slider("Quality", 0, 100, preset["quality"], 5, key=f"{scenario}_quality")
with col4:
    lead = st.slider("Lead time", 0, 100, preset["lead"], 5, key=f"{scenario}_lead")
weights = {"price": price, "delivery": delivery, "quality": quality, "lead": lead}
weight_total = sum(weights.values())
if weight_total == 0:
    st.warning("Set at least one KPI weight above zero to calculate a recommendation.")
    st.stop()

st.caption("Effective weights — " + " · ".join(
    f"{label}: {weights[key] / weight_total:.0%}"
    for label, key in [("Price", "price"), ("Delivery", "delivery"), ("Quality", "quality"), ("Lead time", "lead")]
))

# In the disruption scenario, simulate unavailability of the baseline balanced winner.
filtered_data = data
unavailable = None
if scenario == "Supplier disruption":
    baseline = rank_suppliers(data, selected_sku, SCENARIOS["Balanced operations"])
    if not baseline.empty:
        unavailable = baseline.iloc[0]["supplier"]
        filtered_data = data.loc[~((data["sku"] == selected_sku) & (data["supplier"] == unavailable))].copy()
        st.info(f"Simulated unavailable supplier: **{unavailable}**. Ranking the remaining eligible offers.")

ranked = rank_suppliers(filtered_data, selected_sku, weights)
if ranked.empty:
    st.error("No eligible supplier offers are available for this SKU.")
    st.stop()

st.subheader("2. Recommended supplier")
winner = ranked.iloc[0]
a,b,c,d = st.columns(4)
a.metric("Recommended supplier", winner["supplier"])
b.metric("Evaluation score", f"{winner['total_score']:.1f} / 100")
c.metric("Eligible supplier offers", str(len(ranked)))
d.metric("Unit price", f"€{winner['price_eur']:.2f}")

kpi_info = [("Price", "price_score", "price"), ("On-time delivery", "delivery_score", "delivery"),
            ("Quality", "quality_score", "quality"), ("Lead time", "lead_score", "lead")]
contributions = sorted(
    [(label, float(winner[col]) * weights[key] / weight_total)
     for label,col,key in kpi_info if weights[key] > 0],
    key=lambda pair: pair[1], reverse=True,
)
strongest = ", ".join(f"{label} ({points:.1f} points)" for label,points in contributions[:2])
if len(ranked) > 1:
    gap = float(winner["total_score"] - ranked.iloc[1]["total_score"])
    st.info(f"**Why this supplier?** {winner['supplier']} ranks first for {selected_sku}, "
            f"ahead of {ranked.iloc[1]['supplier']} by **{gap:.1f} score points**. "
            f"Largest weighted KPI contributions: {strongest}. "
            + ("The lead is narrow; test other priorities before deciding." if gap < 2 else ""))
else:
    st.info(f"**Why this supplier?** {winner['supplier']} is the only eligible supplier for this SKU.")

st.subheader("3. Supplier ranking — highest score first")
chart_data = ranked[["supplier", "total_score"]].copy()
chart_data["rank"] = range(1, len(chart_data)+1)
chart_data["label"] = chart_data["rank"].astype(str) + ". " + chart_data["supplier"]
chart = (alt.Chart(chart_data).mark_bar(cornerRadiusEnd=3).encode(
    x=alt.X("total_score:Q", title="Weighted score (out of 100)", scale=alt.Scale(domain=[0, 100])),
    y=alt.Y("label:N", sort=chart_data["label"].tolist(), title=None,
            axis=alt.Axis(labelLimit=260)),
    tooltip=[alt.Tooltip("supplier:N", title="Supplier"),
             alt.Tooltip("total_score:Q", title="Score", format=".2f")]
).properties(height=max(260, len(chart_data)*38)))
st.altair_chart(chart, width="stretch")
show = ranked[["supplier", "price_eur", "on_time_pct", "quality_pct", "lead_days", "total_score"]].copy()
show.columns = ["Supplier", "Unit price (€)", "On-time delivery (%)", "Quality (%)", "Lead time (days)", "Total score"]
show["Total score"] = show["Total score"].round(2)
st.dataframe(show, width="stretch", hide_index=True)

st.subheader("4. Head-to-head supplier comparison")
first, second = st.columns(2)
with first:
    supplier_a = st.selectbox("Supplier A", ranked["supplier"].tolist(), index=0, key="compare_a")
with second:
    candidates_b = [s for s in ranked["supplier"] if s != supplier_a]
    supplier_b = st.selectbox("Supplier B", candidates_b, index=0, key="compare_b") if candidates_b else None
if supplier_b:
    a_row = ranked.loc[ranked["supplier"] == supplier_a].iloc[0]
    b_row = ranked.loc[ranked["supplier"] == supplier_b].iloc[0]
    comparison = pd.DataFrame({
        "KPI": ["Unit price (€) ↓", "On-time delivery (%) ↑", "Quality (%) ↑", "Lead time (days) ↓", "Weighted score ↑"],
        supplier_a: [a_row["price_eur"], a_row["on_time_pct"], a_row["quality_pct"], a_row["lead_days"], a_row["total_score"]],
        supplier_b: [b_row["price_eur"], b_row["on_time_pct"], b_row["quality_pct"], b_row["lead_days"], b_row["total_score"]],
    })
    st.dataframe(comparison, width="stretch", hide_index=True)
    def kpi_winner(col, high=True):
        av, bv = float(a_row[col]), float(b_row[col])
        if abs(av-bv) < 1e-9:
            return "Tie"
        return supplier_a if ((av > bv) == high) else supplier_b
    st.caption("KPI advantages: " + " · ".join([
        f"Price: {kpi_winner('price_eur', False)}",
        f"Delivery: {kpi_winner('on_time_pct')}",
        f"Quality: {kpi_winner('quality_pct')}",
        f"Lead time: {kpi_winner('lead_days', False)}",
    ]))

st.subheader("5. Order quantity & procurement cost impact")
order_qty = st.number_input("Order quantity (units)", min_value=1, value=5000, step=500,
                            help="Fictional planning quantity. Cost = units × unit price; taxes, freight and discounts are excluded.")
cheapest = ranked.loc[ranked["price_eur"].idxmin()]
recommended_cost = float(winner["price_eur"]) * order_qty
cheapest_cost = float(cheapest["price_eur"]) * order_qty
premium = recommended_cost - cheapest_cost
m1, m2, m3 = st.columns(3)
m1.metric("Recommended supplier · order cost", f"€{recommended_cost:,.2f}")
m2.metric(f"Lowest available cost · {cheapest['supplier']}", f"€{cheapest_cost:,.2f}")
m3.metric("Extra cost for recommended supplier", f"€{premium:,.2f}")
if premium > 0.005:
    st.info(f"Choosing **{winner['supplier']}** instead of the cheapest eligible supplier costs **€{premium:,.2f} more** "
            f"for {order_qty:,.0f} units, in exchange for the performance mix selected above.")
else:
    st.success("The recommended supplier is also the lowest-price eligible option for this SKU.")
cost_table = ranked[["supplier", "price_eur"]].copy()
cost_table["Order cost (€)"] = (cost_table["price_eur"] * order_qty).round(2)
cost_table.columns = ["Supplier", "Unit price (€)", "Order cost (€)"]
with st.expander("See total order costs for all eligible suppliers"):
    st.dataframe(cost_table, hide_index=True, width="stretch")

with st.expander("How the scoring works & limitations"):
    st.markdown("""**Only suppliers offering the selected SKU are compared.**

- **Price score** = 100 × lowest eligible unit price ÷ supplier's unit price
- **On-time delivery score** = supplier's on-time delivery percentage
- **Quality score** = supplier's accepted-unit percentage
- **Lead-time score** = 100 × shortest eligible lead time ÷ supplier's lead time
- **Overall score** = sum of each KPI score × its weight, divided by the sum of weights

The four scores are **relative only to the eligible suppliers in the active scenario**. In a disruption, removing one supplier may change the price/lead-time benchmarks and therefore everyone else's scores.

The data is synthetic. Scenario weights are illustrative preferences, not forecasts. A disruption is hypothetical. Total order cost ignores shipping, taxes, discounts and capacity. This tool is a decision aid, not a purchasing authorization or a machine-learning model.
""")
st.divider()
st.caption("Live demo: Balanced operations → Cost reduction → Urgent delivery → Supplier disruption; then compare two suppliers and change order quantity.")
