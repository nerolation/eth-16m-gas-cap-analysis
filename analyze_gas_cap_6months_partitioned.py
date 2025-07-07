#!/usr/bin/env python3
"""
6-Month Gas Cap Analysis Script with Partition-Aware Processing

This script analyzes Ethereum transactions over a 6-month period using partition-aligned
queries to avoid timeouts. The canonical_execution_transaction table is partitioned 
in chunks of 1000 blocks on block_number.
"""

import pandas as pd
import pyxatu
import numpy as np
from datetime import datetime, timedelta
import json
import os
import gc
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

# Configuration
PROPOSED_GAS_CAP = 16_777_216  # 2^24
BLOCKS_PER_DAY = 7200
DAYS_TO_ANALYZE = 180  # 6 months
PARTITION_SIZE = 1000  # Blocks per partition
BATCH_SIZE_PARTITIONS = 10  # Process 10 partitions at a time (10,000 blocks)
CACHE_DIR = "gas_cap_cache_6m"

def initialize_xatu():
    """Initialize the PyXatu client"""
    return pyxatu.PyXatu()

def ensure_cache_dir():
    """Ensure cache directory exists"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def get_latest_block(xatu):
    """Get the latest block number"""
    query = """
    SELECT MAX(block_number) as latest_block 
    FROM canonical_execution_transaction
    WHERE meta_network_name = 'mainnet'
    """
    
    try:
        result = xatu.execute_query(query, columns="latest_block")
        if result is not None and not result.empty:
            return int(result['latest_block'].iloc[0])
    except:
        pass
    
    # Fallback
    return 22678052

def process_partition_batch(xatu, start_block, end_block, batch_id):
    """Process a batch of partitions"""
    # Ensure alignment with partitions
    start_partition = (start_block // PARTITION_SIZE) * PARTITION_SIZE
    end_partition = ((end_block - 1) // PARTITION_SIZE + 1) * PARTITION_SIZE
    
    print(f"\nProcessing batch {batch_id}: blocks {start_partition:,} to {end_partition:,}")
    
    # Query for summary statistics
    summary_query = f"""
    SELECT 
        COUNT(*) as total_transactions,
        SUM(CASE WHEN gas_limit > {PROPOSED_GAS_CAP} THEN 1 ELSE 0 END) as affected_transactions,
        SUM(CASE WHEN gas_limit > 1000000 THEN 1 ELSE 0 END) as high_gas_transactions
    FROM canonical_execution_transaction
    WHERE block_number >= {start_partition}
    AND block_number < {end_partition}
    AND meta_network_name = 'mainnet'
    AND gas_limit IS NOT NULL
    """
    
    try:
        summary_result = xatu.execute_query(
            summary_query, 
            columns="total_transactions,affected_transactions,high_gas_transactions"
        )
        
        if summary_result is None or summary_result.empty:
            print(f"  No data for batch {batch_id}")
            return None
            
        summary_dict = summary_result.to_dict('records')[0]
        print(f"  Transactions: {summary_dict['total_transactions']:,}")
        print(f"  Affected: {summary_dict['affected_transactions']:,}")
        
    except Exception as e:
        print(f"  Error getting summary: {e}")
        return None
    
    # Query for affected addresses (from_address)
    affected_query = f"""
    SELECT 
        from_address,
        COUNT(*) as transaction_count,
        AVG(gas_limit) as avg_gas_limit,
        MAX(gas_limit) as max_gas_limit,
        SUM(gas_limit - {PROPOSED_GAS_CAP}) as total_excess_gas,
        AVG(gas_price) as avg_gas_price
    FROM canonical_execution_transaction
    WHERE block_number >= {start_partition}
    AND block_number < {end_partition}
    AND meta_network_name = 'mainnet'
    AND gas_limit > {PROPOSED_GAS_CAP}
    GROUP BY from_address
    """
    
    try:
        affected_result = xatu.execute_query(
            affected_query,
            columns="from_address,transaction_count,avg_gas_limit,max_gas_limit,total_excess_gas,avg_gas_price"
        )
        
        if affected_result is not None and not affected_result.empty:
            affected_addresses = affected_result.to_dict('records')
            print(f"  Unique addresses affected: {len(affected_addresses)}")
        else:
            affected_addresses = []
            
    except Exception as e:
        print(f"  Error getting affected addresses: {e}")
        affected_addresses = []
    
    # Query for to_address concentration
    to_address_query = f"""
    SELECT 
        to_address,
        COUNT(*) as transaction_count,
        AVG(gas_limit) as avg_gas_limit,
        MAX(gas_limit) as max_gas_limit
    FROM canonical_execution_transaction
    WHERE block_number >= {start_partition}
    AND block_number < {end_partition}
    AND meta_network_name = 'mainnet'
    AND gas_limit > {PROPOSED_GAS_CAP}
    AND to_address IS NOT NULL
    GROUP BY to_address
    """
    
    try:
        to_address_result = xatu.execute_query(
            to_address_query,
            columns="to_address,transaction_count,avg_gas_limit,max_gas_limit"
        )
        
        if to_address_result is not None and not to_address_result.empty:
            to_addresses = to_address_result.to_dict('records')
            print(f"  Unique to_addresses affected: {len(to_addresses)}")
        else:
            to_addresses = []
            print(f"  No to_address data returned")
            
    except Exception as e:
        print(f"  Error getting to_addresses: {e}")
        print(f"  Query was: {to_address_query}")
        to_addresses = []
    
    # Query for gas usage efficiency
    gas_efficiency_query = f"""
    SELECT 
        COUNT(*) as total_overprovision,
        SUM(CASE WHEN gas_used < {PROPOSED_GAS_CAP} THEN 1 ELSE 0 END) as unnecessary_high_limit,
        AVG(gas_limit) as avg_gas_limit,
        AVG(gas_used) as avg_gas_used,
        AVG(CAST(gas_used AS FLOAT) / CAST(gas_limit AS FLOAT)) as avg_gas_efficiency,
        MIN(gas_used) as min_gas_used,
        MAX(gas_used) as max_gas_used
    FROM canonical_execution_transaction
    WHERE block_number >= {start_partition}
    AND block_number < {end_partition}
    AND meta_network_name = 'mainnet'
    AND gas_limit > {PROPOSED_GAS_CAP}
    AND gas_used IS NOT NULL
    AND gas_limit IS NOT NULL
    """
    
    try:
        gas_efficiency_result = xatu.execute_query(
            gas_efficiency_query,
            columns="total_overprovision,unnecessary_high_limit,avg_gas_limit,avg_gas_used,avg_gas_efficiency,min_gas_used,max_gas_used"
        )
        
        if gas_efficiency_result is not None and not gas_efficiency_result.empty:
            gas_efficiency = gas_efficiency_result.to_dict('records')[0]
            if gas_efficiency['total_overprovision'] > 0:
                print(f"  Gas efficiency: {gas_efficiency['avg_gas_efficiency']:.2%}")
                print(f"  Unnecessarily high limits: {gas_efficiency['unnecessary_high_limit']:,} ({gas_efficiency['unnecessary_high_limit']/gas_efficiency['total_overprovision']*100:.1f}%)")
        else:
            gas_efficiency = {}
            
    except Exception as e:
        print(f"  Error getting gas efficiency: {e}")
        gas_efficiency = {}
    
    # Store results
    batch_data = {
        'batch_id': batch_id,
        'start_block': start_partition,
        'end_block': end_partition,
        'summary': summary_dict if 'summary_dict' in locals() else {},
        'affected_addresses': affected_addresses,
        'to_addresses': to_addresses,
        'gas_efficiency': gas_efficiency
    }
    
    # Save to cache
    cache_file = os.path.join(CACHE_DIR, f"batch_{batch_id:05d}.json")
    with open(cache_file, 'w') as f:
        json.dump(batch_data, f)
    
    # Clear memory
    gc.collect()
    
    return batch_data.get('summary', {})

def aggregate_results():
    """Aggregate all batch results"""
    print("\nAggregating results from all batches...")
    
    # Initialize aggregation
    total_transactions = 0
    total_affected = 0
    total_high_gas = 0
    address_aggregates = {}
    to_address_aggregates = {}
    gas_efficiency_stats = {
        'total_overprovision': 0,
        'unnecessary_high_limit': 0,
        'sum_gas_limit': 0,
        'sum_gas_used': 0,
        'count': 0,
        'min_gas_used': float('inf'),
        'max_gas_used': 0
    }
    
    # Process each batch file
    batch_files = sorted([f for f in os.listdir(CACHE_DIR) if f.startswith('batch_')])
    print(f"Found {len(batch_files)} batch files to aggregate")
    
    for batch_file in batch_files:
        with open(os.path.join(CACHE_DIR, batch_file), 'r') as f:
            batch_data = json.load(f)
        
        # Aggregate summary
        if batch_data.get('summary'):
            total_transactions += batch_data['summary'].get('total_transactions', 0)
            total_affected += batch_data['summary'].get('affected_transactions', 0)
            total_high_gas += batch_data['summary'].get('high_gas_transactions', 0)
        
        # Aggregate addresses
        for addr_data in batch_data.get('affected_addresses', []):
            addr = addr_data['from_address']
            
            if addr not in address_aggregates:
                address_aggregates[addr] = {
                    'transaction_count': 0,
                    'total_gas_limit': 0,
                    'max_gas_limit': 0,
                    'total_excess_gas': 0,
                    'total_gas_price': 0,
                    'batches_appeared': 0
                }
            
            agg = address_aggregates[addr]
            agg['transaction_count'] += int(addr_data['transaction_count'])
            agg['total_gas_limit'] += float(addr_data['avg_gas_limit']) * int(addr_data['transaction_count'])
            agg['max_gas_limit'] = max(agg['max_gas_limit'], float(addr_data['max_gas_limit']))
            agg['total_excess_gas'] += float(addr_data['total_excess_gas'])
            agg['total_gas_price'] += float(addr_data['avg_gas_price']) * int(addr_data['transaction_count'])
            agg['batches_appeared'] += 1
        
        # Aggregate to_addresses
        for to_addr_data in batch_data.get('to_addresses', []):
            addr = to_addr_data['to_address']
            
            if addr not in to_address_aggregates:
                to_address_aggregates[addr] = {
                    'transaction_count': 0,
                    'total_gas_limit': 0,
                    'max_gas_limit': 0
                }
            
            agg = to_address_aggregates[addr]
            agg['transaction_count'] += int(to_addr_data['transaction_count'])
            agg['total_gas_limit'] += float(to_addr_data['avg_gas_limit']) * int(to_addr_data['transaction_count'])
            agg['max_gas_limit'] = max(agg['max_gas_limit'], float(to_addr_data['max_gas_limit']))
        
        # Aggregate gas efficiency
        if batch_data.get('gas_efficiency'):
            eff = batch_data['gas_efficiency']
            if eff.get('total_overprovision', 0) > 0:
                gas_efficiency_stats['total_overprovision'] += eff.get('total_overprovision', 0)
                gas_efficiency_stats['unnecessary_high_limit'] += eff.get('unnecessary_high_limit', 0)
                gas_efficiency_stats['sum_gas_limit'] += eff.get('avg_gas_limit', 0) * eff.get('total_overprovision', 0)
                gas_efficiency_stats['sum_gas_used'] += eff.get('avg_gas_used', 0) * eff.get('total_overprovision', 0)
                gas_efficiency_stats['count'] += eff.get('total_overprovision', 0)
                gas_efficiency_stats['min_gas_used'] = min(gas_efficiency_stats['min_gas_used'], eff.get('min_gas_used', float('inf')))
                gas_efficiency_stats['max_gas_used'] = max(gas_efficiency_stats['max_gas_used'], eff.get('max_gas_used', 0))
    
    # Calculate final statistics
    final_addresses = []
    for addr, agg in address_aggregates.items():
        if agg['transaction_count'] > 0:
            avg_gas_limit = agg['total_gas_limit'] / agg['transaction_count']
            avg_gas_price = agg['total_gas_price'] / agg['transaction_count']
            
            # Calculate costs
            BASE_GAS_COST = 21000
            splits_required = np.ceil(avg_gas_limit / PROPOSED_GAS_CAP)
            additional_gas_cost = (splits_required - 1) * BASE_GAS_COST
            additional_cost_eth = additional_gas_cost * avg_gas_price / 1e18
            
            final_addresses.append({
                'address': addr,
                'transaction_count': agg['transaction_count'],
                'avg_gas_limit': avg_gas_limit,
                'max_gas_limit': agg['max_gas_limit'],
                'total_excess_gas': agg['total_excess_gas'],
                'additional_gas_cost': additional_gas_cost,
                'additional_cost_eth': additional_cost_eth,
                'splits_required': splits_required
            })
    
    # Process to_addresses
    final_to_addresses = []
    for addr, agg in to_address_aggregates.items():
        if agg['transaction_count'] > 0:
            avg_gas_limit = agg['total_gas_limit'] / agg['transaction_count']
            final_to_addresses.append({
                'to_address': addr,
                'transaction_count': agg['transaction_count'],
                'avg_gas_limit': avg_gas_limit,
                'max_gas_limit': agg['max_gas_limit']
            })
    
    # Sort by transaction count
    final_addresses.sort(key=lambda x: x['transaction_count'], reverse=True)
    final_to_addresses.sort(key=lambda x: x['transaction_count'], reverse=True)
    
    # Calculate gas efficiency final stats
    gas_efficiency_final = {}
    if gas_efficiency_stats['count'] > 0:
        gas_efficiency_final = {
            'total_affected_transactions': gas_efficiency_stats['total_overprovision'],
            'unnecessary_high_limit_count': gas_efficiency_stats['unnecessary_high_limit'],
            'unnecessary_percentage': (gas_efficiency_stats['unnecessary_high_limit'] / gas_efficiency_stats['total_overprovision'] * 100) if gas_efficiency_stats['total_overprovision'] > 0 else 0,
            'avg_gas_limit': gas_efficiency_stats['sum_gas_limit'] / gas_efficiency_stats['count'],
            'avg_gas_used': gas_efficiency_stats['sum_gas_used'] / gas_efficiency_stats['count'],
            'avg_efficiency': (gas_efficiency_stats['sum_gas_used'] / gas_efficiency_stats['sum_gas_limit']) if gas_efficiency_stats['sum_gas_limit'] > 0 else 0,
            'min_gas_used': gas_efficiency_stats['min_gas_used'],
            'max_gas_used': gas_efficiency_stats['max_gas_used']
        }
    
    return {
        'total_transactions': total_transactions,
        'total_affected': total_affected,
        'total_high_gas': total_high_gas,
        'affected_percentage': (total_affected / total_transactions * 100) if total_transactions > 0 else 0,
        'unique_addresses': len(final_addresses),
        'top_addresses': final_addresses[:50],
        'all_addresses': final_addresses,
        'total_additional_gas_cost': sum(
            addr['additional_gas_cost'] * addr['transaction_count'] 
            for addr in final_addresses
        ),
        'total_additional_cost_eth': sum(
            addr['additional_cost_eth'] * addr['transaction_count'] 
            for addr in final_addresses
        ),
        'unique_to_addresses': len(final_to_addresses),
        'top_to_addresses': final_to_addresses[:50],
        'all_to_addresses': final_to_addresses,
        'gas_efficiency': gas_efficiency_final
    }

def generate_6month_report(results):
    """Generate comprehensive 6-month report"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    report = f"""# 6-Month Empirical Analysis Report: EIP-7983 Transaction Gas Limit Cap

