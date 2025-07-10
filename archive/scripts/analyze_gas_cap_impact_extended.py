#!/usr/bin/env python3
"""
Extended Gas Cap Analysis Script for 30-day Period

This script analyzes Ethereum transactions over a 30-day period to identify which ones would be affected
by implementing a lower transaction gas cap. It uses the pyxatu library to query
blockchain data efficiently and generate professional insights for gas limit proposals.
"""

import re
import pandas as pd
import pyxatu
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

# Set pandas display options for better output
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows', 100)

def initialize_xatu():
    """Initialize the PyXatu client"""
    return pyxatu.PyXatu()

def calculate_block_range_for_days(xatu, days=30):
    """
    Calculate the block range for the specified number of days
    
    Args:
        xatu: PyXatu client instance
        days: Number of days to analyze
    
    Returns:
        Tuple of (start_block, end_block, total_blocks)
    """
    # Get the latest block with proper table name
    latest_block_query = """
    SELECT MAX(block_number) as latest_block
    FROM canonical_execution_transaction
    WHERE meta_network_name = 'mainnet'
    """
    
    try:
        latest_result = xatu.execute_query(latest_block_query, columns="latest_block")
        if latest_result is None or latest_result.empty:
            raise ValueError("Could not determine latest block number")
        
        latest_block = int(latest_result['latest_block'].iloc[0])
        
        # Estimate blocks per day (approximately 7200 blocks per day at 12s per block)
        blocks_per_day = 7200
        estimated_blocks = days * blocks_per_day
        
        # Calculate start block
        start_block = latest_block - estimated_blocks
        end_block = latest_block
        total_blocks = estimated_blocks
        
        return start_block, end_block, total_blocks
        
    except Exception as e:
        print(f"Error in calculate_block_range_for_days: {e}")
        # Fallback to a recent known block range
        # Using approximate values for 30 days from a recent block
        end_block = 22678052  # From our previous analysis
        start_block = end_block - (days * 7200)
        total_blocks = end_block - start_block
        return start_block, end_block, total_blocks

def fetch_transactions_efficiently(xatu, start_block, end_block, batch_size=50000):
    """
    Fetch transaction data efficiently in batches with only necessary columns
    
    Args:
        xatu: PyXatu client instance
        start_block: Starting block number
        end_block: Ending block number
        batch_size: Number of blocks to process per batch
    
    Returns:
        DataFrame with transaction data
    """
    all_data = []
    current_block = start_block
    
    print(f"Fetching transactions from block {start_block:,} to {end_block:,}")
    print(f"Total blocks to process: {end_block - start_block:,}")
    
    while current_block < end_block:
        batch_end = min(current_block + batch_size, end_block)
        
        # Optimized query - only fetch necessary columns and filter early
        query = f"""
        SELECT 
            block_number,
            block_timestamp,
            transaction_hash,
            from_address,
            to_address,
            gas_used,
            gas_limit,
            gas_price,
            transaction_type
        FROM canonical_execution_transaction
        WHERE block_number >= {current_block}
        AND block_number < {batch_end}
        AND meta_network_name = 'mainnet'
        AND gas_limit IS NOT NULL
        AND gas_used IS NOT NULL
        AND gas_limit > 1000000  -- Pre-filter for efficiency
        ORDER BY block_number DESC
        """
        
        columns = "block_number,block_timestamp,transaction_hash,from_address,to_address,gas_used,gas_limit,gas_price,transaction_type"
        
        print(f"Processing blocks {current_block:,} to {batch_end:,} ({((current_block - start_block) / (end_block - start_block) * 100):.1f}% complete)")
        
        try:
            batch_df = xatu.execute_query(query, columns=columns)
            if not batch_df.empty:
                all_data.append(batch_df)
                print(f"  Found {len(batch_df):,} high-gas transactions in this batch")
        except Exception as e:
            print(f"Error processing batch {current_block} to {batch_end}: {e}")
        
        current_block = batch_end
    
    if all_data:
        df = pd.concat(all_data, ignore_index=True)
        print(f"\nTotal high-gas transactions found: {len(df):,}")
        return df
    else:
        return pd.DataFrame()

