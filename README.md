# Ethereum 16M Gas Cap Analysis

This repository contains a comprehensive empirical analysis of EIP-7983, which proposes capping transaction gas limits at 16,777,216 (2^24) gas units.

## Overview

The analysis examines 6 months of Ethereum mainnet transaction data to understand the potential impact of implementing a gas limit cap. The key finding is that the proposed cap would affect only 0.0384% of all transactions, with minimal economic impact on users.

## Repository Contents

### Analysis Scripts
- `analyze_gas_cap_6months_partitioned.py` - Main analysis script that processes 6 months of blockchain data using partition-aware queries
- `eip_7983_comprehensive_analysis.ipynb` - Jupyter notebook with detailed analysis, visualizations, and insights

### Data Files
- `gas_cap_6month_all_addresses_*.csv` - Complete list of affected addresses with impact metrics
- `gas_cap_6month_top50_*.csv` - Top 50 most affected addresses
- `gas_cap_6month_to_addresses_*.csv` - Analysis of transaction recipients
- `gas_cap_6month_efficiency_*.json` - Gas usage efficiency statistics

### Reports
- `gas_cap_6month_report_*.md` - Comprehensive markdown report with executive summary and detailed findings

## Key Findings

- **Total Transactions Analyzed**: 251,922,669
- **Affected Transactions**: 96,577 (0.0384%)
- **Unique Affected Addresses**: 4,601
- **Average Gas Efficiency**: 71.4%
- **Economic Impact**: Minimal, with average additional cost of 0.000488 ETH per affected address

## Usage

### Running the Analysis

```bash
python analyze_gas_cap_6months_partitioned.py
```

### Exploring the Results

Open the Jupyter notebook to explore the analysis interactively:

```bash
jupyter notebook eip_7983_comprehensive_analysis.ipynb
```

## Requirements

- Python 3.8+
- pandas
- numpy
- matplotlib
- seaborn
- pyxatu (for blockchain data access)

## License

This analysis is provided for research and educational purposes.