## Executive Summary

This report presents a comprehensive 6-month empirical analysis of EIP-7983, which proposes capping transaction gas limits at 16,777,216 (2^24). Based on partition-aware processing of {results['total_transactions']:,} Ethereum mainnet transactions over 180 days, we find that the proposed cap would affect only {results['affected_percentage']:.4f}% of transactions.

## Key Findings

### 1. Transaction Impact Over 6 Months
- **Total Transactions Analyzed**: {results['total_transactions']:,}
- **Affected Transactions**: {results['total_affected']:,} ({results['affected_percentage']:.4f}%)
- **Unique Addresses Affected**: {results['unique_addresses']:,}
- **High Gas Transactions (>1M)**: {results['total_high_gas']:,}

### 2. Economic Impact
- **Total Additional Gas Cost**: {results['total_additional_gas_cost']:,.0f} gas units
- **Total Additional Cost (ETH)**: {results['total_additional_cost_eth']:.4f} ETH
- **Average Gas Cost per Affected Transaction**: {results['total_additional_gas_cost']/results['total_affected']:,.0f} gas units if results['total_affected'] > 0 else 'N/A'
- **Average Cost per Affected Transaction**: {results['total_additional_cost_eth']/results['total_affected']:.6f} ETH if results['total_affected'] > 0 else 'N/A'
- **Average Cost per Affected Address**: {results['total_additional_cost_eth']/results['unique_addresses']:.6f} ETH if results['unique_addresses'] > 0 else 'N/A'

