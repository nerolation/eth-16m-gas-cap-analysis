#!/usr/bin/env python3
"""
Analyze the concentration of recipient addresses (address_to) for transactions
that would be affected by the EIP-7983 gas cap
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from pyxatu import PyXatu
import pickle

CACHE_DIR = "gas_cap_cache_6m"
GAS_CAP = 16_777_216  # 2^24
BASE_GAS_COST = 21_000
PARTITION_SIZE = 1000

def load_cached_batches():
    """Load all cached batch data and extract recipient information"""
    batch_files = sorted([f for f in os.listdir(CACHE_DIR) if f.endswith('.json')])
    
    print(f"Found {len(batch_files)} batch files to process")
    
    recipient_stats = {}
    total_transactions = 0
    
    for i, batch_file in enumerate(batch_files):
        if i % 10 == 0:
            print(f"Processing batch {i}/{len(batch_files)}...")
        
        batch_path = os.path.join(CACHE_DIR, batch_file)
        batch_df = pd.read_json(batch_path)
        
        if batch_df.empty:
            continue
        
        # Filter for transactions exceeding gas cap
        affected_df = batch_df[batch_df['gas_limit'] > GAS_CAP]
        
        if affected_df.empty:
            continue
        
        # Group by recipient address
        for _, tx in affected_df.iterrows():
            recipient = tx['address_to']
            if recipient not in recipient_stats:
                recipient_stats[recipient] = {
                    'transaction_count': 0,
                    'total_gas_limit': 0,
                    'max_gas_limit': 0,
                    'unique_senders': set(),
                    'total_excess_gas': 0
                }
            
            recipient_stats[recipient]['transaction_count'] += 1
            recipient_stats[recipient]['total_gas_limit'] += tx['gas_limit']
            recipient_stats[recipient]['max_gas_limit'] = max(
                recipient_stats[recipient]['max_gas_limit'], 
                tx['gas_limit']
            )
            recipient_stats[recipient]['unique_senders'].add(tx['address_from'])
            recipient_stats[recipient]['total_excess_gas'] += (tx['gas_limit'] - GAS_CAP)
        
        total_transactions += len(affected_df)
    
    print(f"\nProcessed {total_transactions} affected transactions")
    print(f"Found {len(recipient_stats)} unique recipient addresses")
    
    return recipient_stats, total_transactions

def process_recipient_stats(recipient_stats):
    """Convert recipient stats to DataFrame and calculate metrics"""
    recipient_data = []
    
    for address, stats in recipient_stats.items():
        recipient_data.append({
            'address': address,
            'transaction_count': stats['transaction_count'],
            'avg_gas_limit': stats['total_gas_limit'] / stats['transaction_count'],
            'max_gas_limit': stats['max_gas_limit'],
            'unique_sender_count': len(stats['unique_senders']),
            'total_excess_gas': stats['total_excess_gas'],
            'additional_cost_eth': (stats['total_excess_gas'] * BASE_GAS_COST) / 1e18
        })
    
    df = pd.DataFrame(recipient_data)
    df = df.sort_values('transaction_count', ascending=False).reset_index(drop=True)
    df['rank'] = range(1, len(df) + 1)
    
    return df

def generate_recipient_report(df, total_transactions):
    """Generate analysis report for recipient concentration"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Calculate concentration metrics
    total_tx_to_top50 = df.head(50)['transaction_count'].sum()
    pct_tx_to_top50 = (total_tx_to_top50 / total_transactions) * 100
    
    total_tx_to_top10 = df.head(10)['transaction_count'].sum()
    pct_tx_to_top10 = (total_tx_to_top10 / total_transactions) * 100
    
    # Calculate Gini coefficient for transaction concentration
    sorted_counts = df['transaction_count'].sort_values()
    cumsum = sorted_counts.cumsum()
    n = len(sorted_counts)
    gini = (n + 1 - 2 * np.sum((n + 1 - np.arange(1, n + 1)) * sorted_counts) / cumsum.iloc[-1]) / n
    
    report = f"""# EIP-7983 Recipient Address Concentration Analysis

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

Analysis of recipient addresses (address_to) for transactions exceeding the proposed 16,777,216 gas cap.

### Key Metrics
- **Total Affected Transactions**: {total_transactions:,}
- **Unique Recipient Addresses**: {len(df):,}
- **Gini Coefficient**: {gini:.3f} (transaction concentration)

### Concentration Analysis
- **Top 10 recipients**: {pct_tx_to_top10:.1f}% of affected transactions
- **Top 50 recipients**: {pct_tx_to_top50:.1f}% of affected transactions
- **Top 100 recipients**: {(df.head(100)['transaction_count'].sum() / total_transactions * 100):.1f}% of affected transactions

### Top 20 Recipient Addresses

| Rank | Address | Transactions | Avg Gas | Max Gas | Unique Senders | Additional Cost (ETH) |
|------|---------|--------------|---------|---------|----------------|----------------------|
"""
    
    for _, row in df.head(20).iterrows():
        addr = row['address']
        addr_short = f"{addr[:10]}...{addr[-6:]}" if addr else "None"
        report += f"| {row['rank']} | {addr_short} | {row['transaction_count']:,} | {row['avg_gas_limit']:,.0f} | {row['max_gas_limit']:,.0f} | {row['unique_sender_count']:,} | {row['additional_cost_eth']:.6f} |\n"
    
    report += f"""

### Distribution Insights

1. **Concentration Level**: {
    'Very High' if gini > 0.8 else 
    'High' if gini > 0.6 else 
    'Moderate' if gini > 0.4 else 
    'Low'
} (Gini: {gini:.3f})

2. **Average Transactions per Recipient**: {df['transaction_count'].mean():.1f}
3. **Median Transactions per Recipient**: {df['transaction_count'].median():.0f}

4. **Recipients by Transaction Volume**:
   - Recipients with >1000 transactions: {(df['transaction_count'] > 1000).sum()}
   - Recipients with >100 transactions: {(df['transaction_count'] > 100).sum()}
   - Recipients with >10 transactions: {(df['transaction_count'] > 10).sum()}
   - Recipients with 1 transaction: {(df['transaction_count'] == 1).sum()}

### Implications

The concentration analysis reveals that high-gas transactions are {
    'highly concentrated among a small number of recipient contracts' if gini > 0.6 else
    'moderately distributed across recipient contracts'
}. This suggests that the EIP-7983 impact would primarily affect interactions with a limited set of contracts.
"""
    
    # Save report
    report_filename = f'recipient_concentration_report_{timestamp}.md'
    with open(report_filename, 'w') as f:
        f.write(report)
    
    print(f"\nReport saved to: {report_filename}")
    
    # Save CSV files
    df.to_csv(f'recipient_addresses_all_{timestamp}.csv', index=False)
    df.head(100).to_csv(f'recipient_addresses_top100_{timestamp}.csv', index=False)
    
    print(f"Top 100 recipients saved to: recipient_addresses_top100_{timestamp}.csv")
    print(f"All recipients saved to: recipient_addresses_all_{timestamp}.csv")
    
    return df, report

