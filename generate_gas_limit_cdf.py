#!/usr/bin/env python3
"""
Generate Gas Limit CDF Data

Creates cumulative distribution function data for all transaction gas limits.
"""

import pandas as pd
import pyxatu
import numpy as np
import json
import os
import argparse
from datetime import datetime

# Configuration
PROPOSED_GAS_CAP = 16_777_216  # 2^24
BLOCKS_PER_DAY = 7200
DAYS_TO_ANALYZE = 30*6 + 3
PARTITION_SIZE = 1000
BATCH_SIZE_PARTITIONS = 20

# Parse command line arguments
parser = argparse.ArgumentParser(description='Generate gas limit CDF data')
parser.add_argument('-o', '--output', type=str, default='outputs', 
                    help='Output directory (default: outputs)')
args = parser.parse_args()

OUTPUT_DIR = args.output
CACHE_DIR = os.path.join(OUTPUT_DIR, "cdf_analysis/cache")

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
    
    return 22678052

def process_gas_distribution_batch(xatu, start_block, end_block, batch_id):
    """Process a batch to get gas limit distribution"""
    start_partition = (start_block // PARTITION_SIZE) * PARTITION_SIZE
    end_partition = ((end_block - 1) // PARTITION_SIZE + 1) * PARTITION_SIZE
    
    print(f"\nProcessing batch {batch_id}: blocks {start_partition:,} to {end_partition:,}")
    
    # Query for gas limit distribution
    distribution_query = f"""
    SELECT 
        CASE 
            WHEN gas_limit <= 21000 THEN 21000
            WHEN gas_limit <= 50000 THEN 50000
            WHEN gas_limit <= 100000 THEN 100000
            WHEN gas_limit <= 200000 THEN 200000
            WHEN gas_limit <= 500000 THEN 500000
            WHEN gas_limit <= 1000000 THEN 1000000
            WHEN gas_limit <= 2000000 THEN 2000000
            WHEN gas_limit <= 5000000 THEN 5000000
            WHEN gas_limit <= 10000000 THEN 10000000
            WHEN gas_limit <= 16777216 THEN 16777216
            WHEN gas_limit <= 20000000 THEN 20000000
            WHEN gas_limit <= 30000000 THEN 30000000
            ELSE 30000001
        END as gas_bucket,
        COUNT(*) as transaction_count,
        MIN(gas_limit) as min_gas,
        MAX(gas_limit) as max_gas,
        AVG(gas_limit) as avg_gas
    FROM canonical_execution_transaction
    WHERE block_number >= {start_partition}
    AND block_number < {end_partition}
    AND meta_network_name = 'mainnet'
    AND gas_limit IS NOT NULL
    GROUP BY gas_bucket
    ORDER BY gas_bucket
    """
    
    try:
        result = xatu.execute_query(
            distribution_query,
            columns="gas_bucket,transaction_count,min_gas,max_gas,avg_gas"
        )
        
        if result is not None and not result.empty:
            print(f"  Found {len(result)} gas buckets with {result['transaction_count'].sum():,} transactions")
            
            # Save to cache
            cache_file = os.path.join(CACHE_DIR, f"batch_{batch_id:05d}.json")
            result_dict = result.to_dict('records')
            
            with open(cache_file, 'w') as f:
                json.dump({
                    'batch_id': batch_id,
                    'start_block': start_partition,
                    'end_block': end_partition,
                    'distribution': result_dict
                }, f)
            
            return result
        else:
            print(f"  No data for batch {batch_id}")
            return None
            
    except Exception as e:
        print(f"  Error getting distribution: {e}")
        return None

def aggregate_distributions():
    """Aggregate all batch distributions"""
    print("\nAggregating distribution data...")
    
    # Initialize buckets
    bucket_totals = {}
    
    # Process each batch file
    batch_files = sorted([f for f in os.listdir(CACHE_DIR) if f.startswith('batch_')])
    print(f"Found {len(batch_files)} batch files to aggregate")
    
    for batch_file in batch_files:
        with open(os.path.join(CACHE_DIR, batch_file), 'r') as f:
            batch_data = json.load(f)
        
        for item in batch_data.get('distribution', []):
            bucket = item['gas_bucket']
            if bucket not in bucket_totals:
                bucket_totals[bucket] = {
                    'count': 0,
                    'min_gas': float('inf'),
                    'max_gas': 0,
                    'sum_gas': 0
                }
            
            bucket_totals[bucket]['count'] += item['transaction_count']
            bucket_totals[bucket]['min_gas'] = min(bucket_totals[bucket]['min_gas'], item['min_gas'])
            bucket_totals[bucket]['max_gas'] = max(bucket_totals[bucket]['max_gas'], item['max_gas'])
            bucket_totals[bucket]['sum_gas'] += item['avg_gas'] * item['transaction_count']
    
    # Convert to sorted list
    distribution_data = []
    for bucket, data in sorted(bucket_totals.items()):
        distribution_data.append({
            'gas_limit': bucket,
            'transaction_count': data['count'],
            'min_gas': data['min_gas'],
            'max_gas': data['max_gas'],
            'avg_gas': data['sum_gas'] / data['count'] if data['count'] > 0 else 0
        })
    
    return distribution_data

def calculate_cdf(distribution_data):
    """Calculate CDF from distribution data"""
    # Sort by gas limit
    sorted_data = sorted(distribution_data, key=lambda x: x['gas_limit'])
    
    # Calculate cumulative counts
    total_transactions = sum(item['transaction_count'] for item in sorted_data)
    cumulative_count = 0
    cdf_data = []
    
    for item in sorted_data:
        cumulative_count += item['transaction_count']
        cdf_data.append({
            'gas_limit': item['gas_limit'],
            'transaction_count': item['transaction_count'],
            'cumulative_count': cumulative_count,
            'cumulative_percentage': (cumulative_count / total_transactions) * 100,
            'min_gas': item['min_gas'],
            'max_gas': item['max_gas'],
            'avg_gas': item['avg_gas']
        })
    
    # Find where cap intersects
    cap_percentage = None
    for i, item in enumerate(cdf_data):
        if item['gas_limit'] >= PROPOSED_GAS_CAP:
            if i > 0:
                # Interpolate
                prev = cdf_data[i-1]
                curr = item
                
                # Linear interpolation
                gas_range = curr['gas_limit'] - prev['gas_limit']
                pct_range = curr['cumulative_percentage'] - prev['cumulative_percentage']
                gas_offset = PROPOSED_GAS_CAP - prev['gas_limit']
                
                cap_percentage = prev['cumulative_percentage'] + (gas_offset / gas_range) * pct_range
            else:
                cap_percentage = item['cumulative_percentage']
            break
    
    return cdf_data, cap_percentage, total_transactions

def save_cdf_data(cdf_data, cap_percentage, total_transactions):
    """Save CDF data to file"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Ensure output directory exists
    os.makedirs(os.path.join(OUTPUT_DIR, 'cdf_analysis/data'), exist_ok=True)
    
    # Save detailed CDF data
    cdf_file = os.path.join(OUTPUT_DIR, f"cdf_analysis/data/gas_limit_cdf_{timestamp}.json")
    with open(cdf_file, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'total_transactions': total_transactions,
            'cap_percentage': cap_percentage,
            'proposed_cap': PROPOSED_GAS_CAP,
            'cdf_data': cdf_data
        }, f, indent=2)
    
    print(f"\nCDF data saved to: {cdf_file}")
    
    # Save summary
    summary = f"""Gas Limit CDF Analysis Summary
================================
Generated: {timestamp}
Total Transactions: {total_transactions:,}
Proposed Cap: {PROPOSED_GAS_CAP:,} ({PROPOSED_GAS_CAP/1e6:.2f}M)

Key Findings:
- {cap_percentage:.2f}% of transactions have gas limit ≤ {PROPOSED_GAS_CAP:,}
- {100 - cap_percentage:.2f}% of transactions would be affected by the cap

Distribution Breakdown:
"""
    
    for item in cdf_data:
        if item['transaction_count'] > 0:
            summary += f"- Gas ≤ {item['gas_limit']:,}: {item['cumulative_percentage']:.2f}% ({item['transaction_count']:,} txs)\n"
    
    summary_file = os.path.join(OUTPUT_DIR, f"cdf_analysis/data/gas_limit_cdf_summary_{timestamp}.txt")
    with open(summary_file, 'w') as f:
        f.write(summary)
    
    print(f"Summary saved to: {summary_file}")
    
    return cdf_file

def main():
    """Main function"""
    try:
        ensure_cache_dir()
        print("Initializing PyXatu client...")
        xatu = initialize_xatu()
        
        # Get latest block
        latest_block = get_latest_block(xatu)
        print(f"Latest block: {latest_block:,}")
        
        # Calculate block range
        total_blocks = DAYS_TO_ANALYZE * BLOCKS_PER_DAY
        start_block = latest_block - total_blocks
        
        print(f"\nAnalyzing {DAYS_TO_ANALYZE} days: blocks {start_block:,} to {latest_block:,}")
        print(f"Total blocks: {total_blocks:,}")
        
        # Process in batches
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
            process_gas_distribution_batch(xatu, batch_start, batch_end, batch_id)
            
            # Progress
            progress = (batch_id + 1) / num_batches * 100
            print(f"Progress: {progress:.1f}%")
        
        # Aggregate results
        distribution_data = aggregate_distributions()
        
        # Calculate CDF
        print("\nCalculating CDF...")
        cdf_data, cap_percentage, total_transactions = calculate_cdf(distribution_data)
        
        # Save results
        cdf_file = save_cdf_data(cdf_data, cap_percentage, total_transactions)
        
        # Summary
        print("\n" + "="*60)
        print("GAS LIMIT CDF ANALYSIS COMPLETE")
        print("="*60)
        print(f"Total Transactions Analyzed: {total_transactions:,}")
        print(f"Proposed Cap: {PROPOSED_GAS_CAP:,} ({PROPOSED_GAS_CAP/1e6:.2f}M gas)")
        print(f"\nKey Finding:")
        print(f"  {cap_percentage:.2f}% of transactions have gas limit ≤ {PROPOSED_GAS_CAP:,}")
        print(f"  {100 - cap_percentage:.2f}% of transactions would be affected")
        
        print("\nAnalysis completed successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()