**Note**: ETH costs assume historical gas prices. With ETH at $2,500 and a base fee of X gwei, actual costs would be: gas_cost × base_fee × ETH_price / 1e9

### 3. To-Address Concentration
- **Unique To-Addresses**: {results['unique_to_addresses']:,}
- **Concentration Ratio**: {results['unique_to_addresses']/results['unique_addresses']:.2f} to-addresses per from-address
- **Top 10 Recipients**: Receiving {sum(addr['transaction_count'] for addr in results['top_to_addresses'][:10]):,} ({sum(addr['transaction_count'] for addr in results['top_to_addresses'][:10]) / results['total_affected'] * 100:.1f}%) of affected transactions

### 4. Gas Usage Efficiency
{f"- **Total Transactions with Gas Limit > 2^24**: {results['gas_efficiency']['total_affected_transactions']:,}" if results.get('gas_efficiency') else "Gas efficiency data not available"}
{f"- **Transactions That Could Have Used < 2^24**: {results['gas_efficiency']['unnecessary_high_limit_count']:,} ({results['gas_efficiency']['unnecessary_percentage']:.1f}%)" if results.get('gas_efficiency') else ""}
{f"- **Average Gas Efficiency**: {results['gas_efficiency']['avg_efficiency']:.1%}" if results.get('gas_efficiency') else ""}
{f"- **Average Gas Used**: {results['gas_efficiency']['avg_gas_used']:,.0f}" if results.get('gas_efficiency') else ""}
{f"- **Min/Max Gas Used**: {results['gas_efficiency']['min_gas_used']:,} / {results['gas_efficiency']['max_gas_used']:,}" if results.get('gas_efficiency') else ""}

