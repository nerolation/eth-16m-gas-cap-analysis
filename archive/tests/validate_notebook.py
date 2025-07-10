#!/usr/bin/env python3
"""
Validate notebook calculations independently
"""

import pandas as pd
import numpy as np
import os
import glob

print("=" * 80)
print("VALIDATING NOTEBOOK CALCULATIONS")
print("=" * 80)

# Load the data files that the notebook uses
top50_files = sorted(glob.glob('gas_cap_6month_top50_*.csv'))
all_files = sorted(glob.glob('gas_cap_6month_all_addresses_*.csv'))
to_files = sorted(glob.glob('gas_cap_6month_to_addresses_*.csv'))

if not top50_files or not all_files:
    print("ERROR: Data files not found. Please run the analysis first.")
    exit(1)

# Load the latest files
df_top50 = pd.read_csv(top50_files[-1])
df_all = pd.read_csv(all_files[-1])
df_to = pd.read_csv(to_files[-1]) if to_files else None

print(f"\nLoaded data files:")
print(f"  - Top 50: {top50_files[-1]}")
print(f"  - All addresses: {all_files[-1]}")
if df_to is not None:
    print(f"  - To addresses: {to_files[-1]}")

# 1. Verify basic statistics
print("\n1. BASIC STATISTICS VALIDATION:")
print(f"   - Unique affected addresses: {len(df_all):,}")
print(f"   - Total affected transactions: {df_all['transaction_count'].sum():,}")

# 2. Verify impact concentration (Lorenz curve / Gini)
print("\n2. IMPACT CONCENTRATION VALIDATION:")
# Calculate total cost for each address
df_all['total_cost'] = df_all['additional_cost_eth'] * df_all['transaction_count']
sorted_df = df_all.sort_values('total_cost')
cumsum_cost = sorted_df['total_cost'].cumsum()
total_cost = sorted_df['total_cost'].sum()

# Calculate Gini coefficient
n = len(sorted_df)
x = np.arange(1, n + 1) / n * 100
y = cumsum_cost / total_cost * 100
area_under_lorenz = np.trapz(y, x)
area_under_equality = 0.5 * 100 * 100
gini = (area_under_equality - area_under_lorenz) / area_under_equality

print(f"   - Gini coefficient: {gini:.3f}")

# Top 10% impact
top_10_pct = int(len(df_all) * 0.1)
top_10_pct_cost = df_all.nlargest(top_10_pct, 'total_cost')['total_cost'].sum()
top_10_pct_share = top_10_pct_cost / total_cost * 100
print(f"   - Top 10% addresses account for: {top_10_pct_share:.1f}% of impact")

# 3. Verify distribution statistics
print("\n3. DISTRIBUTION STATISTICS:")
single_tx_count = (df_all['transaction_count'] == 1).sum()
single_tx_pct = single_tx_count / len(df_all) * 100
print(f"   - Addresses with 1 tx: {single_tx_count:,} ({single_tx_pct:.1f}%)")

high_tx_count = (df_all['transaction_count'] > 100).sum()
high_tx_pct = high_tx_count / len(df_all) * 100
print(f"   - Addresses with >100 tx: {high_tx_count:,} ({high_tx_pct:.1f}%)")

# Top 50 share
top_50_tx_share = df_top50['transaction_count'].sum() / df_all['transaction_count'].sum() * 100
top_50_cost_share = (df_top50['additional_cost_eth'] * df_top50['transaction_count']).sum() / total_cost * 100
print(f"   - Top 50 addresses: {top_50_tx_share:.1f}% of txs, {top_50_cost_share:.1f}% of cost")

