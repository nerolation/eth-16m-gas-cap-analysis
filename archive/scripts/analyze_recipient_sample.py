#!/usr/bin/env python3
"""
Analyze recipient concentration using a sample of affected transactions
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pyxatu import PyXatu
import os

GAS_CAP = 16_777_216  # 2^24
BASE_GAS_COST = 21_000
SAMPLE_SIZE = 50000  # Analyze a sample of recent transactions

def get_recipient_concentration():
    """Get recipient address concentration from recent high-gas transactions"""
    
    # Initialize PyXatu client
    xatu = PyXatu()
    
    # Get the latest block
    query = """
    SELECT MAX(block_number) as latest_block 
    FROM canonical_execution_transaction
    WHERE meta_network_name = 'mainnet'
    """
    
    print("Getting latest block...")
    latest_result = xatu.execute_query(query, columns="latest_block")
    latest_block = int(latest_result.iloc[0]['latest_block'])
    
    # Sample from recent blocks (last 1000 blocks)
    start_block = latest_block - 1000
    end_block = latest_block
    
    print(f"Analyzing transactions from blocks {start_block:,} to {end_block:,}")
    
    # Query for high-gas transactions and their recipients
    query = f"""
    SELECT 
        address_to,
        COUNT(*) as transaction_count,
        AVG(gas_limit) as avg_gas_limit,
        MAX(gas_limit) as max_gas_limit,
        MIN(gas_limit) as min_gas_limit,
        COUNT(DISTINCT address_from) as unique_senders,
        SUM(gas_limit - {GAS_CAP}) as total_excess_gas
    FROM canonical_execution_transaction
    WHERE meta_network_name = 'mainnet'
        AND block_number >= {start_block}
        AND block_number < {end_block}
        AND gas_limit > {GAS_CAP}
    GROUP BY address_to
    ORDER BY transaction_count DESC
    LIMIT 1000
    """
    
    print("Querying recipient concentration...")
    df_recipients = xatu.execute_query(query)
    
    # Calculate additional metrics
    df_recipients['additional_cost_eth'] = (df_recipients['total_excess_gas'] * BASE_GAS_COST) / 1e18
    df_recipients['rank'] = range(1, len(df_recipients) + 1)
    
    # Get total count for percentage calculations
    total_query = f"""
    SELECT COUNT(*) as total_affected_transactions
    FROM canonical_execution_transaction
    WHERE meta_network_name = 'mainnet'
        AND block_number >= {start_block}
        AND block_number < {end_block}
        AND gas_limit > {GAS_CAP}
    """
    
    total_result = xatu.execute_query(total_query, columns="total_affected_transactions")
    total_affected = int(total_result.iloc[0]['total_affected_transactions'])
    
    return df_recipients, total_affected, start_block, end_block

def generate_recipient_analysis(df_recipients, total_affected, start_block, end_block):
    """Generate analysis report for recipient concentration"""
    
    # Calculate concentration metrics
    total_in_top50 = df_recipients.head(50)['transaction_count'].sum()
    pct_top50 = (total_in_top50 / total_affected) * 100 if total_affected > 0 else 0
    
    total_in_top10 = df_recipients.head(10)['transaction_count'].sum()
    pct_top10 = (total_in_top10 / total_affected) * 100 if total_affected > 0 else 0
    
    # Calculate Gini coefficient
    if len(df_recipients) > 0:
        sorted_counts = df_recipients['transaction_count'].sort_values()
        cumsum = sorted_counts.cumsum()
        n = len(sorted_counts)
        if cumsum.iloc[-1] > 0:
            gini = (n + 1 - 2 * np.sum((n + 1 - np.arange(1, n + 1)) * sorted_counts) / cumsum.iloc[-1]) / n
        else:
            gini = 0
    else:
        gini = 0
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print("\n" + "="*60)
    print("RECIPIENT CONCENTRATION ANALYSIS")
    print("="*60)
    print(f"Sample Period: Blocks {start_block:,} to {end_block:,}")
    print(f"Total Affected Transactions: {total_affected:,}")
    print(f"Unique Recipient Addresses: {len(df_recipients):,}")
    print(f"Gini Coefficient: {gini:.3f}")
    print(f"\nConcentration Metrics:")
    print(f"  • Top 10 recipients: {pct_top10:.1f}% of affected transactions")
    print(f"  • Top 50 recipients: {pct_top50:.1f}% of affected transactions")
    
    if len(df_recipients) > 0:
        print(f"\nTop 10 Recipient Addresses:")
        print("="*100)
        print(f"{'Rank':<5} {'Address':<20} {'Transactions':<12} {'Avg Gas':<12} {'Unique Senders':<15} {'Cost (ETH)':<12}")
        print("-"*100)
        
        for _, row in df_recipients.head(10).iterrows():
            addr = row['address_to'] if row['address_to'] else 'Contract Creation'
            addr_short = f"{addr[:10]}...{addr[-6:]}" if addr and addr != 'Contract Creation' else addr
            print(f"{row['rank']:<5} {addr_short:<20} {row['transaction_count']:<12,} {row['avg_gas_limit']:<12,.0f} {row['unique_senders']:<15,} {row['additional_cost_eth']:<12.6f}")
    
    # Save results
    df_recipients.to_csv(f'recipient_concentration_sample_{timestamp}.csv', index=False)
    print(f"\nResults saved to: recipient_concentration_sample_{timestamp}.csv")
    
    return df_recipients

def main():
    """Main analysis function"""
    print("Analyzing recipient address concentration (sample)...")
    
    try:
        # Get recipient data
        df_recipients, total_affected, start_block, end_block = get_recipient_concentration()
        
        # Generate analysis
        generate_recipient_analysis(df_recipients, total_affected, start_block, end_block)
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()