def main():
    """Main analysis function"""
    print("Analyzing recipient address concentration for EIP-7983...")
    print("=" * 60)
    
    # Check if cache directory exists
    if not os.path.exists(CACHE_DIR):
        print(f"Error: Cache directory '{CACHE_DIR}' not found.")
        print("Please run the 6-month analysis first to generate cached data.")
        return
    
    # Load and process data
    recipient_stats, total_transactions = load_cached_batches()
    
    if not recipient_stats:
        print("No affected transactions found in cached data.")
        return
    
    # Convert to DataFrame
    df_recipients = process_recipient_stats(recipient_stats)
    
    # Generate report
    df_recipients, report = generate_recipient_report(df_recipients, total_transactions)
    
    # Save processed data for notebook use
    df_recipients.to_pickle('recipient_concentration_data.pkl')
    print("\nData saved to: recipient_concentration_data.pkl")
    
    print("\n" + "="*60)
    print("RECIPIENT CONCENTRATION SUMMARY")
    print("="*60)
    print(f"Total Recipients: {len(df_recipients):,}")
    print(f"Top 10 Recipients: {df_recipients.head(10)['transaction_count'].sum():,} transactions")
    print(f"Top 50 Recipients: {df_recipients.head(50)['transaction_count'].sum():,} transactions")
    print(f"Single-transaction Recipients: {(df_recipients['transaction_count'] == 1).sum():,}")

if __name__ == "__main__":
    main()