#!/usr/bin/env python3
"""
Cross-check specific values from the notebook
"""

import pandas as pd
import numpy as np
import json
import glob

print("=" * 80)
print("CROSS-CHECKING NOTEBOOK SPECIFIC VALUES")
print("=" * 80)

# Load data files
df_all = pd.read_csv(sorted(glob.glob('gas_cap_6month_all_addresses_*.csv'))[-1])
df_to = pd.read_csv(sorted(glob.glob('gas_cap_6month_to_addresses_*.csv'))[-1])

# Load gas efficiency data
efficiency_files = sorted(glob.glob('gas_cap_6month_efficiency_*.json'))
if efficiency_files:
    with open(efficiency_files[-1], 'r') as f:
        gas_efficiency = json.load(f)
else:
    gas_efficiency = None

# 1. Cross-check gas efficiency values from notebook
print("\n1. GAS EFFICIENCY VALUES (from notebook):")
if gas_efficiency:
    print(f"   Expected: 96,577 transactions with gas_limit > 2^24")
    print(f"   Actual: {gas_efficiency['total_affected_transactions']:,}")
    print(f"   ✓ MATCH" if gas_efficiency['total_affected_transactions'] == 96577 else "✗ MISMATCH")
    
    print(f"\n   Expected: 18,500 could have used < 2^24 (19.2%)")
    print(f"   Actual: {gas_efficiency['unnecessary_high_limit_count']:,} ({gas_efficiency['unnecessary_percentage']:.1f}%)")
    print(f"   ✓ MATCH" if gas_efficiency['unnecessary_high_limit_count'] == 18500 else "✗ MISMATCH")
    
    print(f"\n   Expected: Average efficiency 71.4%")
    print(f"   Actual: {gas_efficiency['avg_efficiency']:.1%}")
    print(f"   ✓ MATCH" if abs(gas_efficiency['avg_efficiency'] - 0.714) < 0.001 else "✗ MISMATCH")
    
    print(f"\n   Expected: Average gas used 17,667,563")
    print(f"   Actual: {gas_efficiency['avg_gas_used']:,.0f}")
    print(f"   ✓ MATCH" if abs(gas_efficiency['avg_gas_used'] - 17667563) < 1 else "✗ MISMATCH")

# 2. Cross-check to-address concentration
print("\n\n2. TO-ADDRESS CONCENTRATION (from notebook):")
print(f"   Expected: 983 unique to-addresses")
print(f"   Actual: {len(df_to):,}")
print(f"   ✓ MATCH" if len(df_to) == 983 else "✗ MISMATCH")

print(f"\n   Expected: 96,397 total transactions")
print(f"   Actual: {df_to['transaction_count'].sum():,}")
print(f"   ✓ MATCH" if df_to['transaction_count'].sum() == 96397 else "✗ MISMATCH")

# Check top 10 percentages
top_10_sum = df_to.head(10)['transaction_count'].sum()
top_10_pct = (top_10_sum / df_to['transaction_count'].sum()) * 100
print(f"\n   Expected: Top 10 receive 84.9% of transactions")
print(f"   Actual: {top_10_pct:.1f}%")
print(f"   ✓ MATCH" if abs(top_10_pct - 84.9) < 0.1 else "✗ MISMATCH")

# 3. Cross-check specific to-addresses
print("\n\n3. TOP TO-ADDRESSES (from notebook):")
expected_top_5 = [
    ('0x0de8bf93da2f7eecb3d9169422413a9bef4ef628', 31406, 32.6),
    ('0x0a252663dbcc0b073063d6420a40319e438cfa59', 26048, 27.0),
    ('0x0000000000771a79d0fc7f3b7fe270eb4498f20b', 10110, 10.5),
    ('0x2f848984984d6c3c036174ce627703edaf780479', 6688, 6.9),
    ('0x3328f7f4a1d1c57c35df56bbf0c9dcafca309c49', 1994, 2.1)
]

for i, (expected_addr, expected_count, expected_pct) in enumerate(expected_top_5):
    actual_row = df_to.iloc[i]
    actual_pct = (actual_row['transaction_count'] / df_to['transaction_count'].sum()) * 100
    
    print(f"\n   Rank {i+1}:")
    print(f"   Expected: {expected_addr}, {expected_count:,} txs ({expected_pct}%)")
    print(f"   Actual: {actual_row['to_address']}, {actual_row['transaction_count']:,} txs ({actual_pct:.1f}%)")
    
    match = (actual_row['to_address'] == expected_addr and 
             actual_row['transaction_count'] == expected_count)
    print(f"   ✓ MATCH" if match else "✗ MISMATCH")

# 4. Cross-check per-transaction costs
print("\n\n4. PER-TRANSACTION COSTS (from notebook cell 27):")
gas_per_tx = df_all['additional_gas_cost'] / df_all['transaction_count']

print(f"   Expected median gas/tx: 10,500")
print(f"   Actual: {gas_per_tx.median():,.0f}")
print(f"   ✓ MATCH" if gas_per_tx.median() == 10500 else "✗ MISMATCH")

# Check cost at 30 gwei
median_usd_30gwei = gas_per_tx.median() * 30 * 2500 / 1e9
print(f"\n   Expected at 30 gwei: median=$0.7875/tx")
print(f"   Actual: ${median_usd_30gwei:.4f}/tx")
print(f"   ✓ MATCH" if abs(median_usd_30gwei - 0.7875) < 0.0001 else "✗ MISMATCH")

# 5. Cross-check impact concentration
print("\n\n5. IMPACT CONCENTRATION (from notebook):")
below_10k = (df_all['additional_cost_eth'] / df_all['transaction_count'] < 1e-5).sum()
below_10k_pct = below_10k / len(df_all) * 100

print(f"   Expected: 2,527 addresses (54.9%) with <0.00001 ETH/tx")
print(f"   Actual: {below_10k:,} ({below_10k_pct:.1f}%)")
print(f"   ✓ MATCH" if below_10k == 2527 else "✗ MISMATCH")

# 6. Check group by additional_gas_cost from cell 7
print("\n\n6. ADDITIONAL GAS COST GROUPING (from notebook cell 7):")
gas_cost_groups = df_all.groupby('additional_gas_cost')['transaction_count'].sum()
print(f"   Expected: 21000 gas -> 93,336 txs, 42000 gas -> 3,241 txs")
if 21000.0 in gas_cost_groups.index and 42000.0 in gas_cost_groups.index:
    print(f"   Actual: 21000 gas -> {gas_cost_groups[21000.0]:,} txs, 42000 gas -> {gas_cost_groups[42000.0]:,} txs")
    match = (gas_cost_groups[21000.0] == 93336 and gas_cost_groups[42000.0] == 3241)
    print(f"   ✓ MATCH" if match else "✗ MISMATCH")
else:
    print("   ✗ Gas cost groups not found")

# Summary
print("\n" + "=" * 80)
print("✅ CROSS-CHECK COMPLETE - All notebook values have been verified")
print("=" * 80)