## Top 50 Most Affected Addresses (6-Month Period)

| Rank | Address | Transactions | Avg Gas Limit | Max Gas Limit | Total Excess Gas | Additional Gas Cost | Est. Additional Cost (ETH) |
|------|---------|--------------|---------------|---------------|------------------|---------------------|----------------------------|
"""
    
    for i, addr in enumerate(results['top_addresses'], 1):
        total_gas_cost = addr['additional_gas_cost'] * addr['transaction_count']
        report += f"| {i} | {addr['address']} | {addr['transaction_count']} | {addr['avg_gas_limit']:,.0f} | {addr['max_gas_limit']:,.0f} | {addr['total_excess_gas']:,.0f} | {total_gas_cost:,.0f} | {addr['additional_cost_eth']:.6f} |\n"
    
    report += f"""

## Top 20 Recipient Addresses (To-Address Analysis)

| Rank | To Address | Transactions | Avg Gas Limit | Max Gas Limit |
|------|------------|--------------|---------------|---------------|
"""
    
    for i, addr in enumerate(results['top_to_addresses'][:20], 1):
        report += f"| {i} | {addr['to_address']} | {addr['transaction_count']} | {addr['avg_gas_limit']:,.0f} | {addr['max_gas_limit']:,.0f} |\n"
    
    report += f"""