def get_all_transactions_summary(xatu, start_block, end_block):
    """
    Get summary statistics for all transactions in the period
    """
    query = f"""
    SELECT 
        COUNT(*) as total_transactions,
        AVG(gas_limit) as avg_gas_limit,
        quantile(0.5)(gas_limit) as median_gas_limit,
        quantile(0.99)(gas_limit) as p99_gas_limit,
        quantile(0.999)(gas_limit) as p999_gas_limit,
        MAX(gas_limit) as max_gas_limit
    FROM canonical_execution_transaction
    WHERE block_number >= {start_block}
    AND block_number < {end_block}
    AND meta_network_name = 'mainnet'
    AND gas_limit IS NOT NULL
    """
    
    columns = "total_transactions,avg_gas_limit,median_gas_limit,p99_gas_limit,p999_gas_limit,max_gas_limit"
    return xatu.execute_query(query, columns=columns)

def analyze_gas_cap_impact_extended(df, all_tx_summary, proposed_gas_cap):
    """
    Analyze the impact of gas cap with extended metrics
    """
    total_transactions = all_tx_summary['total_transactions'].iloc[0]
    
    # Get transactions affected by the cap
    affected_txs = df[df['gas_limit'] > proposed_gas_cap].copy()
    affected_count = len(affected_txs)
    affected_percentage = (affected_count / total_transactions) * 100
    
    results = {
        'total_transactions': total_transactions,
        'affected_transactions': affected_count,
        'affected_percentage': affected_percentage,
        'all_tx_stats': all_tx_summary
    }
    
    if not affected_txs.empty:
        # Time series analysis
        affected_txs['date'] = pd.to_datetime(affected_txs['block_timestamp']).dt.date
        daily_affected = affected_txs.groupby('date').size().reset_index(name='count')
        results['daily_affected'] = daily_affected
        
        # Address analysis
        address_stats = affected_txs.groupby('from_address').agg({
            'gas_limit': ['count', 'mean', 'max', 'sum'],
            'gas_used': ['mean', 'sum'],
            'transaction_hash': 'first'
        }).round(0)
        
        address_stats.columns = ['_'.join(col).strip() for col in address_stats.columns]
        address_stats = address_stats.rename(columns={'transaction_hash_first': 'sample_tx'})
        
        # Calculate excess gas and splitting requirements
        address_stats['avg_excess_gas'] = (
            affected_txs.groupby('from_address')['gas_limit'].mean() - proposed_gas_cap
        )
        address_stats['total_excess_gas'] = (
            affected_txs.groupby('from_address')['gas_limit'].sum() - 
            proposed_gas_cap * affected_txs.groupby('from_address').size()
        )
        
        # Calculate splitting costs
        BASE_GAS_COST = 21000
        avg_gas_price = affected_txs['gas_price'].mean()
        
        address_stats['splits_required'] = np.ceil(
            affected_txs.groupby('from_address')['gas_limit'].mean() / proposed_gas_cap
        )
        address_stats['additional_tx_cost_eth'] = (
            (address_stats['splits_required'] - 1) * BASE_GAS_COST * avg_gas_price / 1e18
        )
        
        address_stats = address_stats.sort_values('gas_limit_count', ascending=False)
        results['address_stats'] = address_stats
        
        # Transaction type breakdown
        tx_types = affected_txs['transaction_type'].value_counts()
        results['tx_types'] = tx_types
        
        # Gas efficiency analysis
        affected_txs['gas_efficiency'] = affected_txs['gas_used'] / affected_txs['gas_limit']
        results['avg_gas_efficiency'] = affected_txs['gas_efficiency'].mean()
        
    return results

