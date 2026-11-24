"""Transparent, beginner-friendly supplier scoring for SupplierIQ."""
import pandas as pd

KPI_COLUMNS = ['price_eur', 'on_time_pct', 'quality_pct', 'lead_days']


def rank_suppliers(data: pd.DataFrame, sku: str, weights: dict) -> pd.DataFrame:
    """Rank only suppliers that offer the selected SKU. Higher score is better."""
    subset = data.loc[data['sku'] == sku].copy()
    if subset.empty:
        return subset
    weight_total = sum(weights.values())
    if weight_total <= 0:
        raise ValueError('At least one KPI weight must be greater than zero.')

    # Relative price and lead-time competitiveness within the chosen SKU.
    # A ratio of best available / supplier value makes smaller numbers better.
    subset['price_score'] = 100 * subset['price_eur'].min() / subset['price_eur']
    subset['delivery_score'] = subset['on_time_pct']
    subset['quality_score'] = subset['quality_pct']
    subset['lead_score'] = 100 * subset['lead_days'].min() / subset['lead_days']

    subset['total_score'] = (
        weights['price'] * subset['price_score']
        + weights['delivery'] * subset['delivery_score']
        + weights['quality'] * subset['quality_score']
        + weights['lead'] * subset['lead_score']
    ) / weight_total

    return subset.sort_values(['total_score', 'supplier'], ascending=[False, True]).reset_index(drop=True)