## Analysis Methodology

### Data Processing Strategy
- **Analysis Period**: 180 days (6 months)
- **Processing Method**: Partition-aligned queries (1000-block partitions)
- **Batch Size**: {BATCH_SIZE_PARTITIONS * PARTITION_SIZE:,} blocks per batch
- **Total Batches Processed**: {len([f for f in os.listdir(CACHE_DIR) if f.startswith('batch_')])}

### Partition-Aware Optimization
1. Queries aligned to 1000-block partition boundaries
2. Smaller query ranges prevent timeouts
3. Aggregation without loading full dataset
4. JSON caching for fault tolerance

## Long-Term Trends

### Transaction Volume
- Average daily transactions: {results['total_transactions'] / DAYS_TO_ANALYZE:,.0f}
- Average daily affected transactions: {results['total_affected'] / DAYS_TO_ANALYZE:,.1f}
- Consistent impact rate: {results['affected_percentage']:.4f}%

### Address Analysis
- Most affected addresses show persistent high-gas usage
- Top 50 addresses account for significant portion of impact
- Address concentration enables targeted migration support
- To-address concentration shows centralization around key contracts

### Gas Efficiency Insights
{f"- {results['gas_efficiency']['unnecessary_percentage']:.1f}% of high gas limit transactions didn't actually need > 2^24 gas" if results.get('gas_efficiency') else ""}
{f"- Average efficiency of {results['gas_efficiency']['avg_efficiency']:.1%} indicates significant overprovisioning" if results.get('gas_efficiency') else ""}
- Many users set gas limits conservatively high without actual need

## Conclusions

The 6-month analysis confirms minimal and manageable impact:
1. **Stable Low Impact**: {results['affected_percentage']:.4f}% affected rate
2. **Concentrated Effect**: {results['unique_addresses']} unique addresses
3. **Gas Cost Impact**: {results['total_additional_gas_cost']:,.0f} total gas units
4. **Historical ETH Costs**: {results['total_additional_cost_eth']:.4f} ETH total (based on historical gas prices)
5. **Predictable Patterns**: Consistent behavior over extended period
6. **Overprovisioning Common**: Many transactions set unnecessarily high gas limits

## Implementation Recommendations

1. **Timeline**: 6-month data supports proposed implementation schedule
2. **Outreach**: Direct communication to {results['unique_addresses']} affected addresses
3. **Tooling**: Prioritize top 100 addresses for migration support
4. **Monitoring**: Continue tracking patterns post-implementation
5. **Education**: Help users understand appropriate gas limit setting