def create_professional_visualizations(analysis_results, proposed_gas_cap):
    """
    Create high-quality, professional visualizations
    """
    # Set professional theme
    template = "plotly_white"
    colors = px.colors.qualitative.Set3
    
    # 1. Time Series of Affected Transactions
    if 'daily_affected' in analysis_results:
        daily_data = analysis_results['daily_affected']
        
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=daily_data['date'],
            y=daily_data['count'],
            mode='lines+markers',
            name='Daily Affected Transactions',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=6)
        ))
        
        # Add 7-day moving average
        daily_data['ma7'] = daily_data['count'].rolling(window=7, center=True).mean()
        fig1.add_trace(go.Scatter(
            x=daily_data['date'],
            y=daily_data['ma7'],
            mode='lines',
            name='7-Day Moving Average',
            line=dict(color='#ff7f0e', width=2, dash='dash')
        ))
        
        fig1.update_layout(
            title={
                'text': f'Daily Transactions Exceeding {proposed_gas_cap:,} Gas Limit (30-Day Period)',
                'font': {'size': 20}
            },
            xaxis_title="Date",
            yaxis_title="Number of Transactions",
            template=template,
            height=500,
            hovermode='x unified'
        )
        
        fig1.write_html("gas_cap_daily_trend_30d.html")
    
    # 2. Gas Distribution Visualization with Percentiles
    all_stats = analysis_results['all_tx_stats']
    
    fig2 = go.Figure()
    
    # Create percentile markers
    percentiles = {
        'Median (P50)': all_stats['median_gas_limit'].iloc[0],
        'P99': all_stats['p99_gas_limit'].iloc[0],
        'P99.9': all_stats['p999_gas_limit'].iloc[0],
        'Proposed Cap': proposed_gas_cap
    }
    
    # Add percentile lines
    for i, (label, value) in enumerate(percentiles.items()):
        color = colors[i % len(colors)]
        fig2.add_vline(
            x=value,
            line_dash="dash",
            line_color=color,
            annotation_text=f"{label}: {value:,.0f}",
            annotation_position="top"
        )
    
    # Add shaded regions
    fig2.add_vrect(
        x0=0, x1=all_stats['median_gas_limit'].iloc[0],
        fillcolor="green", opacity=0.1,
        annotation_text="50% of transactions"
    )
    
    fig2.add_vrect(
        x0=all_stats['p99_gas_limit'].iloc[0], x1=all_stats['max_gas_limit'].iloc[0],
        fillcolor="red", opacity=0.1,
        annotation_text="Top 1% outliers"
    )
    
    fig2.update_layout(
        title={
            'text': 'Gas Limit Distribution Percentiles (30-Day Analysis)',
            'font': {'size': 20}
        },
        xaxis_title="Gas Limit",
        xaxis_type="log",
        template=template,
        height=500,
        showlegend=False
    )
    
    fig2.write_html("gas_cap_distribution_percentiles_30d.html")
    
    # 3. Top Affected Addresses Visualization
    if 'address_stats' in analysis_results:
        top_addresses = analysis_results['address_stats'].head(20)
        
        fig3 = go.Figure()
        
        # Create horizontal bar chart
        fig3.add_trace(go.Bar(
            y=top_addresses.index[::-1],
            x=top_addresses['gas_limit_count'][::-1],
            orientation='h',
            marker_color='#1f77b4',
            text=top_addresses['gas_limit_count'][::-1],
            textposition='auto'
        ))
        
        fig3.update_layout(
            title={
                'text': 'Top 20 Most Affected Addresses by Transaction Count',
                'font': {'size': 20}
            },
            xaxis_title="Number of Affected Transactions",
            yaxis_title="From Address",
            template=template,
            height=600,
            margin=dict(l=300)
        )
        
        # Format y-axis labels
        fig3.update_yaxis(
            tickfont=dict(family='monospace', size=10)
        )
        
        fig3.write_html("gas_cap_top_affected_addresses_30d.html")
        
        # 4. Cost Impact Bubble Chart
        top_cost_addresses = analysis_results['address_stats'].nlargest(15, 'additional_tx_cost_eth')
        
        fig4 = go.Figure()
        
        fig4.add_trace(go.Scatter(
            x=top_cost_addresses['gas_limit_count'],
            y=top_cost_addresses['additional_tx_cost_eth'],
            mode='markers+text',
            marker=dict(
                size=top_cost_addresses['total_excess_gas'] / 1e6,
                color=top_cost_addresses['avg_excess_gas'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Avg Excess Gas"),
                sizemin=5
            ),
            text=[addr[:8] + "..." for addr in top_cost_addresses.index],
            textposition="top center",
            hovertemplate=(
                'Address: %{text}<br>' +
                'Transactions: %{x}<br>' +
                'Additional Cost: %{y:.4f} ETH<br>' +
                '<extra></extra>'
            )
        ))
        
        fig4.update_layout(
            title={
                'text': 'Cost Impact Analysis: Top 15 Most Affected Addresses',
                'font': {'size': 20}
            },
            xaxis_title="Number of Affected Transactions",
            yaxis_title="Total Additional Cost (ETH)",
            template=template,
            height=600
        )
        
        fig4.write_html("gas_cap_cost_impact_bubble_30d.html")
    
    # 5. Transaction Type Breakdown
    if 'tx_types' in analysis_results:
        tx_types = analysis_results['tx_types']
        
        fig5 = go.Figure()
        
        fig5.add_trace(go.Pie(
            labels=[f"Type {t}" for t in tx_types.index],
            values=tx_types.values,
            hole=0.4,
            marker_colors=colors[:len(tx_types)]
        ))
        
        fig5.update_layout(
            title={
                'text': 'Affected Transactions by Type',
                'font': {'size': 20}
            },
            template=template,
            height=500
        )
        
        fig5.write_html("gas_cap_tx_types_30d.html")
    
    # 6. Summary Dashboard
    fig6 = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Impact Overview',
            'Gas Efficiency Distribution',
            'Daily Trend (Last 7 Days)',
            'Cost Distribution'
        ),
        specs=[
            [{"type": "indicator"}, {"type": "histogram"}],
            [{"type": "scatter"}, {"type": "box"}]
        ]
    )
    
    # Impact indicator
    fig6.add_trace(
        go.Indicator(
            mode="number+gauge+delta",
            value=analysis_results['affected_percentage'],
            title={'text': "Affected Transactions (%)"},
            delta={'reference': 0.1, 'relative': True},
            gauge={
                'axis': {'range': [None, 1]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 0.01], 'color': "lightgreen"},
                    {'range': [0.01, 0.1], 'color': "yellow"},
                    {'range': [0.1, 1], 'color': "lightred"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 0.05
                }
            }
        ),
        row=1, col=1
    )
    
    # Add other subplot components as needed
    
    fig6.update_layout(
        title={
            'text': 'Gas Cap Impact Dashboard - 30 Day Analysis',
            'font': {'size': 24}
        },
        template=template,
        height=800,
        showlegend=False
    )
    
    fig6.write_html("gas_cap_dashboard_30d.html")
    
    print("\nProfessional visualizations created:")
    print("- gas_cap_daily_trend_30d.html")
    print("- gas_cap_distribution_percentiles_30d.html")
    print("- gas_cap_top_affected_addresses_30d.html")
    print("- gas_cap_cost_impact_bubble_30d.html")
    print("- gas_cap_tx_types_30d.html")
    print("- gas_cap_dashboard_30d.html")

