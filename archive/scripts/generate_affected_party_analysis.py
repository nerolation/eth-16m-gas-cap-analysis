#!/usr/bin/env python3
"""
Generate focused statistical analysis and visualizations for affected parties
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
from datetime import datetime

def load_data():
    """Load the 6-month analysis data"""
    # Load top 50 addresses
    top50_df = pd.read_csv('gas_cap_6month_top50_20250707_080912.csv')
    
    # Load all addresses
    all_addresses_df = pd.read_csv('gas_cap_6month_all_addresses_20250707_080912.csv')
    
    return top50_df, all_addresses_df

def generate_impact_distribution_chart(all_addresses_df):
    """Generate impact distribution visualization"""
    # Categorize addresses
    all_addresses_df['category'] = pd.cut(
        all_addresses_df['transaction_count'],
        bins=[0, 10, 100, float('inf')],
        labels=['Light (<10 txs)', 'Medium (10-100 txs)', 'Heavy (>100 txs)']
    )
    
    # Create distribution chart
    fig = go.Figure()
    
    # Add histogram
    fig.add_trace(go.Histogram(
        x=all_addresses_df['transaction_count'],
        nbinsx=50,
        name='Address Distribution',
        marker_color='#1f77b4',
        opacity=0.7
    ))
    
    # Add percentile lines
    percentiles = [50, 90, 95, 99]
    colors = ['green', 'yellow', 'orange', 'red']
    
    for p, color in zip(percentiles, colors):
        value = np.percentile(all_addresses_df['transaction_count'], p)
        fig.add_vline(
            x=value,
            line_dash="dash",
            line_color=color,
            annotation_text=f"P{p}: {value:.0f} txs"
        )
    
    fig.update_layout(
        title="Affected Address Distribution by Transaction Count",
        xaxis_title="Transactions per Address",
        yaxis_title="Number of Addresses",
        xaxis_type="log",
        template="plotly_white",
        height=500
    )
    
    fig.write_html("affected_address_distribution.html")
    
    return all_addresses_df

def generate_concentration_analysis(all_addresses_df):
    """Generate concentration analysis"""
    # Sort by transaction count
    sorted_addresses = all_addresses_df.sort_values('transaction_count', ascending=False).reset_index(drop=True)
    
    # Calculate cumulative percentages
    total_affected_txs = sorted_addresses['transaction_count'].sum()
    sorted_addresses['cumulative_txs'] = sorted_addresses['transaction_count'].cumsum()
    sorted_addresses['cumulative_pct'] = (sorted_addresses['cumulative_txs'] / total_affected_txs) * 100
    
    # Create Lorenz curve
    fig = go.Figure()
    
    # Add Lorenz curve
    x = np.arange(len(sorted_addresses)) / len(sorted_addresses) * 100
    fig.add_trace(go.Scatter(
        x=x,
        y=sorted_addresses['cumulative_pct'],
        mode='lines',
        name='Actual Distribution',
        line=dict(color='#1f77b4', width=3)
    ))
    
    # Add perfect equality line
    fig.add_trace(go.Scatter(
        x=[0, 100],
        y=[0, 100],
        mode='lines',
        name='Perfect Equality',
        line=dict(color='gray', width=2, dash='dash')
    ))
    
    # Highlight key points
    key_points = [10, 50, 100, 500]
    for n in key_points:
        if n < len(sorted_addresses):
            pct_addresses = (n / len(sorted_addresses)) * 100
            pct_txs = sorted_addresses.iloc[n-1]['cumulative_pct']
            fig.add_trace(go.Scatter(
                x=[pct_addresses],
                y=[pct_txs],
                mode='markers+text',
                text=[f'Top {n}: {pct_txs:.1f}%'],
                textposition='top right',
                marker=dict(size=10, color='red'),
                showlegend=False
            ))
    
    fig.update_layout(
        title="Transaction Concentration Among Affected Addresses (Lorenz Curve)",
        xaxis_title="Cumulative % of Addresses",
        yaxis_title="Cumulative % of Affected Transactions",
        template="plotly_white",
        height=500
    )
    
    fig.write_html("transaction_concentration_lorenz.html")
    
    # Calculate Gini coefficient
    n = len(sorted_addresses)
    index = np.arange(1, n + 1)
    gini = (2 * np.sum(index * sorted_addresses['transaction_count'])) / (n * np.sum(sorted_addresses['transaction_count'])) - (n + 1) / n
    
    return gini

def generate_economic_impact_analysis(all_addresses_df):
    """Generate economic impact analysis"""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Cost Distribution by Address Category',
            'Transaction Count vs Additional Cost',
            'Cost per Transaction Distribution',
            'Top 20 Addresses by Economic Impact'
        ),
        specs=[[{"type": "box"}, {"type": "scatter"}],
               [{"type": "histogram"}, {"type": "bar"}]]
    )
    
    # 1. Box plot by category
    categories = pd.cut(
        all_addresses_df['transaction_count'],
        bins=[0, 10, 100, float('inf')],
        labels=['Light', 'Medium', 'Heavy']
    )
    
    for cat in ['Light', 'Medium', 'Heavy']:
        mask = categories == cat
        fig.add_trace(
            go.Box(
                y=all_addresses_df[mask]['additional_cost_eth'],
                name=cat,
                boxpoints='outliers'
            ),
            row=1, col=1
        )
    
    # 2. Scatter plot
    fig.add_trace(
        go.Scatter(
            x=all_addresses_df['transaction_count'],
            y=all_addresses_df['additional_cost_eth'],
            mode='markers',
            marker=dict(
                size=5,
                color=all_addresses_df['avg_gas_limit'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Avg Gas Limit", x=1.1)
            ),
            text=[f"{addr[:6]}..." for addr in all_addresses_df['address']],
            hovertemplate='Address: %{text}<br>Txs: %{x}<br>Cost: %{y:.6f} ETH'
        ),
        row=1, col=2
    )
    
    # 3. Cost per transaction histogram
    cost_per_tx = all_addresses_df['additional_cost_eth'] / all_addresses_df['transaction_count']
    fig.add_trace(
        go.Histogram(
            x=cost_per_tx,
            nbinsx=50,
            name='Cost per Tx',
            marker_color='#2ca02c'
        ),
        row=2, col=1
    )
    
    # 4. Top 20 by economic impact
    top20 = all_addresses_df.nlargest(20, 'additional_cost_eth')
    fig.add_trace(
        go.Bar(
            x=[f"{addr[:8]}..." for addr in top20['address']],
            y=top20['additional_cost_eth'],
            marker_color='#d62728',
            text=[f"{cost:.4f}" for cost in top20['additional_cost_eth']],
            textposition='auto'
        ),
        row=2, col=2
    )
    
    fig.update_xaxes(title_text="Address Category", row=1, col=1)
    fig.update_yaxes(title_text="Additional Cost (ETH)", type="log", row=1, col=1)
    
    fig.update_xaxes(title_text="Transaction Count", type="log", row=1, col=2)
    fig.update_yaxes(title_text="Additional Cost (ETH)", type="log", row=1, col=2)
    
    fig.update_xaxes(title_text="Cost per Transaction (ETH)", row=2, col=1)
    fig.update_yaxes(title_text="Frequency", row=2, col=1)
    
    fig.update_xaxes(tickangle=-45, row=2, col=2)
    fig.update_yaxes(title_text="Additional Cost (ETH)", row=2, col=2)
    
    fig.update_layout(
        title="Economic Impact Analysis of EIP-7983",
        height=800,
        template="plotly_white",
        showlegend=False
    )
    
    fig.write_html("economic_impact_analysis.html")

def generate_migration_complexity_chart(all_addresses_df):
    """Generate migration complexity analysis"""
    # Calculate migration complexity score
    all_addresses_df['complexity_score'] = (
        all_addresses_df['splits_required'] * 0.4 +
        (all_addresses_df['avg_gas_limit'] / 16777216) * 0.3 +
        np.log1p(all_addresses_df['transaction_count']) * 0.3
    )
    
    # Create bubble chart
    fig = go.Figure()
    
    # Add bubbles
    fig.add_trace(go.Scatter(
        x=all_addresses_df['transaction_count'],
        y=all_addresses_df['splits_required'],
        mode='markers',
        marker=dict(
            size=np.sqrt(all_addresses_df['additional_cost_eth']) * 1000,
            color=all_addresses_df['complexity_score'],
            colorscale='RdYlBu_r',
            showscale=True,
            colorbar=dict(title="Migration<br>Complexity"),
            sizemin=5,
            line=dict(width=1, color='white')
        ),
        text=[f"{addr[:8]}..." for addr in all_addresses_df['address']],
        hovertemplate=(
            'Address: %{text}<br>' +
            'Transactions: %{x}<br>' +
            'Avg Splits Required: %{y:.1f}<br>' +
            'Additional Cost: %{marker.size:.4f} ETH'
        )
    ))
    
    # Add annotations for top complex addresses
    top_complex = all_addresses_df.nlargest(5, 'complexity_score')
    for _, row in top_complex.iterrows():
        fig.add_annotation(
            x=row['transaction_count'],
            y=row['splits_required'],
            text=f"{row['address'][:6]}...",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="red"
        )
    
    fig.update_layout(
        title="Migration Complexity Analysis (Bubble Size = Additional Cost)",
        xaxis_title="Number of Affected Transactions",
        yaxis_title="Average Transaction Splits Required",
        xaxis_type="log",
        template="plotly_white",
        height=600
    )
    
    fig.write_html("migration_complexity_analysis.html")

def generate_summary_statistics(all_addresses_df, gini):
    """Generate summary statistics report"""
    stats = {
        "total_affected_addresses": int(len(all_addresses_df)),
        "total_affected_transactions": int(all_addresses_df['transaction_count'].sum()),
        "concentration_metrics": {
            "gini_coefficient": round(float(gini), 4),
            "top_10_address_share": round(
                float(all_addresses_df.nlargest(10, 'transaction_count')['transaction_count'].sum() / 
                all_addresses_df['transaction_count'].sum() * 100), 2
            ),
            "top_50_address_share": round(
                float(all_addresses_df.nlargest(50, 'transaction_count')['transaction_count'].sum() / 
                all_addresses_df['transaction_count'].sum() * 100), 2
            )
        },
        "economic_impact": {
            "total_additional_cost_eth": round(float(all_addresses_df['additional_cost_eth'].sum()), 4),
            "mean_cost_per_address_eth": round(float(all_addresses_df['additional_cost_eth'].mean()), 6),
            "median_cost_per_address_eth": round(float(all_addresses_df['additional_cost_eth'].median()), 6),
            "max_cost_per_address_eth": round(float(all_addresses_df['additional_cost_eth'].max()), 6)
        },
        "transaction_characteristics": {
            "mean_gas_limit": int(round(all_addresses_df['avg_gas_limit'].mean(), 0)),
            "median_gas_limit": int(round(all_addresses_df['avg_gas_limit'].median(), 0)),
            "mean_splits_required": round(float(all_addresses_df['splits_required'].mean()), 2)
        },
        "address_categories": {
            "heavy_users": int(len(all_addresses_df[all_addresses_df['transaction_count'] > 100])),
            "medium_users": int(len(all_addresses_df[(all_addresses_df['transaction_count'] > 10) & 
                                               (all_addresses_df['transaction_count'] <= 100)])),
            "light_users": int(len(all_addresses_df[all_addresses_df['transaction_count'] <= 10]))
        }
    }
    
    # Save as JSON
    with open('affected_party_statistics.json', 'w') as f:
        json.dump(stats, f, indent=2)
    
    return stats

def main():
    """Generate comprehensive affected party analysis"""
    print("Loading data...")
    top50_df, all_addresses_df = load_data()
    
    print("Generating impact distribution chart...")
    all_addresses_df = generate_impact_distribution_chart(all_addresses_df)
    
    print("Generating concentration analysis...")
    gini = generate_concentration_analysis(all_addresses_df)
    print(f"Gini coefficient: {gini:.4f}")
    
    print("Generating economic impact analysis...")
    generate_economic_impact_analysis(all_addresses_df)
    
    print("Generating migration complexity chart...")
    generate_migration_complexity_chart(all_addresses_df)
    
    print("Generating summary statistics...")
    stats = generate_summary_statistics(all_addresses_df, gini)
    
    print("\nKey Statistics:")
    print(f"- Total affected addresses: {stats['total_affected_addresses']:,}")
    print(f"- Gini coefficient: {stats['concentration_metrics']['gini_coefficient']}")
    print(f"- Top 10 address share: {stats['concentration_metrics']['top_10_address_share']}%")
    print(f"- Max individual cost: {stats['economic_impact']['max_cost_per_address_eth']} ETH")
    
    print("\nVisualizations created:")
    print("- affected_address_distribution.html")
    print("- transaction_concentration_lorenz.html")
    print("- economic_impact_analysis.html")
    print("- migration_complexity_analysis.html")
    print("- affected_party_statistics.json")

if __name__ == "__main__":
    main()