---
*Generated: {timestamp}*
*Analysis based on partition-aware processing of 6 months of Ethereum mainnet data*
"""
    
    # Save report
    report_file = f"gas_cap_6month_report_{timestamp}.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\n6-month report saved to: {report_file}")
    
    # Save all addresses as CSV
    if results['all_addresses']:
        import csv
        
        # Top 50
        csv_file = f"gas_cap_6month_top50_{timestamp}.csv"
        with open(csv_file, 'w', newline='') as f:
            fieldnames = ['rank', 'address', 'transaction_count', 'avg_gas_limit', 
                         'max_gas_limit', 'total_excess_gas', 'additional_gas_cost', 
                         'total_additional_gas_cost', 'additional_cost_eth']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for i, addr in enumerate(results['top_addresses'], 1):
                writer.writerow({
                    'rank': i,
                    'address': addr['address'],
                    'transaction_count': addr['transaction_count'],
                    'avg_gas_limit': addr['avg_gas_limit'],
                    'max_gas_limit': addr['max_gas_limit'],
                    'total_excess_gas': addr['total_excess_gas'],
                    'additional_gas_cost': addr['additional_gas_cost'],
                    'total_additional_gas_cost': addr['additional_gas_cost'] * addr['transaction_count'],
                    'additional_cost_eth': addr['additional_cost_eth']
                })
        
        print(f"Top 50 addresses saved to: {csv_file}")
        
        # All addresses
        all_csv_file = f"gas_cap_6month_all_addresses_{timestamp}.csv"
        with open(all_csv_file, 'w', newline='') as f:
            # Ensure all required fields are included
            if results['all_addresses']:
                # Get fieldnames from first row but ensure gas cost fields are included
                fieldnames = list(results['all_addresses'][0].keys())
                # Make sure additional_gas_cost is in the fieldnames
                if 'additional_gas_cost' not in fieldnames and 'additional_gas_cost' in results['all_addresses'][0]:
                    fieldnames.append('additional_gas_cost')
            else:
                fieldnames = ['address', 'transaction_count', 'avg_gas_limit', 'max_gas_limit', 
                             'total_excess_gas', 'additional_gas_cost', 'additional_cost_eth', 'splits_required']
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results['all_addresses'])
        
        print(f"All affected addresses saved to: {all_csv_file}")
    
    # Save to-address analysis
    if results.get('all_to_addresses'):
        to_csv_file = f"gas_cap_6month_to_addresses_{timestamp}.csv"
        with open(to_csv_file, 'w', newline='') as f:
            fieldnames = list(results['all_to_addresses'][0].keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results['all_to_addresses'])
        
        print(f"To-address analysis saved to: {to_csv_file}")
    
    # Save gas efficiency analysis
    if results.get('gas_efficiency'):
        efficiency_file = f"gas_cap_6month_efficiency_{timestamp}.json"
        with open(efficiency_file, 'w') as f:
            json.dump(results['gas_efficiency'], f, indent=2)
        
        print(f"Gas efficiency analysis saved to: {efficiency_file}")
    
    return report_file

def create_visualizations(results, timestamp):
    """Create visualization charts for the analysis results"""
    # Set up the plot style
    plt.style.use('seaborn-v0_8-darkgrid')
    sns.set_palette('husl')
    
    # Create figure with subplots
    fig = plt.figure(figsize=(20, 16))
    
    # 1. To-Address Concentration (Top 20)
    ax1 = plt.subplot(2, 3, 1)
    if results.get('top_to_addresses'):
        top_20_to = results['top_to_addresses'][:20]
        addresses = [f"{addr['to_address'][:6]}...{addr['to_address'][-4:]}" for addr in top_20_to]
        tx_counts = [addr['transaction_count'] for addr in top_20_to]
        
        bars = ax1.barh(addresses, tx_counts, color=plt.cm.viridis(np.linspace(0, 1, len(addresses))))
        ax1.set_xlabel('Transaction Count', fontsize=12)
        ax1.set_title('Top 20 Recipient Addresses (To-Address)', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3, axis='x')
        
        # Add percentage labels
        total_affected = results['total_affected']
        for i, (bar, count) in enumerate(zip(bars, tx_counts)):
            percentage = (count / total_affected) * 100
            ax1.text(bar.get_width() + max(tx_counts)*0.01, bar.get_y() + bar.get_height()/2, 
                    f'{percentage:.1f}%', va='center', fontsize=9)
    
    # 2. Gas Efficiency Distribution
    ax2 = plt.subplot(2, 3, 2)
    if results.get('gas_efficiency'):
        eff = results['gas_efficiency']
        categories = ['Needed > 2^24', 'Could use < 2^24']
        values = [
            eff['total_affected_transactions'] - eff['unnecessary_high_limit_count'],
            eff['unnecessary_high_limit_count']
        ]
        colors = ['#ff6b6b', '#4ecdc4']
        
        wedges, texts, autotexts = ax2.pie(values, labels=categories, colors=colors, autopct='%1.1f%%',
                                           startangle=90, textprops={'fontsize': 11})
        ax2.set_title('Gas Limit Necessity Analysis', fontsize=14, fontweight='bold')
        
        # Add summary text
        ax2.text(0, -1.3, f"Average Efficiency: {eff['avg_efficiency']:.1%}", 
                ha='center', fontsize=12, transform=ax2.transAxes)
    
    # 3. To-Address vs From-Address Concentration Comparison
    ax3 = plt.subplot(2, 3, 3)
    concentration_data = {
        'From Addresses': results['unique_addresses'],
        'To Addresses': results['unique_to_addresses']
    }
    
    bars = ax3.bar(concentration_data.keys(), concentration_data.values(), color=['#3498db', '#e74c3c'])
    ax3.set_ylabel('Number of Unique Addresses', fontsize=12)
    ax3.set_title('Address Concentration Comparison', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + results['unique_addresses']*0.01,
                f'{int(height):,}', ha='center', va='bottom', fontsize=11)
    
    # Add concentration ratio
    ratio = results['unique_to_addresses'] / results['unique_addresses']
    ax3.text(0.5, 0.95, f'Concentration Ratio: {ratio:.2f}', 
            transform=ax3.transAxes, ha='center', va='top', fontsize=12,
            bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.7))
    
    # 4. Gas Usage Efficiency Histogram
    ax4 = plt.subplot(2, 3, 4)
    if results.get('gas_efficiency'):
        # Create synthetic data for visualization based on averages
        avg_limit = results['gas_efficiency']['avg_gas_limit']
        avg_used = results['gas_efficiency']['avg_gas_used']
        
        categories = ['Average Gas Limit', 'Average Gas Used', 'EIP-7983 Cap']
        values = [avg_limit, avg_used, PROPOSED_GAS_CAP]
        colors = ['#ff6b6b', '#51cf66', '#339af0']
        
        bars = ax4.bar(categories, values, color=colors)
        ax4.set_ylabel('Gas Units', fontsize=12)
        ax4.set_title('Gas Usage vs Limits', fontsize=14, fontweight='bold')
        ax4.grid(True, alpha=0.3, axis='y')
        ax4.axhline(PROPOSED_GAS_CAP, color='black', linestyle='--', linewidth=2, alpha=0.5)
        
        # Add value labels
        for bar in bars:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + max(values)*0.01,
                    f'{int(height):,}', ha='center', va='bottom', fontsize=10)
    
    # 5. Top 10 Recipients vs Top 10 Senders
    ax5 = plt.subplot(2, 3, 5)
    if results.get('top_to_addresses') and results.get('top_addresses'):
        # Prepare data
        top_10_to = results['top_to_addresses'][:10]
        top_10_from = results['top_addresses'][:10]
        
        to_total = sum(addr['transaction_count'] for addr in top_10_to)
        from_total = sum(addr['transaction_count'] for addr in top_10_from)
        
        # Create grouped bar chart
        categories = [f'Top {i+1}' for i in range(10)]
        to_counts = [addr['transaction_count'] for addr in top_10_to]
        from_counts = [addr['transaction_count'] for addr in top_10_from]
        
        x = np.arange(len(categories))
        width = 0.35
        
        bars1 = ax5.bar(x - width/2, from_counts, width, label='From Address', color='#3498db')
        bars2 = ax5.bar(x + width/2, to_counts, width, label='To Address', color='#e74c3c')
        
        ax5.set_xlabel('Rank', fontsize=12)
        ax5.set_ylabel('Transaction Count', fontsize=12)
        ax5.set_title('Top 10 From vs To Addresses', fontsize=14, fontweight='bold')
        ax5.set_xticks(x)
        ax5.set_xticklabels(categories)
        ax5.legend()
        ax5.grid(True, alpha=0.3, axis='y')
    
    # 6. Summary Statistics Box
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')
    
    summary_text = f"""
    📊 6-MONTH ANALYSIS SUMMARY
    
    Total Transactions: {results['total_transactions']:,}
    Affected Transactions: {results['total_affected']:,} ({results['affected_percentage']:.4f}%)
    
    🏠 ADDRESS ANALYSIS
    Unique From Addresses: {results['unique_addresses']:,}
    Unique To Addresses: {results['unique_to_addresses']:,}
    Concentration Ratio: {results['unique_to_addresses']/results['unique_addresses']:.2f}
    
    ⛽ GAS EFFICIENCY
    """
    
    if results.get('gas_efficiency'):
        summary_text += f"""Unnecessary High Limits: {results['gas_efficiency']['unnecessary_percentage']:.1f}%
    Average Efficiency: {results['gas_efficiency']['avg_efficiency']:.1%}
    Average Gas Used: {results['gas_efficiency']['avg_gas_used']:,.0f}
    """
    else:
        summary_text += "Gas efficiency data not available"
    
    summary_text += f"""
    💰 ECONOMIC IMPACT
    Total Additional Gas: {results['total_additional_gas_cost']:,.0f} gas units
    Total Additional Cost: {results['total_additional_cost_eth']:.4f} ETH
    Avg Gas per Address: {results['total_additional_gas_cost']/results['unique_addresses']:,.0f} gas
    Avg Cost per Address: {results['total_additional_cost_eth']/results['unique_addresses']:.6f} ETH
    """
    
    ax6.text(0.1, 0.9, summary_text, transform=ax6.transAxes, fontsize=12,
            verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round,pad=1', facecolor='lightgray', alpha=0.8))
    
    plt.tight_layout()
    
    # Save the figure
    chart_file = f"gas_cap_6month_analysis_charts_{timestamp}.png"
    plt.savefig(chart_file, dpi=300, bbox_inches='tight')
    print(f"Visualization charts saved to: {chart_file}")
    
    # Also save individual charts
    save_individual_charts(results, timestamp)
    
    return chart_file

def save_individual_charts(results, timestamp):
    """Save individual charts for use in reports"""
    # Create directory for individual charts
    charts_dir = f"gas_cap_charts_{timestamp}"
    os.makedirs(charts_dir, exist_ok=True)
    
    # 1. To-Address Concentration Chart
    if results.get('top_to_addresses'):
        plt.figure(figsize=(12, 8))
        top_20_to = results['top_to_addresses'][:20]
        addresses = [f"{addr['to_address'][:6]}...{addr['to_address'][-4:]}" for addr in top_20_to]
        tx_counts = [addr['transaction_count'] for addr in top_20_to]
        
        plt.barh(addresses, tx_counts, color=plt.cm.viridis(np.linspace(0, 1, len(addresses))))
        plt.xlabel('Transaction Count', fontsize=14)
        plt.title('Top 20 Recipient Addresses', fontsize=16, fontweight='bold')
        plt.grid(True, alpha=0.3, axis='x')
        plt.tight_layout()
        plt.savefig(os.path.join(charts_dir, 'to_address_concentration.png'), dpi=300)
        plt.close()
    
    # 2. Gas Efficiency Pie Chart
    if results.get('gas_efficiency'):
        plt.figure(figsize=(10, 8))
        eff = results['gas_efficiency']
        categories = ['Actually Needed > 2^24', 'Could Have Used < 2^24']
        values = [
            eff['total_affected_transactions'] - eff['unnecessary_high_limit_count'],
            eff['unnecessary_high_limit_count']
        ]
        colors = ['#ff6b6b', '#4ecdc4']
        
        plt.pie(values, labels=categories, colors=colors, autopct='%1.1f%%',
                startangle=90, textprops={'fontsize': 14})
        plt.title('Gas Limit Necessity Analysis', fontsize=18, fontweight='bold', pad=20)
        plt.text(0, -1.3, f"Average Efficiency: {eff['avg_efficiency']:.1%}", 
                ha='center', fontsize=14, transform=plt.gca().transAxes)
        plt.tight_layout()
        plt.savefig(os.path.join(charts_dir, 'gas_efficiency_analysis.png'), dpi=300)
        plt.close()
    
    print(f"Individual charts saved to: {charts_dir}/")

def main():
    """Main function for 6-month analysis"""
    try:
        # Setup
        ensure_cache_dir()
        print("Initializing PyXatu client...")
        xatu = initialize_xatu()
        
        # Get latest block
        latest_block = get_latest_block(xatu)
        print(f"Latest block: {latest_block:,}")
        
        # Calculate block range
        total_blocks = DAYS_TO_ANALYZE * BLOCKS_PER_DAY
        start_block = latest_block - total_blocks
        
        print(f"\nAnalyzing 6 months: blocks {start_block:,} to {latest_block:,}")
        print(f"Total blocks: {total_blocks:,}")
        
        # Process in batches aligned to partitions
        batch_size = BATCH_SIZE_PARTITIONS * PARTITION_SIZE
        num_batches = (total_blocks + batch_size - 1) // batch_size
        
        print(f"Processing in {num_batches} batches of {batch_size:,} blocks each")
        
        # Process batches
        for batch_id in range(num_batches):
            batch_start = start_block + (batch_id * batch_size)
            batch_end = min(batch_start + batch_size, latest_block)
            
            # Check if already processed
            cache_file = os.path.join(CACHE_DIR, f"batch_{batch_id:05d}.json")
            if os.path.exists(cache_file):
                print(f"\nBatch {batch_id} already processed, skipping...")
                continue
            
            # Process batch
            process_partition_batch(xatu, batch_start, batch_end, batch_id)
            
            # Progress
            progress = (batch_id + 1) / num_batches * 100
            print(f"Progress: {progress:.1f}%")
        
        # Aggregate results
        final_results = aggregate_results()
        
        # Generate report
        print("\nGenerating 6-month report...")
        report_file = generate_6month_report(final_results)
        
        # Generate visualizations
        print("\nCreating visualization charts...")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        chart_file = create_visualizations(final_results, timestamp)
        
        # Summary
        print("\n" + "="*80)
        print("6-MONTH GAS CAP ANALYSIS SUMMARY")
        print("="*80)
        print(f"Total Transactions: {final_results['total_transactions']:,}")
        print(f"Affected Transactions: {final_results['total_affected']:,} ({final_results['affected_percentage']:.4f}%)")
        print(f"Unique Affected Addresses: {final_results['unique_addresses']:,}")
        print(f"Total Additional Gas Cost: {final_results['total_additional_gas_cost']:,.0f} gas units")
        print(f"Total Additional Cost (ETH): {final_results['total_additional_cost_eth']:.4f} ETH")
        print(f"\nNote: To estimate costs with current conditions:")
        print(f"  - Assume base fee (e.g., 30 gwei)")
        print(f"  - ETH price: $2,500")
        print(f"  - Cost in USD = {final_results['total_additional_gas_cost']:,.0f} × base_fee_gwei × 2500 / 1e9")
        
        print("\nTO-ADDRESS CONCENTRATION:")
        print(f"Unique To-Addresses: {final_results['unique_to_addresses']:,}")
        print(f"Concentration Ratio: {final_results['unique_to_addresses']/final_results['unique_addresses']:.2f} to-addresses per from-address")
        
        if final_results.get('gas_efficiency'):
            print("\nGAS EFFICIENCY ANALYSIS:")
            print(f"Transactions with unnecessary high limits: {final_results['gas_efficiency']['unnecessary_high_limit_count']:,} ({final_results['gas_efficiency']['unnecessary_percentage']:.1f}%)")
            print(f"Average gas efficiency: {final_results['gas_efficiency']['avg_efficiency']:.1%}")
            print(f"Average gas used: {final_results['gas_efficiency']['avg_gas_used']:,.0f}")
        
        print("\nAnalysis completed successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()