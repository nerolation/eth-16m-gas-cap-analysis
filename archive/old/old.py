#!/usr/bin/env python3
"""
Gas Cap Analysis Script

This script analyzes Ethereum transactions to identify which ones would be affected
by implementing a lower transaction gas cap. It uses the pyxatu library to query
blockchain data and generate insights for gas limit proposals.
"""

import re
import pandas as pd
import pyxatu
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np

# Set pandas display options for better output
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows', 100)

def initialize_xatu():
    """Initialize the PyXatu client"""
    return pyxatu.PyXatu()

def get_recent_transactions(xatu, blocks_to_analyze=1000, start_block=None):
    """
    Fetch recent transaction data from Ethereum mainnet
    
    Args:
        xatu: PyXatu client instance
        blocks_to_analyze: Number of recent blocks to analyze
        start_block: Starting block number (if None, uses recent blocks)
    
    Returns:
        DataFrame with transaction data
    """
    if start_block is None:
        # Get recent block number and work backwards
        latest_block_query = """
        SELECT MAX(block_number) as latest_block 
        FROM canonical_execution_transaction
        WHERE meta_network_name = 'mainnet'
        """
        latest_result = xatu.execute_query(latest_block_query, columns="latest_block")
        if latest_result.empty:
            raise ValueError("Could not determine latest block number")
        
        latest_block = latest_result['latest_block'].iloc[0]
        start_block = latest_block - blocks_to_analyze
    
    print(f"Analyzing transactions from block {start_block} to {start_block + blocks_to_analyze}")
    
    query = f"""
    SELECT 
        block_number,
        transaction_hash,
        from_address,
        to_address,
        gas_used,
        gas_limit,
        gas_price,
        value,
        transaction_type,
        transaction_index
    FROM canonical_execution_transaction
    WHERE block_number >= {start_block}
    AND block_number < {start_block + blocks_to_analyze}
    AND meta_network_name = 'mainnet'
    AND gas_used IS NOT NULL
    AND gas_limit IS NOT NULL
    ORDER BY block_number DESC, transaction_index
    """
    
    columns = "block_number,transaction_hash,from_address,to_address,gas_used,gas_limit,gas_price,value,transaction_type,transaction_index"
    
    print("Executing query to fetch transaction data...")
    df = xatu.execute_query(query, columns=columns)
    
    return df

def analyze_gas_distribution_statistics(df):
    """
    Analyze the gas limit distribution to understand skewness and outliers
    
    Args:
        df: DataFrame with transaction data
    
    Returns:
        Dictionary with distribution statistics
    """
    gas_limits = df['gas_limit']
    
    # Calculate percentiles to understand distribution
    percentiles = [50, 90, 95, 99, 99.5, 99.9, 99.95, 99.99]
    percentile_values = {f'p{p}': gas_limits.quantile(p/100) for p in percentiles}
    
    # Calculate skewness and outlier thresholds
    q1 = gas_limits.quantile(0.25)
    q3 = gas_limits.quantile(0.75)
    iqr = q3 - q1
    outlier_threshold = q3 + 1.5 * iqr
    extreme_outlier_threshold = q3 + 3 * iqr
    
    outliers = df[df['gas_limit'] > outlier_threshold]
    extreme_outliers = df[df['gas_limit'] > extreme_outlier_threshold]
    
    return {
        'percentiles': percentile_values,
        'q1': q1,
        'q3': q3,
        'iqr': iqr,
        'outlier_threshold': outlier_threshold,
        'extreme_outlier_threshold': extreme_outlier_threshold,
        'outlier_count': len(outliers),
        'outlier_percentage': (len(outliers) / len(df)) * 100,
        'extreme_outlier_count': len(extreme_outliers),
        'extreme_outlier_percentage': (len(extreme_outliers) / len(df)) * 100,
        'mean': gas_limits.mean(),
        'median': gas_limits.median(),
        'std': gas_limits.std(),
        'skewness': gas_limits.skew()
    }

