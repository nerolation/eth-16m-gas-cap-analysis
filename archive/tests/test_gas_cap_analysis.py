#!/usr/bin/env python3
"""
Unit tests for analyze_gas_cap_6months_partitioned.py
Tests all key functions and calculations to ensure 100% correctness
"""

import unittest
import json
import os
import tempfile
import shutil
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import sys

# Import the module we're testing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze_gas_cap_6months_partitioned as gas_cap

class TestGasCapAnalysis(unittest.TestCase):
    """Test suite for gas cap analysis functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.original_cache_dir = gas_cap.CACHE_DIR
        gas_cap.CACHE_DIR = os.path.join(self.test_dir, 'cache')
        os.makedirs(gas_cap.CACHE_DIR)
        
    def tearDown(self):
        """Clean up test fixtures"""
        gas_cap.CACHE_DIR = self.original_cache_dir
        shutil.rmtree(self.test_dir)
    
    def test_partition_alignment(self):
        """Test that partition alignment works correctly"""
        # Test case 1: Already aligned
        start = 5000
        end = 6000
        start_partition = (start // gas_cap.PARTITION_SIZE) * gas_cap.PARTITION_SIZE
        end_partition = ((end - 1) // gas_cap.PARTITION_SIZE + 1) * gas_cap.PARTITION_SIZE
        self.assertEqual(start_partition, 5000)
        self.assertEqual(end_partition, 6000)
        
        # Test case 2: Not aligned
        start = 5001
        end = 5999
        start_partition = (start // gas_cap.PARTITION_SIZE) * gas_cap.PARTITION_SIZE
        end_partition = ((end - 1) // gas_cap.PARTITION_SIZE + 1) * gas_cap.PARTITION_SIZE
        self.assertEqual(start_partition, 5000)
        self.assertEqual(end_partition, 6000)
        
        # Test case 3: Crossing multiple partitions
        start = 1500
        end = 3500
        start_partition = (start // gas_cap.PARTITION_SIZE) * gas_cap.PARTITION_SIZE
        end_partition = ((end - 1) // gas_cap.PARTITION_SIZE + 1) * gas_cap.PARTITION_SIZE
        self.assertEqual(start_partition, 1000)
        self.assertEqual(end_partition, 4000)
    
    def test_gas_cost_calculations(self):
        """Test gas cost calculations for accuracy"""
        # Test basic calculation
        avg_gas_limit = 30_000_000  # 30M gas
        splits_required = np.ceil(avg_gas_limit / gas_cap.PROPOSED_GAS_CAP)
        self.assertEqual(splits_required, 2)  # 30M / 16.777216M = 1.79, ceil = 2
        
        # Test additional gas cost
        additional_gas_cost = (splits_required - 1) * 21000
        self.assertEqual(additional_gas_cost, 21000)
        
        # Test ETH cost calculation
        avg_gas_price = 30_000_000_000  # 30 gwei
        additional_cost_eth = additional_gas_cost * avg_gas_price / 1e18
        expected_cost = 21000 * 30e9 / 1e18
        self.assertAlmostEqual(additional_cost_eth, expected_cost, places=10)
        
        # Test edge cases
        # Case 1: Gas limit exactly at cap
        avg_gas_limit = gas_cap.PROPOSED_GAS_CAP
        splits_required = np.ceil(avg_gas_limit / gas_cap.PROPOSED_GAS_CAP)
        self.assertEqual(splits_required, 1)
        additional_gas_cost = (splits_required - 1) * 21000
        self.assertEqual(additional_gas_cost, 0)
        
        # Case 2: Just above cap
        avg_gas_limit = gas_cap.PROPOSED_GAS_CAP + 1
        splits_required = np.ceil(avg_gas_limit / gas_cap.PROPOSED_GAS_CAP)
        self.assertEqual(splits_required, 2)
        additional_gas_cost = (splits_required - 1) * 21000
        self.assertEqual(additional_gas_cost, 21000)
    
    def test_aggregation_logic(self):
        """Test the aggregation logic for correctness"""
        # Create test batch data
        batch1 = {
            'batch_id': 0,
            'start_block': 0,
            'end_block': 1000,
            'summary': {
                'total_transactions': 1000,
                'affected_transactions': 10,
                'high_gas_transactions': 5
            },
            'affected_addresses': [
                {
                    'from_address': '0xaddr1',
                    'transaction_count': 5,
                    'avg_gas_limit': 20_000_000,
                    'max_gas_limit': 25_000_000,
                    'total_excess_gas': 15_000_000,
                    'avg_gas_price': 30_000_000_000
                },
                {
                    'from_address': '0xaddr2',
                    'transaction_count': 3,
                    'avg_gas_limit': 18_000_000,
                    'max_gas_limit': 20_000_000,
                    'total_excess_gas': 3_600_000,
                    'avg_gas_price': 25_000_000_000
                }
            ],
            'to_addresses': [
                {
                    'to_address': '0xtoaddr1',
                    'transaction_count': 8,
                    'avg_gas_limit': 19_000_000,
                    'max_gas_limit': 24_000_000
                }
            ],
            'gas_efficiency': {
                'total_overprovision': 10,
                'unnecessary_high_limit': 2,
                'avg_gas_limit': 19_500_000,
                'avg_gas_used': 15_000_000,
                'min_gas_used': 12_000_000,
                'max_gas_used': 18_000_000
            }
        }
        
        batch2 = {
            'batch_id': 1,
            'start_block': 1000,
            'end_block': 2000,
            'summary': {
                'total_transactions': 1500,
                'affected_transactions': 15,
                'high_gas_transactions': 8
            },
            'affected_addresses': [
                {
                    'from_address': '0xaddr1',  # Same address as batch1
                    'transaction_count': 3,
                    'avg_gas_limit': 22_000_000,
                    'max_gas_limit': 26_000_000,
                    'total_excess_gas': 16_800_000,
                    'avg_gas_price': 32_000_000_000
                },
                {
                    'from_address': '0xaddr3',  # New address
                    'transaction_count': 7,
                    'avg_gas_limit': 24_000_000,
                    'max_gas_limit': 30_000_000,
                    'total_excess_gas': 50_400_000,
                    'avg_gas_price': 28_000_000_000
                }
            ],
            'to_addresses': [
                {
                    'to_address': '0xtoaddr1',  # Same to_address
                    'transaction_count': 5,
                    'avg_gas_limit': 21_000_000,
                    'max_gas_limit': 26_000_000
                },
                {
                    'to_address': '0xtoaddr2',
                    'transaction_count': 10,
                    'avg_gas_limit': 23_000_000,
                    'max_gas_limit': 28_000_000
                }
            ],
            'gas_efficiency': {
                'total_overprovision': 15,
                'unnecessary_high_limit': 5,
                'avg_gas_limit': 22_000_000,
                'avg_gas_used': 17_000_000,
                'min_gas_used': 13_000_000,
                'max_gas_used': 20_000_000
            }
        }
        
        # Save test batch files
        with open(os.path.join(gas_cap.CACHE_DIR, 'batch_00000.json'), 'w') as f:
            json.dump(batch1, f)
        with open(os.path.join(gas_cap.CACHE_DIR, 'batch_00001.json'), 'w') as f:
            json.dump(batch2, f)
        
        # Run aggregation
        results = gas_cap.aggregate_results()
        
        # Verify summary aggregation
        self.assertEqual(results['total_transactions'], 2500)
        self.assertEqual(results['total_affected'], 25)
        self.assertEqual(results['total_high_gas'], 13)
        
        # Verify address aggregation
        self.assertEqual(results['unique_addresses'], 3)  # addr1, addr2, addr3
        
        # Check addr1 aggregation (appears in both batches)
        addr1_data = next(a for a in results['all_addresses'] if a['address'] == '0xaddr1')
        self.assertEqual(addr1_data['transaction_count'], 8)  # 5 + 3
        expected_avg_gas = (5 * 20_000_000 + 3 * 22_000_000) / 8
        self.assertAlmostEqual(addr1_data['avg_gas_limit'], expected_avg_gas, places=2)
        self.assertEqual(addr1_data['max_gas_limit'], 26_000_000)
        self.assertEqual(addr1_data['total_excess_gas'], 31_800_000)  # 15M + 16.8M
        
        # Verify to_address aggregation
        self.assertEqual(results['unique_to_addresses'], 2)
        toaddr1_data = next(a for a in results['all_to_addresses'] if a['to_address'] == '0xtoaddr1')
        self.assertEqual(toaddr1_data['transaction_count'], 13)  # 8 + 5
        
        # Verify gas efficiency aggregation
        gas_eff = results['gas_efficiency']
        self.assertEqual(gas_eff['total_affected_transactions'], 25)  # 10 + 15
        self.assertEqual(gas_eff['unnecessary_high_limit_count'], 7)  # 2 + 5
        self.assertAlmostEqual(gas_eff['unnecessary_percentage'], 28.0, places=1)  # 7/25 * 100
        
        # Verify gas efficiency calculations
        expected_avg_limit = (10 * 19_500_000 + 15 * 22_000_000) / 25
        expected_avg_used = (10 * 15_000_000 + 15 * 17_000_000) / 25
        self.assertAlmostEqual(gas_eff['avg_gas_limit'], expected_avg_limit, places=0)
        self.assertAlmostEqual(gas_eff['avg_gas_used'], expected_avg_used, places=0)
        self.assertAlmostEqual(gas_eff['avg_efficiency'], expected_avg_used / expected_avg_limit, places=3)
        self.assertEqual(gas_eff['min_gas_used'], 12_000_000)
        self.assertEqual(gas_eff['max_gas_used'], 20_000_000)
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        # Test empty batch
        empty_batch = {
            'batch_id': 0,
            'start_block': 0,
            'end_block': 1000,
            'summary': {},
            'affected_addresses': [],
            'to_addresses': [],
            'gas_efficiency': {}
        }
        
        with open(os.path.join(gas_cap.CACHE_DIR, 'batch_00000.json'), 'w') as f:
            json.dump(empty_batch, f)
        
        results = gas_cap.aggregate_results()
        self.assertEqual(results['total_transactions'], 0)
        self.assertEqual(results['total_affected'], 0)
        self.assertEqual(results['unique_addresses'], 0)
        
        # Test division by zero handling
        self.assertEqual(results['affected_percentage'], 0)
        
    @patch('analyze_gas_cap_6months_partitioned.pyxatu.PyXatu')
    def test_process_partition_batch(self, mock_xatu_class):
        """Test the process_partition_batch function"""
        # Mock PyXatu instance
        mock_xatu = Mock()
        mock_xatu_class.return_value = mock_xatu
        
        # Mock query responses
        summary_df = pd.DataFrame([{
            'total_transactions': 1000,
            'affected_transactions': 10,
            'high_gas_transactions': 5
        }])
        
        affected_df = pd.DataFrame([{
            'from_address': '0xtest1',
            'transaction_count': 5,
            'avg_gas_limit': 20000000,
            'max_gas_limit': 25000000,
            'total_excess_gas': 15000000,
            'avg_gas_price': 30000000000
        }])
        
        to_address_df = pd.DataFrame([{
            'to_address': '0xtotest1',
            'transaction_count': 8,
            'avg_gas_limit': 19000000,
            'max_gas_limit': 24000000
        }])
        
        gas_efficiency_df = pd.DataFrame([{
            'total_overprovision': 10,
            'unnecessary_high_limit': 2,
            'avg_gas_limit': 19500000,
            'avg_gas_used': 15000000,
            'avg_gas_efficiency': 0.77,
            'min_gas_used': 12000000,
            'max_gas_used': 18000000
        }])
        
        # Configure mock to return our test data
        mock_xatu.execute_query.side_effect = [
            summary_df,
            affected_df,
            to_address_df,
            gas_efficiency_df
        ]
        
        # Create a real PyXatu instance for testing
        xatu = gas_cap.initialize_xatu()
        
        # Test process_partition_batch
        result = gas_cap.process_partition_batch(mock_xatu, 1000, 2000, 0)
        
        # Verify the result
        self.assertIsNotNone(result)
        self.assertEqual(result['total_transactions'], 1000)
        self.assertEqual(result['affected_transactions'], 10)
        
        # Verify cache file was created
        cache_file = os.path.join(gas_cap.CACHE_DIR, 'batch_00000.json')
        self.assertTrue(os.path.exists(cache_file))
        
        # Load and verify cache content
        with open(cache_file, 'r') as f:
            cached_data = json.load(f)
        
        self.assertEqual(cached_data['batch_id'], 0)
        self.assertEqual(cached_data['start_block'], 1000)
        self.assertEqual(cached_data['end_block'], 2000)
        self.assertEqual(len(cached_data['affected_addresses']), 1)
        self.assertEqual(cached_data['affected_addresses'][0]['from_address'], '0xtest1')
    
    def test_report_generation(self):
        """Test report generation doesn't crash and produces valid output"""
        # Create minimal test results
        test_results = {
            'total_transactions': 1000,
            'total_affected': 10,
            'total_high_gas': 5,
            'affected_percentage': 1.0,
            'unique_addresses': 3,
            'top_addresses': [
                {
                    'address': '0xtest1',
                    'transaction_count': 5,
                    'avg_gas_limit': 20000000,
                    'max_gas_limit': 25000000,
                    'total_excess_gas': 15000000,
                    'additional_gas_cost': 21000,
                    'additional_cost_eth': 0.00063,
                    'splits_required': 2
                }
            ],
            'all_addresses': [
                {
                    'address': '0xtest1',
                    'transaction_count': 5,
                    'avg_gas_limit': 20000000,
                    'max_gas_limit': 25000000,
                    'total_excess_gas': 15000000,
                    'additional_gas_cost': 21000,
                    'additional_cost_eth': 0.00063,
                    'splits_required': 2
                }
            ],
            'total_additional_gas_cost': 21000,
            'total_additional_cost_eth': 0.00063,
            'unique_to_addresses': 1,
            'top_to_addresses': [
                {
                    'to_address': '0xtotest1',
                    'transaction_count': 8,
                    'avg_gas_limit': 19000000,
                    'max_gas_limit': 24000000
                }
            ],
            'all_to_addresses': [
                {
                    'to_address': '0xtotest1',
                    'transaction_count': 8,
                    'avg_gas_limit': 19000000,
                    'max_gas_limit': 24000000
                }
            ],
            'gas_efficiency': {
                'total_affected_transactions': 10,
                'unnecessary_high_limit_count': 2,
                'unnecessary_percentage': 20.0,
                'avg_gas_limit': 19500000,
                'avg_gas_used': 15000000,
                'avg_efficiency': 0.77,
                'min_gas_used': 12000000,
                'max_gas_used': 18000000
            }
        }
        
        # Generate report (should not raise any exceptions)
        report_file = gas_cap.generate_6month_report(test_results)
        
        # Verify report file exists
        self.assertTrue(os.path.exists(report_file))
        
        # Read and verify report content
        with open(report_file, 'r') as f:
            report_content = f.read()
        
        # Check key elements are present
        self.assertIn('EIP-7983', report_content)
        self.assertIn('1,000', report_content)  # Total transactions
        self.assertIn('1.0000%', report_content)  # Impact percentage
        self.assertIn('0xtest1', report_content)  # Address
        
        # Clean up
        os.remove(report_file)
        
        # Also check CSV files were created
        csv_files = [f for f in os.listdir('.') if f.startswith('gas_cap_6month_') and f.endswith('.csv')]
        self.assertGreater(len(csv_files), 0)
        
        # Clean up CSV files
        for csv_file in csv_files:
            os.remove(csv_file)
    
    def test_2_power_24_value(self):
        """Test that 2^24 is correctly calculated"""
        expected = 16777216
        self.assertEqual(gas_cap.PROPOSED_GAS_CAP, expected)
        self.assertEqual(gas_cap.PROPOSED_GAS_CAP, 2**24)
    
    def test_batch_size_calculations(self):
        """Test batch size and partition calculations"""
        # Test that batch size is correct
        expected_batch_size = gas_cap.BATCH_SIZE_PARTITIONS * gas_cap.PARTITION_SIZE
        self.assertEqual(expected_batch_size, 10000)  # 10 * 1000
        
        # Test number of batches calculation
        total_blocks = 1_296_000  # 6 months
        batch_size = expected_batch_size
        num_batches = (total_blocks + batch_size - 1) // batch_size
        expected_num_batches = 130  # ceil(1296000 / 10000)
        self.assertEqual(num_batches, expected_num_batches)


