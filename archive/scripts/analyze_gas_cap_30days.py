#!/usr/bin/env python3
"""
Extended Gas Cap Analysis Script for 30-day Period
Optimized version using the original working approach
"""

import pandas as pd
import pyxatu
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Set pandas display options
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows', 100)

def initialize_xatu():
    """Initialize the PyXatu client"""
    return pyxatu.PyXatu()

def get_30day_transactions(xatu):
    """
    Fetch 30 days of transaction data focusing on high gas transactions
    """
    # Calculate approximate block range for 30 days
    # ~7200 blocks per day, so 30 days = ~216,000 blocks
    blocks_to_analyze = 216000
    
    # Get recent block number
    latest_block_query = """
    SELECT MAX(block_number) as latest_block 
    FROM canonical_execution_transaction
    WHERE meta_network_name = 'mainnet'
    """
    
    latest_result = xatu.execute_query(latest_block_query, columns="latest_block")
    if latest_result.empty:
        # Use fallback
        latest_block = 22678052
    else:
        latest_block = latest_result['latest_block'].iloc[0]
    
    start_block = latest_block - blocks_to_analyze
    
    print(f"Analyzing 30 days of data from block {start_block:,} to {latest_block:,}")
    
    # Query for high gas transactions only (>1M gas) to reduce data size
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
    WHERE block_number >= {start_block}
    AND block_number <= {latest_block}
    AND meta_network_name = 'mainnet'
    AND gas_limit > 1000000
    AND gas_used IS NOT NULL
    AND gas_limit IS NOT NULL
    ORDER BY block_number DESC
    LIMIT 500000
    """
    
    columns = "block_number,block_timestamp,transaction_hash,from_address,to_address,gas_used,gas_limit,gas_price,transaction_type"
    
    print("Fetching high-gas transactions (this may take a few minutes)...")
    df = xatu.execute_query(query, columns=columns)
    
    # Also get summary statistics for all transactions
    summary_query = f"""
    SELECT 
        COUNT(*) as total_transactions,
        AVG(gas_limit) as avg_gas_limit,
        MAX(gas_limit) as max_gas_limit
    FROM canonical_execution_transaction
    WHERE block_number >= {start_block}
    AND block_number <= {latest_block}
    AND meta_network_name = 'mainnet'
    AND gas_limit IS NOT NULL
    """
    
    summary_result = xatu.execute_query(summary_query, columns="total_transactions,avg_gas_limit,max_gas_limit")
    
    return df, summary_result, start_block, latest_block

def analyze_30day_impact(df, summary_result, proposed_gas_cap):
    """
    Comprehensive analysis for 30-day period
    """
    if summary_result is not None and not summary_result.empty:
        total_transactions = summary_result['total_transactions'].iloc[0]
    else:
        # Estimate: ~100 transactions per block
        total_transactions = 216000 * 100
    
    # Get affected transactions
    affected_txs = df[df['gas_limit'] > proposed_gas_cap].copy()
    affected_count = len(affected_txs)
    affected_percentage = (affected_count / total_transactions) * 100
    
    results = {
        'total_transactions': total_transactions,
        'affected_transactions': affected_count,
        'affected_percentage': affected_percentage,
        'high_gas_transactions': len(df)
    }
    
    if not affected_txs.empty:
        # Time series analysis
        affected_txs['date'] = pd.to_datetime(affected_txs['block_timestamp']).dt.date
        daily_affected = affected_txs.groupby('date').size().reset_index(name='count')
        results['daily_affected'] = daily_affected
        
        # Address analysis - Top 50
        address_stats = affected_txs.groupby('from_address').agg({
            'gas_limit': ['count', 'mean', 'max', 'sum'],
            'gas_used': ['mean', 'sum'],
            'gas_price': 'mean',
            'transaction_hash': 'first'
        }).round(0)
        
        address_stats.columns = ['_'.join(col).strip() for col in address_stats.columns]
        address_stats = address_stats.rename(columns={'transaction_hash_first': 'sample_tx'})
        
        # Calculate excess gas
        address_stats['avg_excess_gas'] = (
            affected_txs.groupby('from_address')['gas_limit'].mean() - proposed_gas_cap
        )
        address_stats['total_excess_gas'] = (
            affected_txs.groupby('from_address')['gas_limit'].sum() - 
            proposed_gas_cap * affected_txs.groupby('from_address').size()
        )
        
        # Calculate splitting costs
        BASE_GAS_COST = 21000
        address_stats['splits_required'] = np.ceil(
            affected_txs.groupby('from_address')['gas_limit'].mean() / proposed_gas_cap
        )
        address_stats['additional_tx_cost_eth'] = (
            (address_stats['splits_required'] - 1) * BASE_GAS_COST * 
            address_stats['gas_price_mean'] / 1e18
        )
        
        address_stats = address_stats.sort_values('gas_limit_count', ascending=False)
        results['address_stats'] = address_stats
        results['top_50_addresses'] = address_stats.head(50)
        
        # Transaction type breakdown
        if 'transaction_type' in affected_txs.columns:
            tx_types = affected_txs['transaction_type'].value_counts()
            results['tx_types'] = tx_types
        
        # Gas efficiency
        affected_txs['gas_efficiency'] = affected_txs['gas_used'] / affected_txs['gas_limit']
        results['avg_gas_efficiency'] = affected_txs['gas_efficiency'].mean()
        
        # Weekly pattern analysis
        affected_txs['weekday'] = pd.to_datetime(affected_txs['block_timestamp']).dt.day_name()
        weekly_pattern = affected_txs.groupby('weekday').size()
        results['weekly_pattern'] = weekly_pattern
        
    return results

def create_enhanced_visualizations(results, proposed_gas_cap):
    """
    Create professional visualizations for 30-day analysis
    """
    template = "plotly_white"
    
    # 1. Daily trend with moving average
    if 'daily_affected' in results and not results['daily_affected'].empty:
        daily_data = results['daily_affected']
        daily_data['ma7'] = daily_data['count'].rolling(window=7, center=True).mean()
        
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=daily_data['date'],
            y=daily_data['count'],
            mode='lines+markers',
            name='Daily Count',
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=5)
        ))
        
        fig1.add_trace(go.Scatter(
            x=daily_data['date'],
            y=daily_data['ma7'],
            mode='lines',
            name='7-Day MA',
            line=dict(color='#ff7f0e', width=3, dash='dash')
        ))
        
        fig1.update_layout(
            title={
                'text': f'Daily Transactions Exceeding {proposed_gas_cap:,} Gas (30-Day Period)',
                'font': {'size': 24, 'family': 'Arial Black'}
            },
            xaxis_title="Date",
            yaxis_title="Number of Transactions",
            template=template,
            height=600,
            hovermode='x unified',
            showlegend=True,
            legend=dict(x=0.02, y=0.98)
        )
        
        fig1.write_html("gas_cap_daily_trend_30d.html")
    
    # 2. Top 20 affected addresses with cost impact
    if 'address_stats' in results and not results['address_stats'].empty:
        top_20 = results['address_stats'].head(20)
        
        fig2 = make_subplots(
            rows=1, cols=2,
            column_widths=[0.6, 0.4],
            subplot_titles=('Transaction Count', 'Additional Cost (ETH)')
        )
        
        # Transaction count
        fig2.add_trace(
            go.Bar(
                y=[f"{addr[:8]}...{addr[-6:]}" for addr in top_20.index[::-1]],
                x=top_20['gas_limit_count'][::-1],
                orientation='h',
                marker_color='#1f77b4',
                text=top_20['gas_limit_count'][::-1].astype(int),
                textposition='auto',
                name='Transactions'
            ),
            row=1, col=1
        )
        
        # Additional cost
        fig2.add_trace(
            go.Bar(
                y=[f"{addr[:8]}...{addr[-6:]}" for addr in top_20.index[::-1]],
                x=top_20['additional_tx_cost_eth'][::-1],
                orientation='h',
                marker_color='#ff7f0e',
                text=[f"{x:.4f}" for x in top_20['additional_tx_cost_eth'][::-1]],
                textposition='auto',
                name='Cost (ETH)'
            ),
            row=1, col=2
        )
        
        fig2.update_layout(
            title={
                'text': 'Top 20 Most Affected Addresses',
                'font': {'size': 24, 'family': 'Arial Black'}
            },
            template=template,
            height=800,
            showlegend=False
        )
        
        fig2.update_xaxes(title_text="Number of Transactions", row=1, col=1)
        fig2.update_xaxes(title_text="Additional Cost (ETH)", row=1, col=2)
        
        fig2.write_html("gas_cap_top_addresses_30d.html")
    
    # 3. Cost impact bubble chart
    if 'address_stats' in results and not results['address_stats'].empty:
        top_cost = results['address_stats'].nlargest(15, 'additional_tx_cost_eth')
        
        fig3 = go.Figure()
        
        fig3.add_trace(go.Scatter(
            x=top_cost['gas_limit_count'],
            y=top_cost['additional_tx_cost_eth'],
            mode='markers+text',
            marker=dict(
                size=np.sqrt(top_cost['total_excess_gas'] / 1e6) * 5,
                color=top_cost['avg_excess_gas'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(
                    title="Avg Excess<br>Gas",
                    titlefont=dict(size=14)
                ),
                sizemin=10,
                line=dict(width=2, color='white')
            ),
            text=[f"{addr[:6]}..." for addr in top_cost.index],
            textposition="top center",
            textfont=dict(size=10),
            hovertemplate=(
                'Address: %{text}<br>' +
                'Transactions: %{x}<br>' +
                'Additional Cost: %{y:.4f} ETH<br>' +
                '<extra></extra>'
            )
        ))
        
        fig3.update_layout(
            title={
                'text': 'Cost Impact Analysis: Top 15 Most Affected Addresses',
                'font': {'size': 24, 'family': 'Arial Black'}
            },
            xaxis_title="Number of Affected Transactions",
            yaxis_title="Total Additional Cost (ETH)",
            template=template,
            height=700,
            xaxis=dict(gridcolor='lightgray'),
            yaxis=dict(gridcolor='lightgray')
        )
        
        fig3.write_html("gas_cap_cost_bubble_30d.html")
    
    # 4. Summary statistics dashboard
    fig4 = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Impact Overview',
            'Transaction Distribution',
            'Weekly Pattern',
            'Gas Efficiency'
        ),
        specs=[
            [{"type": "indicator"}, {"type": "pie"}],
            [{"type": "bar"}, {"type": "histogram"}]
        ],
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )
    
    # Impact gauge
    fig4.add_trace(
        go.Indicator(
            mode="number+gauge",
            value=results['affected_percentage'],
            number={'suffix': "%", 'font': {'size': 40}},
            title={'text': "Affected Transactions", 'font': {'size': 20}},
            gauge={
                'axis': {'range': [None, 0.5], 'tickwidth': 1},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 0.01], 'color': "lightgreen"},
                    {'range': [0.01, 0.05], 'color': "yellow"},
                    {'range': [0.05, 0.5], 'color': "lightcoral"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 0.1
                }
            }
        ),
        row=1, col=1
    )
    
    # Transaction type pie
    if 'tx_types' in results and not results['tx_types'].empty:
        fig4.add_trace(
            go.Pie(
                labels=[f"Type {t}" for t in results['tx_types'].index],
                values=results['tx_types'].values,
                hole=0.4,
                textinfo='label+percent',
                textposition='auto'
            ),
            row=1, col=2
        )
    
    # Weekly pattern
    if 'weekly_pattern' in results and not results['weekly_pattern'].empty:
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekly_data = results['weekly_pattern'].reindex(days_order, fill_value=0)
        
        fig4.add_trace(
            go.Bar(
                x=days_order,
                y=weekly_data.values,
                marker_color='#2ca02c',
                text=weekly_data.values,
                textposition='auto'
            ),
            row=2, col=1
        )
    
    # Gas efficiency histogram
    if 'address_stats' in results and not results['address_stats'].empty:
        efficiency_data = results['address_stats']['gas_used_mean'] / results['address_stats']['gas_limit_mean']
        
        fig4.add_trace(
            go.Histogram(
                x=efficiency_data,
                nbinsx=30,
                marker_color='#d62728',
                opacity=0.7
            ),
            row=2, col=2
        )
    
    fig4.update_layout(
        title={
            'text': 'Gas Cap Impact Dashboard - 30 Day Analysis',
            'font': {'size': 28, 'family': 'Arial Black'}
        },
        template=template,
        height=900,
        showlegend=False
    )
    
    fig4.update_xaxes(title_text="Day of Week", row=2, col=1)
    fig4.update_xaxes(title_text="Gas Efficiency Ratio", row=2, col=2)
    fig4.update_yaxes(title_text="Count", row=2, col=1)
    fig4.update_yaxes(title_text="Frequency", row=2, col=2)
    
    fig4.write_html("gas_cap_dashboard_30d.html")
    
    print("\nEnhanced visualizations created:")
    print("- gas_cap_daily_trend_30d.html")
    print("- gas_cap_top_addresses_30d.html")
    print("- gas_cap_cost_bubble_30d.html")
    print("- gas_cap_dashboard_30d.html")

def generate_top_50_table(results):
    """
    Generate formatted table of top 50 affected senders
    """
    if 'top_50_addresses' not in results:
        return None
    
    top_50 = results['top_50_addresses']
    
    table_data = []
    for i, (address, row) in enumerate(top_50.iterrows(), 1):
        table_data.append({
            'Rank': i,
            'Address': address,
            'Affected_Transactions': int(row['gas_limit_count']),
            'Avg_Gas_Limit': f"{row['gas_limit_mean']:,.0f}",
            'Max_Gas_Limit': f"{row['gas_limit_max']:,.0f}",
            'Total_Excess_Gas': f"{row['total_excess_gas']:,.0f}",
            'Avg_Gas_Efficiency': f"{row['gas_used_mean']/row['gas_limit_mean']:.2%}",
            'Est_Additional_Cost_ETH': f"{row['additional_tx_cost_eth']:.6f}",
            'Avg_Splits_Required': f"{row['splits_required']:.1f}"
        })
    
    return pd.DataFrame(table_data)

def main():
    """Main function for 30-day analysis"""
    
    PROPOSED_GAS_CAP = 16_777_216  # 2^24
    
    try:
        # Initialize
        print("Initializing PyXatu client...")
        xatu = initialize_xatu()
        
        # Fetch data
        print("\nFetching 30 days of transaction data...")
        df, summary_result, start_block, end_block = get_30day_transactions(xatu)
        
        if df.empty:
            print("No high-gas transaction data found.")
            return
        
        print(f"Fetched {len(df):,} high-gas transactions (>1M gas limit)")
        
        # Analyze
        print(f"\nAnalyzing impact of {PROPOSED_GAS_CAP:,} gas cap...")
        results = analyze_30day_impact(df, summary_result, PROPOSED_GAS_CAP)
        
        # Print summary
        print("\n" + "="*80)
        print("30-DAY GAS CAP ANALYSIS SUMMARY")
        print("="*80)
        print(f"Block Range: {start_block:,} to {end_block:,}")
        print(f"Total Transactions (estimated): {results['total_transactions']:,}")
        print(f"High Gas Transactions (>1M): {results['high_gas_transactions']:,}")
        print(f"Affected Transactions: {results['affected_transactions']:,}")
        print(f"Affected Percentage: {results['affected_percentage']:.4f}%")
        
        if 'address_stats' in results:
            print(f"\nUnique Affected Addresses: {len(results['address_stats']):,}")
            total_cost = results['address_stats']['additional_tx_cost_eth'].sum()
            print(f"Total Additional Costs: {total_cost:.4f} ETH")
            avg_cost = results['address_stats']['additional_tx_cost_eth'].mean()
            print(f"Average Additional Cost per Address: {avg_cost:.6f} ETH")
        
        # Generate visualizations
        print("\nGenerating enhanced visualizations...")
        create_enhanced_visualizations(results, PROPOSED_GAS_CAP)
        
        # Generate top 50 table
        print("\nGenerating top 50 affected senders table...")
        top_50_table = generate_top_50_table(results)
        
        if top_50_table is not None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"gas_cap_top50_senders_30d_{timestamp}.csv"
            top_50_table.to_csv(filename, index=False)
            print(f"Top 50 senders table saved to: {filename}")
            
            # Preview
            print("\nTop 10 Most Affected Senders:")
            print(top_50_table.head(10).to_string(index=False))
        
        # Save detailed analysis
        if 'address_stats' in results:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            detailed_filename = f"gas_cap_detailed_30d_{timestamp}.csv"
            results['address_stats'].to_csv(detailed_filename)
            print(f"\nDetailed analysis saved to: {detailed_filename}")
        
        print("\n30-day analysis completed successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()