def analyze_address_impact(df, gas_cap):
    """
    Analyze impact on specific addresses that would be affected by gas cap
    
    Args:
        df: DataFrame with transaction data
        gas_cap: Gas cap limit to analyze
    
    Returns:
        DataFrame with address-level impact analysis
    """
    affected_txs = df[df['gas_limit'] > gas_cap].copy()
    
    if affected_txs.empty:
        return pd.DataFrame()
    
    # Group by from_address to analyze per-address impact
    address_analysis = affected_txs.groupby('from_address').agg({
        'gas_limit': ['count', 'mean', 'median', 'max', 'sum'],
        'gas_used': ['mean', 'sum'],
        'gas_price': ['mean'],
        'value': ['sum'],
        'transaction_hash': 'first'  # Just to keep one tx hash as reference
    }).round(0)
    
    # Flatten column names
    address_analysis.columns = ['_'.join(col).strip() for col in address_analysis.columns]
    address_analysis = address_analysis.rename(columns={'transaction_hash_first': 'sample_tx_hash'})
    
    # Calculate additional metrics
    address_analysis['excess_gas_per_tx'] = affected_txs.groupby('from_address')['gas_limit'].mean() - gas_cap
    address_analysis['total_excess_gas'] = (affected_txs.groupby('from_address')['gas_limit'].sum() - 
                                          gas_cap * affected_txs.groupby('from_address').size())
    
    # Calculate estimated splitting costs (assuming 21k base gas per additional tx)
    BASE_GAS_COST = 21000
    address_analysis['estimated_additional_txs'] = np.ceil(address_analysis['total_excess_gas'] / gas_cap)
    address_analysis['estimated_additional_gas_cost'] = (address_analysis['estimated_additional_txs'] * 
                                                       BASE_GAS_COST * address_analysis['gas_price_mean'])
    
    # Sort by total impact (excess gas)
    address_analysis = address_analysis.sort_values('total_excess_gas', ascending=False)
    
    return address_analysis

def calculate_transaction_splitting_costs(df, gas_cap):
    """
    Calculate detailed costs for splitting transactions that exceed gas cap
    
    Args:
        df: DataFrame with transaction data
        gas_cap: Gas cap limit
    
    Returns:
        DataFrame with splitting cost analysis
    """
    affected_txs = df[df['gas_limit'] > gas_cap].copy()
    
    if affected_txs.empty:
        return pd.DataFrame()
    
    BASE_GAS_COST = 21000  # Base cost for each transaction
    
    # Calculate how many transactions each would need to be split into
    affected_txs['splits_needed'] = np.ceil(affected_txs['gas_limit'] / gas_cap)
    affected_txs['excess_gas'] = affected_txs['gas_limit'] - gas_cap
    
    # Calculate additional costs from splitting
    affected_txs['additional_base_costs'] = (affected_txs['splits_needed'] - 1) * BASE_GAS_COST
    affected_txs['additional_fee_wei'] = affected_txs['additional_base_costs'] * affected_txs['gas_price']
    affected_txs['additional_fee_eth'] = affected_txs['additional_fee_wei'] / 1e18
    
    # Calculate original transaction cost for comparison
    affected_txs['original_gas_cost_wei'] = affected_txs['gas_used'] * affected_txs['gas_price']
    affected_txs['original_gas_cost_eth'] = affected_txs['original_gas_cost_wei'] / 1e18
    
    # Calculate percentage increase in costs
    affected_txs['cost_increase_percentage'] = (affected_txs['additional_fee_wei'] / 
                                              affected_txs['original_gas_cost_wei']) * 100
    
    return affected_txs[[
        'block_number', 'transaction_hash', 'from_address', 'to_address',
        'gas_limit', 'gas_used', 'gas_price', 'excess_gas', 'splits_needed',
        'additional_base_costs', 'additional_fee_wei', 'additional_fee_eth',
        'original_gas_cost_wei', 'original_gas_cost_eth', 'cost_increase_percentage'
    ]].sort_values('additional_fee_eth', ascending=False)