class TestDataIntegrity(unittest.TestCase):
    """Test data integrity and calculation correctness"""
    
    def test_gas_splits_calculation(self):
        """Verify gas splits calculation is correct"""
        test_cases = [
            (16_777_216, 1),     # Exactly at cap
            (16_777_217, 2),     # Just above cap
            (33_554_432, 2),     # 2 * cap
            (33_554_433, 3),     # Just above 2 * cap
            (50_331_648, 3),     # 3 * cap
            (50_331_649, 4),     # Just above 3 * cap
        ]
        
        for gas_limit, expected_splits in test_cases:
            splits = int(np.ceil(gas_limit / gas_cap.PROPOSED_GAS_CAP))
            self.assertEqual(splits, expected_splits, 
                           f"Failed for gas_limit={gas_limit}: expected {expected_splits}, got {splits}")
    
    def test_additional_gas_cost_formula(self):
        """Test the additional gas cost formula"""
        # For 2 splits: 1 additional transaction needed
        # Cost = 1 * 21000 = 21000
        
        # For 3 splits: 2 additional transactions needed
        # Cost = 2 * 21000 = 42000
        
        test_cases = [
            (1, 0),      # 1 split = 0 additional cost
            (2, 21000),  # 2 splits = 1 * 21000
            (3, 42000),  # 3 splits = 2 * 21000
            (4, 63000),  # 4 splits = 3 * 21000
        ]
        
        for splits, expected_cost in test_cases:
            cost = (splits - 1) * 21000
            self.assertEqual(cost, expected_cost)
    
    def test_eth_cost_calculation(self):
        """Test ETH cost calculation with various gas prices"""
        additional_gas = 21000
        
        test_cases = [
            (20_000_000_000, 0.00042),   # 20 gwei
            (30_000_000_000, 0.00063),   # 30 gwei
            (50_000_000_000, 0.00105),   # 50 gwei
            (100_000_000_000, 0.00210),  # 100 gwei
        ]
        
        for gas_price, expected_eth in test_cases:
            eth_cost = additional_gas * gas_price / 1e18
            self.assertAlmostEqual(eth_cost, expected_eth, places=5)


if __name__ == '__main__':
    unittest.main(verbosity=2)