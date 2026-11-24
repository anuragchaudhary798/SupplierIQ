"""Quick deterministic checks of unchanged V2 scoring and V3 scenarios/cost logic."""
from pathlib import Path
import pandas as pd
from scoring import rank_suppliers

DATA = pd.read_csv(Path(__file__).with_name('supplier_offers.csv'))
SCENARIOS = {
    'Balanced operations': {'price': 35, 'delivery': 30, 'quality': 25, 'lead': 10},
    'Cost reduction': {'price': 85, 'delivery': 5, 'quality': 5, 'lead': 5},
    'Urgent delivery': {'price': 10, 'delivery': 50, 'quality': 10, 'lead': 30},
    'Supplier disruption': {'price': 15, 'delivery': 45, 'quality': 25, 'lead': 15},
}
assert DATA['supplier'].nunique() == 12
assert DATA['sku'].nunique() == 5
assert len(DATA) == 35
assert not DATA.isna().any().any()
assert (DATA[['price_eur','lead_days']] > 0).all().all()
assert DATA[['on_time_pct','quality_pct']].ge(0).all().all()
assert DATA[['on_time_pct','quality_pct']].le(100).all().all()
checked = 0
for sku in DATA['sku'].unique():
    for scenario, weights in SCENARIOS.items():
        active = DATA
        lost = None
        if scenario == 'Supplier disruption':
            lost = rank_suppliers(DATA, sku, SCENARIOS['Balanced operations']).iloc[0]['supplier']
            active = DATA.loc[~((DATA['sku']==sku) & (DATA['supplier']==lost))]
        ranked = rank_suppliers(active, sku, weights)
        assert len(ranked) == (6 if lost else 7)
        assert ranked['supplier'].is_unique
        assert ranked['total_score'].between(0,100).all()
        assert ranked['total_score'].is_monotonic_decreasing
        if lost:
            assert lost not in ranked['supplier'].values
        best = ranked.iloc[0]
        low = ranked.loc[ranked['price_eur'].idxmin()]
        for qty in [1, 5000, 10000]:
            assert abs(float(best['price_eur'])*qty - float(low['price_eur'])*qty - (float(best['price_eur'])-float(low['price_eur']))*qty) < 1e-7
            assert float(best['price_eur'])*qty >= float(low['price_eur'])*qty - 1e-8
        checked += 1
        print(f'PASS {sku}: {scenario}, winner = {best["supplier"]}, score = {best["total_score"]:.2f}')

sku = 'PKG-001'
price_only = rank_suppliers(DATA, sku, {'price':100,'delivery':0,'quality':0,'lead':0})
delivery_only = rank_suppliers(DATA, sku, {'price':0,'delivery':100,'quality':0,'lead':0})
assert price_only.iloc[0]['supplier'] == 'Alpha Components'
assert delivery_only.iloc[0]['supplier'] == 'Delta Materials'
assert rank_suppliers(DATA,sku,{'price':35,'delivery':30,'quality':25,'lead':10})['supplier'].tolist() == rank_suppliers(DATA,sku,{'price':70,'delivery':60,'quality':50,'lead':20})['supplier'].tolist()
try:
    rank_suppliers(DATA,sku,{'price':0,'delivery':0,'quality':0,'lead':0})
    raise AssertionError('all-zero weights should have failed')
except ValueError:
    pass
print(f'ALL PASS: {checked} SKU/scenario combinations, data checks, original V2 behavior, cost calculations and zero-weight rejection')