def analyze_gas_cap_impact(df, proposed_gas_caps):
    """
    Analyze the impact of different gas cap proposals with enhanced address and cost analysis
    
    Args:
        df: DataFrame with transaction data
        proposed_gas_caps: List of proposed gas cap limits
    
    Returns:
        Dictionary with analysis results
    """
    total_transactions = len(df)
    
    results = {}
    
    for gas_cap in proposed_gas_caps:
        affected_txs = df[df['gas_limit'] > gas_cap]
        affected_count = len(affected_txs)
        affected_percentage = (affected_count / total_transactions) * 100
        
        # Calculate gas usage statistics for affected transactions
        if not affected_txs.empty:
            avg_gas_limit = affected_txs['gas_limit'].mean()
            median_gas_limit = affected_txs['gas_limit'].median()
            max_gas_limit = affected_txs['gas_limit'].max()
            
            # Analyze transaction types
            tx_type_breakdown = affected_txs['transaction_type'].value_counts() if 'transaction_type' in affected_txs.columns else pd.Series()
            
            # Calculate potential gas savings if cap was applied
            excess_gas = affected_txs['gas_limit'] - gas_cap
            total_excess_gas = excess_gas.sum()
            avg_excess_gas = excess_gas.mean()
            
            # Address-level analysis
            address_impact = analyze_address_impact(df, gas_cap)
            unique_addresses_affected = len(address_impact)
            
            # Transaction splitting cost analysis
            splitting_costs = calculate_transaction_splitting_costs(df, gas_cap)
            total_additional_costs_eth = splitting_costs['additional_fee_eth'].sum() if not splitting_costs.empty else 0
            avg_additional_costs_eth = splitting_costs['additional_fee_eth'].mean() if not splitting_costs.empty else 0
            
        else:
            avg_gas_limit = median_gas_limit = max_gas_limit = 0
            tx_type_breakdown = pd.Series()
            total_excess_gas = avg_excess_gas = 0
            address_impact = pd.DataFrame()
            unique_addresses_affected = 0
            splitting_costs = pd.DataFrame()
            total_additional_costs_eth = avg_additional_costs_eth = 0
        
        results[gas_cap] = {
            'affected_transactions': affected_count,
            'affected_percentage': affected_percentage,
            'unique_addresses_affected': unique_addresses_affected,
            'avg_gas_limit': avg_gas_limit,
            'median_gas_limit': median_gas_limit,
            'max_gas_limit': max_gas_limit,
            'transaction_type_breakdown': tx_type_breakdown,
            'total_excess_gas': total_excess_gas,
            'avg_excess_gas': avg_excess_gas,
            'address_impact': address_impact,
            'splitting_costs': splitting_costs,
            'total_additional_costs_eth': total_additional_costs_eth,
            'avg_additional_costs_eth': avg_additional_costs_eth
        }
    
    return results