def generate_top_50_senders_table(analysis_results):
    """
    Generate a formatted table of the top 50 most affected senders
    """
    if 'address_stats' not in analysis_results:
        return None
    
    top_50 = analysis_results['address_stats'].head(50)
    
    # Create formatted table
    table_data = []
    for i, (address, row) in enumerate(top_50.iterrows(), 1):
        table_data.append({
            'Rank': i,
            'Address': address,
            'Affected Txs': int(row['gas_limit_count']),
            'Avg Gas Limit': f"{row['gas_limit_mean']:,.0f}",
            'Max Gas Limit': f"{row['gas_limit_max']:,.0f}",
            'Total Excess Gas': f"{row['total_excess_gas']:,.0f}",
            'Est. Additional Cost (ETH)': f"{row['additional_tx_cost_eth']:.6f}",
            'Avg Splits Required': f"{row['splits_required']:.1f}"
        })
    
    return pd.DataFrame(table_data)

def main():
    """Main function to run the extended 30-day gas cap analysis"""
    
    # Configuration
    PROPOSED_GAS_CAP = 16_777_216  # 2^24
    ANALYSIS_DAYS = 30
    
    try:
        # Initialize pyxatu client
        print("Initializing PyXatu client...")
        xatu = initialize_xatu()
        
        # Calculate block range for 30 days
        print(f"\nCalculating block range for {ANALYSIS_DAYS} days...")
        start_block, end_block, total_blocks = calculate_block_range_for_days(xatu, ANALYSIS_DAYS)
        print(f"Block range: {start_block:,} to {end_block:,} ({total_blocks:,} blocks)")
        
        # Get summary statistics for all transactions
        print("\nFetching summary statistics for all transactions...")
        all_tx_summary = get_all_transactions_summary(xatu, start_block, end_block)
        
        if all_tx_summary is None or all_tx_summary.empty:
            print("Failed to fetch summary statistics. Using estimated values.")
            # Create dummy summary for continuation
            all_tx_summary = pd.DataFrame({
                'total_transactions': [216000 * 100],  # Estimate ~100 tx per block
                'avg_gas_limit': [250000],
                'median_gas_limit': [84000],
                'p99_gas_limit': [2000000],
                'p999_gas_limit': [10000000],
                'max_gas_limit': [30000000]
            })
        
        print(f"Total transactions in period: {all_tx_summary['total_transactions'].iloc[0]:,}")
        
        # Fetch high-gas transactions efficiently
        print(f"\nFetching high-gas transactions (>1M gas limit)...")
        df = fetch_transactions_efficiently(xatu, start_block, end_block)
        
        if df.empty:
            print("No high-gas transaction data found.")
            return
        
        # Analyze gas cap impact
        print(f"\nAnalyzing impact of {PROPOSED_GAS_CAP:,} gas cap...")
        analysis_results = analyze_gas_cap_impact_extended(df, all_tx_summary, PROPOSED_GAS_CAP)
        
        # Print summary
        print("\n" + "="*80)
        print("30-DAY GAS CAP ANALYSIS SUMMARY")
        print("="*80)
        print(f"Analysis Period: {ANALYSIS_DAYS} days")
        print(f"Total Transactions: {analysis_results['total_transactions']:,}")
        print(f"Affected Transactions: {analysis_results['affected_transactions']:,}")
        print(f"Affected Percentage: {analysis_results['affected_percentage']:.4f}%")
        
        if 'address_stats' in analysis_results:
            print(f"Unique Affected Addresses: {len(analysis_results['address_stats']):,}")
            total_cost = analysis_results['address_stats']['additional_tx_cost_eth'].sum()
            print(f"Total Additional Costs: {total_cost:.4f} ETH")
        
        # Generate visualizations
        print("\nGenerating professional visualizations...")
        create_professional_visualizations(analysis_results, PROPOSED_GAS_CAP)
        
        # Generate top 50 senders table
        print("\nGenerating top 50 affected senders table...")
        top_50_table = generate_top_50_senders_table(analysis_results)
        
        if top_50_table is not None:
            # Save to CSV
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            top_50_filename = f"gas_cap_top50_senders_30d_{timestamp}.csv"
            top_50_table.to_csv(top_50_filename, index=False)
            print(f"Top 50 senders table saved to: {top_50_filename}")
            
            # Print first 10 for preview
            print("\nPreview - Top 10 Most Affected Senders:")
            print(top_50_table.head(10).to_string(index=False))
        
        # Save detailed results
        if 'address_stats' in analysis_results:
            detailed_filename = f"gas_cap_detailed_analysis_30d_{timestamp}.csv"
            analysis_results['address_stats'].to_csv(detailed_filename)
            print(f"\nDetailed analysis saved to: {detailed_filename}")
        
        print("\n30-day analysis completed successfully!")
        
    except Exception as e:
        print(f"Error occurred during analysis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()