# 4. Verify gas cost statistics
print("\n4. GAS COST STATISTICS:")
if 'additional_gas_cost' in df_all.columns:
    total_gas_cost = (df_all['additional_gas_cost'] * df_all['transaction_count']).sum()
    avg_gas_per_addr = df_all['additional_gas_cost'].mean()
    median_gas_per_addr = df_all['additional_gas_cost'].median()
    
    print(f"   - Total additional gas cost: {total_gas_cost:,.0f} gas units")
    print(f"   - Average gas cost per address: {avg_gas_per_addr:,.0f} gas units")
    print(f"   - Median gas cost per address: {median_gas_per_addr:,.0f} gas units")
    
    # Verify splits calculation
    df_all['calc_splits'] = np.ceil(df_all['avg_gas_limit'] / 16_777_216)
    df_all['calc_gas_cost'] = (df_all['calc_splits'] - 1) * 21000
    
    # Check if our calculation matches
    gas_diff = abs(df_all['additional_gas_cost'] - df_all['calc_gas_cost']).sum()
    print(f"   - Gas cost calculation difference: {gas_diff:.0f} (should be 0)")

# 5. Verify to-address concentration
if df_to is not None:
    print("\n5. TO-ADDRESS CONCENTRATION:")
    print(f"   - Unique to-addresses: {len(df_to):,}")
    print(f"   - Total transactions to these addresses: {df_to['transaction_count'].sum():,}")
    
    concentration_ratio = len(df_to) / len(df_all)
    print(f"   - Concentration ratio: {concentration_ratio:.2f}")
    
    # Top 10 recipients
    top_10_to_share = df_to.head(10)['transaction_count'].sum() / df_to['transaction_count'].sum() * 100
    print(f"   - Top 10 recipients: {top_10_to_share:.1f}% of transactions")

# 6. Verify per-transaction impact
print("\n6. PER-TRANSACTION IMPACT:")
eth_per_tx = df_all['additional_cost_eth'] / df_all['transaction_count']
print(f"   - Min ETH/tx: {eth_per_tx.min():.8f}")
print(f"   - Median ETH/tx: {eth_per_tx.median():.8f}")
print(f"   - Mean ETH/tx: {eth_per_tx.mean():.8f}")
print(f"   - Max ETH/tx: {eth_per_tx.max():.8f}")

if 'additional_gas_cost' in df_all.columns:
    gas_per_tx = df_all['additional_gas_cost'] / df_all['transaction_count']
    print(f"\n   - Min gas/tx: {gas_per_tx.min():,.0f}")
    print(f"   - Median gas/tx: {gas_per_tx.median():,.0f}")
    print(f"   - Mean gas/tx: {gas_per_tx.mean():,.0f}")
    print(f"   - Max gas/tx: {gas_per_tx.max():,.0f}")

# 7. Verify economic impact
print("\n7. ECONOMIC IMPACT VALIDATION:")
total_eth_cost = (df_all['additional_cost_eth'] * df_all['transaction_count']).sum()
avg_eth_per_addr = total_eth_cost / len(df_all)

print(f"   - Total ETH cost: {total_eth_cost:.4f} ETH")
print(f"   - Average ETH per address: {avg_eth_per_addr:.6f} ETH")

# Cost at different gas prices
if 'additional_gas_cost' in df_all.columns:
    for gwei in [20, 30, 50, 100]:
        total_usd = total_gas_cost * gwei * 2500 / 1e9
        avg_usd = (total_gas_cost / len(df_all)) * gwei * 2500 / 1e9
        print(f"   - At {gwei} gwei & $2500/ETH: Total ${total_usd:,.2f}, Avg ${avg_usd:.2f}/addr")

# 8. Check for data consistency
print("\n8. DATA CONSISTENCY CHECKS:")
# All gas limits should be > 16,777,216
above_cap = (df_all['avg_gas_limit'] > 16_777_216).all()
print(f"   - All avg gas limits > cap: {above_cap}")

# All costs should be positive
positive_costs = (df_all['additional_cost_eth'] > 0).all()
print(f"   - All costs positive: {positive_costs}")

# Transaction counts should be positive
positive_txs = (df_all['transaction_count'] > 0).all()
print(f"   - All transaction counts positive: {positive_txs}")

# Max gas should be >= avg gas
max_ge_avg = (df_all['max_gas_limit'] >= df_all['avg_gas_limit']).all()
print(f"   - Max gas >= avg gas for all: {max_ge_avg}")

print("\n" + "=" * 80)
print("✅ VALIDATION COMPLETE")
print("=" * 80)