def generate_visualizations(df, analysis_results, proposed_gas_caps, dist_stats):
    """
    Generate visualizations focused on skewed distribution and outliers
    
    Args:
        df: DataFrame with transaction data
        analysis_results: Results from analyze_gas_cap_impact
        proposed_gas_caps: List of proposed gas cap limits
        dist_stats: Distribution statistics
    """
    
    # 1. Gas limit distribution with focus on tail (log scale)
    fig1 = px.histogram(
        df, 
        x='gas_limit', 
        nbins=100, 
        title='Gas Limit Distribution (Log Scale) - Highlighting Outliers',
        labels={'gas_limit': 'Gas Limit', 'count': 'Number of Transactions'}
    )
    fig1.update_xaxes(type="log")
    
    # Add vertical lines for percentiles and proposed caps
    colors = ['green', 'orange', 'red', 'purple', 'brown']
    for i, gas_cap in enumerate(proposed_gas_caps):
        fig1.add_vline(
            x=gas_cap, 
            line_dash="dash", 
            line_color=colors[i % len(colors)],
            annotation_text=f"Cap: {gas_cap:,}"
        )
    
    # Add percentile lines
    fig1.add_vline(x=dist_stats['percentiles']['p99'], line_dash="dot", line_color="red", annotation_text="99th percentile")
    fig1.add_vline(x=dist_stats['outlier_threshold'], line_dash="dot", line_color="orange", annotation_text="Outlier threshold")
    
    fig1.show()
    
    # 2. Cost impact analysis - Additional costs for affected addresses
    if analysis_results[proposed_gas_caps[0]]['affected_transactions'] > 0:
        cost_data = []
        for gas_cap in proposed_gas_caps:
            cost_data.append({
                'Gas Cap': f"{gas_cap:,}",
                'Total Additional Costs (ETH)': analysis_results[gas_cap]['total_additional_costs_eth'],
                'Affected Addresses': analysis_results[gas_cap]['unique_addresses_affected']
            })
        
        cost_df = pd.DataFrame(cost_data)
        
        fig2 = px.bar(
            cost_df, 
            x='Gas Cap', 
            y='Total Additional Costs (ETH)',
            title='Total Additional Costs from Transaction Splitting',
            labels={'Total Additional Costs (ETH)': 'Additional Costs (ETH)'}
        )
        fig2.show()
        
        # 3. Number of affected addresses
        fig3 = px.bar(
            cost_df, 
            x='Gas Cap', 
            y='Affected Addresses',
            title='Number of Unique Addresses Affected by Gas Caps'
        )
        fig3.show()
    
    # 4. Outlier analysis - Box plot showing distribution with outliers
    # Limit to reasonable range for visualization
    df_viz = df[df['gas_limit'] <= dist_stats['percentiles']['p99.9']].copy()
    
    fig4 = px.box(
        df_viz, 
        y='gas_limit',
        title='Gas Limit Distribution (up to 99.9th percentile) - Box Plot',
        labels={'gas_limit': 'Gas Limit'}
    )
    
    # Add horizontal lines for proposed caps
    for gas_cap in proposed_gas_caps:
        if gas_cap <= dist_stats['percentiles']['p99.9']:
            fig4.add_hline(y=gas_cap, line_dash="dash", annotation_text=f"Cap: {gas_cap:,}")
    
    fig4.show()
    
    # 5. Gas efficiency analysis - focusing on outliers
    outliers = df[df['gas_limit'] > dist_stats['outlier_threshold']]
    if not outliers.empty:
        sample_outliers = outliers.sample(n=min(1000, len(outliers)))
        
        fig5 = px.scatter(
            sample_outliers,
            x='gas_limit',
            y='gas_used',
            title='Gas Efficiency for Outlier Transactions (Gas Limit > Outlier Threshold)',
            labels={'gas_limit': 'Gas Limit', 'gas_used': 'Gas Used'},
            opacity=0.7
        )
        
        # Add diagonal line
        max_gas = max(sample_outliers['gas_limit'].max(), sample_outliers['gas_used'].max())
        fig5.add_trace(go.Scatter(
            x=[0, max_gas],
            y=[0, max_gas],
            mode='lines',
            name='Gas Used = Gas Limit',
            line=dict(dash='dash', color='red')
        ))
        
        fig5.show()

def print_gas_distribution_analysis(dist_stats):
    """
    Print gas distribution statistics focusing on skewness and outliers
    
    Args:
        dist_stats: Results from analyze_gas_distribution_statistics
    """
    print("\n" + "="*80)
    print("GAS DISTRIBUTION ANALYSIS - SKEWNESS & OUTLIERS")
    print("="*80)
    
    print(f"\nDistribution Statistics:")
    print(f"  Mean: {dist_stats['mean']:,.0f}")
    print(f"  Median: {dist_stats['median']:,.0f}")
    print(f"  Standard Deviation: {dist_stats['std']:,.0f}")
    print(f"  Skewness: {dist_stats['skewness']:.2f} (highly right-skewed if > 1)")
    
    print(f"\nPercentile Analysis:")
    for percentile, value in dist_stats['percentiles'].items():
        print(f"  {percentile}: {value:,.0f}")
    
    print(f"\nOutlier Analysis:")
    print(f"  IQR: {dist_stats['iqr']:,.0f}")
    print(f"  Outlier Threshold (Q3 + 1.5*IQR): {dist_stats['outlier_threshold']:,.0f}")
    print(f"  Outliers: {dist_stats['outlier_count']:,} ({dist_stats['outlier_percentage']:.4f}%)")
    print(f"  Extreme Outlier Threshold (Q3 + 3*IQR): {dist_stats['extreme_outlier_threshold']:,.0f}")
    print(f"  Extreme Outliers: {dist_stats['extreme_outlier_count']:,} ({dist_stats['extreme_outlier_percentage']:.4f}%)")

def print_detailed_analysis(analysis_results, proposed_gas_caps):
    """
    Print detailed analysis results with address and cost focus
    
    Args:
        analysis_results: Results from analyze_gas_cap_impact
        proposed_gas_caps: List of proposed gas cap limits
    """
    print("\n" + "="*80)
    print("GAS CAP IMPACT ANALYSIS REPORT - ADDRESS & COST FOCUS")
    print("="*80)
    
    for gas_cap in proposed_gas_caps:
        result = analysis_results[gas_cap]
        
        print(f"\nProposed Gas Cap: {gas_cap:,}")
        print("-" * 50)
        print(f"Affected Transactions: {result['affected_transactions']:,} ({result['affected_percentage']:.2f}%)")
        print(f"Unique Affected Addresses: {result['unique_addresses_affected']:,}")
        
        if result['affected_transactions'] > 0:
            print(f"\nGas Limit Statistics (affected transactions):")
            print(f"  Average: {result['avg_gas_limit']:,.0f}")
            print(f"  Median: {result['median_gas_limit']:,.0f}")
            print(f"  Maximum: {result['max_gas_limit']:,}")
            print(f"  Total Excess Gas: {result['total_excess_gas']:,}")
            print(f"  Average Excess Gas per TX: {result['avg_excess_gas']:,.0f}")
            
            print(f"\nTransaction Splitting Cost Impact:")
            print(f"  Total Additional Costs: {result['total_additional_costs_eth']:.4f} ETH")
            print(f"  Average Additional Cost per TX: {result['avg_additional_costs_eth']:.6f} ETH")
            
            if not result['transaction_type_breakdown'].empty:
                print(f"\nTransaction Type Breakdown:")
                for tx_type, count in result['transaction_type_breakdown'].items():
                    print(f"  Type {tx_type}: {count}")
            
            # Show top affected addresses
            if not result['address_impact'].empty:
                print(f"\nTop 10 Most Affected Addresses:")
                top_addresses = result['address_impact'].head(10)
                print(f"{'Address':<42} {'Affected TXs':<12} {'Total Excess Gas':<15} {'Additional Cost (ETH)':<20}")
                print("-" * 90)
                for addr, row in top_addresses.iterrows():
                    print(f"{addr:<42} {row['gas_limit_count']:<12.0f} {row['total_excess_gas']:<15.0f} {row['estimated_additional_gas_cost']/1e18:<20.6f}")
            
            # Show most expensive transactions to split
            if not result['splitting_costs'].empty:
                print(f"\nTop 5 Most Expensive Transactions to Split:")
                top_expensive = result['splitting_costs'].head(5)
                print(f"{'Transaction Hash':<66} {'Splits':<7} {'Additional Cost (ETH)':<20}")
                print("-" * 95)
                for _, row in top_expensive.iterrows():
                    print(f"{row['transaction_hash']:<66} {row['splits_needed']:<7.0f} {row['additional_fee_eth']:<20.6f}")
        else:
            print("No transactions would be affected by this gas cap.")

def analyze_high_gas_transactions(df, threshold=1000000):
    """
    Analyze transactions with unusually high gas limits
    
    Args:
        df: DataFrame with transaction data
        threshold: Gas limit threshold for "high gas" transactions
    
    Returns:
        DataFrame with high gas transactions
    """
    high_gas_txs = df[df['gas_limit'] >= threshold].copy()
    
    if not high_gas_txs.empty:
        print(f"\nHigh Gas Transactions (>= {threshold:,} gas):")
        print("-" * 50)
        print(f"Count: {len(high_gas_txs)}")
        print(f"Percentage of total: {(len(high_gas_txs) / len(df)) * 100:.4f}%")
        
        # Show top 10 highest gas transactions
        top_gas_txs = high_gas_txs.nlargest(10, 'gas_limit')[
            ['block_number', 'transaction_hash', 'gas_limit', 'gas_used', 'from_address', 'to_address']
        ]
        
        print("\nTop 10 Highest Gas Limit Transactions:")
        print(top_gas_txs.to_string(index=False))
    
    return high_gas_txs

def main():
    """Main function to run the enhanced gas cap analysis"""
    
    # Configuration
    PROPOSED_GAS_CAPS = [int(2**24)]  # Different cap proposals
    BLOCKS_TO_ANALYZE = 1000  # Analyze last 1000 blocks
    
    try:
        # Initialize pyxatu client
        print("Initializing PyXatu client...")
        xatu = initialize_xatu()
        
        # Fetch transaction data
        print("Fetching transaction data...")
        df = get_recent_transactions(xatu, blocks_to_analyze=BLOCKS_TO_ANALYZE)
        
        if df.empty:
            print("No transaction data found. Please check your query parameters.")
            return
        
        print(f"Fetched {len(df):,} transactions")
        
        # Basic statistics
        print(f"\nBasic Statistics:")
        print(f"Gas Limit - Min: {df['gas_limit'].min():,}, Max: {df['gas_limit'].max():,}, Mean: {df['gas_limit'].mean():,.0f}")
        print(f"Gas Used - Min: {df['gas_used'].min():,}, Max: {df['gas_used'].max():,}, Mean: {df['gas_used'].mean():,.0f}")
        
        # Analyze gas distribution for skewness and outliers
        print("\nAnalyzing gas distribution statistics...")
        dist_stats = analyze_gas_distribution_statistics(df)
        print_gas_distribution_analysis(dist_stats)
        
        # Analyze gas cap impact with address and cost focus
        print("\nAnalyzing gas cap impact with address and cost analysis...")
        analysis_results = analyze_gas_cap_impact(df, PROPOSED_GAS_CAPS)
        
        # Print detailed analysis
        print_detailed_analysis(analysis_results, PROPOSED_GAS_CAPS)
        
        # Analyze high gas transactions
        analyze_high_gas_transactions(df)
        
        # Generate visualizations
        print("\nGenerating enhanced visualizations...")
        generate_visualizations(df, analysis_results, PROPOSED_GAS_CAPS, dist_stats)
        
        # Save enhanced results to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save main transaction data
        output_filename = f"gas_cap_analysis_{timestamp}.csv"
        df.to_csv(output_filename, index=False)
        print(f"\nTransaction data saved to: {output_filename}")
        
        # Save address impact analysis for most restrictive cap
        most_restrictive_cap = min(PROPOSED_GAS_CAPS)
        address_impact = analysis_results[most_restrictive_cap]['address_impact']
        if not address_impact.empty:
            address_filename = f"address_impact_{most_restrictive_cap}_{timestamp}.csv"
            address_impact.to_csv(address_filename)
            print(f"Address impact analysis saved to: {address_filename}")
        
        # Save splitting costs analysis
        splitting_costs = analysis_results[most_restrictive_cap]['splitting_costs']
        if not splitting_costs.empty:
            splitting_filename = f"splitting_costs_{most_restrictive_cap}_{timestamp}.csv"
            splitting_costs.to_csv(splitting_filename, index=False)
            print(f"Transaction splitting costs saved to: {splitting_filename}")
        
        # Create enhanced summary report
        summary_data = []
        for gas_cap in PROPOSED_GAS_CAPS:
            result = analysis_results[gas_cap]
            summary_data.append({
                'gas_cap': gas_cap,
                'affected_transactions': result['affected_transactions'],
                'affected_percentage': result['affected_percentage'],
                'unique_addresses_affected': result['unique_addresses_affected'],
                'avg_gas_limit_affected': result['avg_gas_limit'],
                'total_excess_gas': result['total_excess_gas'],
                'total_additional_costs_eth': result['total_additional_costs_eth'],
                'avg_additional_costs_eth': result['avg_additional_costs_eth']
            })
        
        summary_df = pd.DataFrame(summary_data)
        summary_filename = f"gas_cap_summary_{timestamp}.csv"
        summary_df.to_csv(summary_filename, index=False)
        print(f"Enhanced summary report saved to: {summary_filename}")
        
        # Print key insights
        print(f"\n" + "="*80)
        print("KEY INSIGHTS")
        print("="*80)
        print(f"Distribution Skewness: {dist_stats['skewness']:.2f} (highly right-skewed)")
        print(f"99th Percentile Gas Limit: {dist_stats['percentiles']['p99']:,.0f}")
        print(f"Outliers (>{dist_stats['outlier_threshold']:,.0f}): {dist_stats['outlier_count']:,} ({dist_stats['outlier_percentage']:.4f}%)")
        
        most_restrictive_result = analysis_results[most_restrictive_cap]
        if most_restrictive_result['affected_transactions'] > 0:
            print(f"\nMost Restrictive Cap ({most_restrictive_cap:,}):")
            print(f"  - Affects {most_restrictive_result['unique_addresses_affected']:,} unique addresses")
            print(f"  - Total additional costs: {most_restrictive_result['total_additional_costs_eth']:.4f} ETH")
            print(f"  - Average additional cost per affected transaction: {most_restrictive_result['avg_additional_costs_eth']:.6f} ETH")
        
    except Exception as e:
        print(f"Error occurred during analysis: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()