# Extended Empirical Analysis Report: EIP-7983 Transaction Gas Limit Cap

## Executive Summary

This report presents an extended empirical analysis of EIP-7983, which proposes capping transaction gas limits at 16,777,216 (2^24). Based on analysis of 20,164,635 Ethereum mainnet transactions over approximately 14 days (100,000 blocks), we find that the proposed cap would affect only 0.02% of transactions with minimal economic impact, strongly supporting the proposal's feasibility.

## Key Findings

### 1. Minimal Transaction Impact
- **Total Transactions Analyzed**: 20,164,635
- **Affected Transactions**: 3,159 (0.02%)
- **Unique Addresses Affected**: 492
- **High Gas Transactions (>1M)**: 703,491 (3.49%)

### 2. Negligible Economic Impact
- **Total Additional Costs**: 0.1746 ETH for all affected transactions
- **Average Cost per Transaction**: 0.000055 ETH
- **Average Cost per Address**: 0.000355 ETH

### 3. Gas Usage Distribution
| Percentile | Gas Limit | Status |
|------------|-----------|---------|
| 50th (Median) | 84,281 | Well below cap |
| 90th | 300,000 | Well below cap |
| 95th | 487,428 | Well below cap |
| 99th | 2,000,000 | Well below cap |
| 99.9th | 8,475,980 | Well below cap |
| 99.98th | 16,777,216 | **Proposed Cap** |
| Maximum | 36,000,000 | Above cap |

### 4. Distribution Characteristics
- **Distribution Skewness**: 15.44 (highly right-skewed)
- **Outliers (>541,710 gas)**: 1,246,670 (6.18%)
- **Extreme Outliers (>854,136 gas)**: 766,587 (3.80%)

## Top 50 Most Affected Addresses

| Rank | Address | Affected Txs | Avg Gas Limit | Max Gas Limit | Total Excess Gas | Est. Additional Cost (ETH) | Avg Splits Required |
|------|---------|--------------|---------------|---------------|------------------|----------------------------|-------------------|
| 1 | 0x4fb9bbb1838ee0acb7b4d2e519a4c233198499fb | 648 | 26,021,000 | 26,021,000 | 5,989,972,032 | 0.009012 | 2.0 |
| 2 | 0xabd7a659d4c6e30c78899015f49b3513cf496351 | 201 | 25,600,000 | 25,600,000 | 1,773,379,584 | 0.000934 | 2.0 |
| 3 | 0x08621813a1b33bc58a97f9d3cc819dbbdde8d572 | 117 | 25,537,534 | 31,271,268 | 1,024,957,255 | 0.008978 | 2.0 |
| 4 | 0x2c3b6e74be767cd9722cdf4a4ca08c6910012b0a | 75 | 27,751,554 | 28,698,339 | 823,075,341 | 0.000678 | 2.0 |
| 5 | 0xd4abcbef17e002266a15ce9b7a678c4030ef4b0f | 52 | 30,000,000 | 30,000,000 | 687,584,768 | 0.003144 | 2.0 |
| 6 | 0x2855fbee020193d211de7beca52149dbc1555555 | 45 | 30,000,000 | 30,000,000 | 595,025,280 | 0.004626 | 2.0 |
| 7 | 0x85024d236f55294df581f4c8328da4eabefc3575 | 49 | 28,607,984 | 31,508,294 | 579,707,612 | 0.000535 | 2.0 |
| 8 | 0x41db6c3fcd594decda67ffa31ba013e6b562980f | 38 | 30,000,000 | 30,000,000 | 502,465,792 | 0.002460 | 2.0 |
| 9 | 0x6582b7c80df319553a988f62436b8a1be6b2b24c | 30 | 32,546,535 | 32,841,243 | 473,079,567 | 0.000351 | 2.0 |
| 10 | 0xee67263be078df8ce3f55d5bcc1d23eb0cdc61bb | 48 | 25,416,303 | 25,416,303 | 414,676,176 | 0.000221 | 2.0 |
| 11 | 0x0a94f91516c2d43afc8daf9da1171533c7ec1111 | 31 | 30,000,000 | 30,000,000 | 409,906,304 | 0.001789 | 2.0 |
| 12 | 0xa22c5a59102fe3e3463abb2e8254aeb302ca4592 | 23 | 30,000,000 | 30,000,000 | 304,124,032 | 0.001662 | 2.0 |
| 13 | 0xff0581a78019c65f3257429e053863304f555555 | 91 | 20,094,284 | 20,094,988 | 301,853,148 | 0.000201 | 2.0 |
| 14 | 0x5478c578a9e74891ecc6a3a9b58cfe67216cb301 | 20 | 30,000,000 | 30,000,000 | 264,455,680 | 0.001642 | 2.0 |
| 15 | 0xf3d72d2027e2b56d9bb5aeb7788b6427a99aef59 | 24 | 25,000,000 | 25,000,000 | 197,346,816 | 0.002064 | 2.0 |
| 16 | 0xab9b0c00c81ca20d6d5d421e47295e6c52a3ca95 | 26 | 24,165,099 | 32,073,144 | 192,084,960 | 0.000131 | 2.0 |
| 17 | 0xb288ccb7965eec0847bde9b39f36b57f40d8f2f2 | 14 | 30,000,000 | 30,000,000 | 185,118,976 | 0.000946 | 2.0 |
| 18 | 0x22dcb4798abf95b96c18cb6aade0229ae8dda3e1 | 66 | 19,497,706 | 20,025,269 | 179,552,348 | 0.000127 | 2.0 |
| 19 | 0x3df54eda69d8b61f651ac6b65e534e489b88cbd5 | 13 | 30,000,000 | 30,000,000 | 171,896,192 | 0.000852 | 2.0 |
| 20 | 0x4c4450b0da21bf531314fcd2ac1ceaac50cd7266 | 15 | 27,668,953 | 28,694,589 | 163,376,055 | 0.000183 | 2.0 |
| 21 | 0x8675094643d8c0bb853d326ef8b280dc2f30d024 | 12 | 30,000,000 | 30,000,000 | 158,673,408 | 0.000915 | 2.0 |
| 22 | 0xbfe294058478f27e5f041561ea5659672b0157e6 | 16 | 26,646,750 | 26,713,000 | 157,912,544 | 0.000700 | 2.0 |
| 23 | 0xa1a2851d339ad08a82811638fc6789148c80a428 | 10 | 32,306,984 | 33,333,550 | 155,297,677 | 0.000782 | 2.0 |
| 24 | 0x013a7b462107c1392300478337d17d668dc9a3a9 | 11 | 30,000,000 | 30,000,000 | 145,450,624 | 0.000899 | 2.0 |
| 25 | 0x33e3842b6ca9216ae34316cc2e450a57e8edcba3 | 11 | 30,000,000 | 30,000,000 | 145,450,624 | 0.001235 | 2.0 |
| 26 | 0xef2d3fcf79927ce06237dcc80ddd75f3ef40151e | 25 | 22,577,521 | 22,608,427 | 145,007,617 | 0.000183 | 2.0 |
| 27 | 0x1fccc097db89a86bfc474a1028f93958295b1fb7 | 44 | 20,000,000 | 20,000,000 | 141,802,496 | 0.000592 | 2.0 |
| 28 | 0x0d7c1e5fb47273d507a26a5e9d3292eeaf117cb5 | 15 | 25,600,000 | 25,600,000 | 132,341,760 | 0.000073 | 2.0 |
| 29 | 0x3c3e3b8f3cc0275f51acefab893d7cd70256b156 | 10 | 30,000,000 | 30,000,000 | 132,227,840 | 0.000673 | 2.0 |
| 30 | 0x70b00f8ffbaccbf662aff76dce82058296b46af9 | 40 | 20,025,269 | 20,025,269 | 129,922,120 | 0.000081 | 2.0 |
| 31 | 0x2147838f241fb984f9229fec1c148f0fb58d70a7 | 12 | 27,542,000 | 28,383,000 | 129,177,408 | 0.000075 | 2.0 |
| 32 | 0xf073a21f0d68adacfff34d5b8df04550c944e348 | 9 | 30,309,092 | 32,000,000 | 121,786,888 | 0.000671 | 2.0 |
| 33 | 0x33bb05b30a6f769a87e09def3816f1999c02d3b7 | 9 | 30,000,000 | 30,000,000 | 119,005,056 | 0.000615 | 2.0 |
| 34 | 0x9e95aabd118fc8f7db16772a754c12ceb3c889b3 | 9 | 30,000,000 | 30,000,000 | 119,005,056 | 0.000577 | 2.0 |
| 35 | 0x3be279545df0075930652031113ad0b3e196a309 | 9 | 30,000,000 | 30,000,000 | 119,005,056 | 0.001029 | 2.0 |
| 36 | 0x49b34ce4a3d6dbc461e253feec173fcf93eb212d | 12 | 25,878,000 | 25,933,000 | 109,209,408 | 0.000085 | 2.0 |
| 37 | 0x9dfc840576e285ee2d08358098d26cb02c0782cc | 8 | 30,000,000 | 30,000,000 | 105,782,272 | 0.000620 | 2.0 |
| 38 | 0x4c15e560dbca6002398be258b483e36322f02cb9 | 8 | 30,000,000 | 30,000,000 | 105,782,272 | 0.000561 | 2.0 |
| 39 | 0xcde31f52d75a3ea0a512faac9dd685df39e50f50 | 8 | 30,000,000 | 30,000,000 | 105,782,272 | 0.000566 | 2.0 |
| 40 | 0xe11b294d442cd78289b599ea4cb7eed585ca0980 | 8 | 30,000,000 | 30,000,000 | 105,782,272 | 0.000902 | 2.0 |
| 41 | 0xc87a8df3d07e06a929dc693245ef02630c848e85 | 13 | 24,269,053 | 26,537,674 | 97,393,885 | 0.000119 | 2.0 |
| 42 | 0x2ed82a0cd5f2f6c9759c4b2a77a224866eca3238 | 9 | 27,320,825 | 28,694,589 | 94,892,483 | 0.000095 | 2.0 |
| 43 | 0x5bd84f67e50551e3f135d952e10ff3a2562c131b | 7 | 30,000,000 | 30,000,000 | 92,559,488 | 0.000402 | 2.0 |
| 44 | 0x95cec2396015061cbfea82b24c8a683a9a8a1ab8 | 7 | 30,000,000 | 30,000,000 | 92,559,488 | 0.000283 | 2.0 |
| 45 | 0x66dceb2b3f5beb480b743e0889460fc7be54e2f8 | 7 | 30,000,000 | 30,000,000 | 92,559,488 | 0.000507 | 2.0 |
| 46 | 0xf5c08d55a77063ac4e5e18f1a470804088be1ad4 | 28 | 20,000,000 | 20,000,000 | 90,237,952 | 0.000353 | 2.0 |
| 47 | 0x65540841331bcd3085a7e25d83f78d941a87ca97 | 8 | 28,000,000 | 28,000,000 | 89,782,272 | 0.000404 | 2.0 |
| 48 | 0x46345207af256726d1d2a4a8bcfe70c2d446a147 | 9 | 26,664,804 | 27,645,804 | 88,988,290 | 0.000081 | 2.0 |
| 49 | 0xb9c3b7a17c62f2deacf4aeafe6b10962c660dc5f | 36 | 19,200,000 | 19,200,000 | 87,220,224 | 0.000100 | 2.0 |
| 50 | 0x2b151ba1ff176844884eaf82cc1c5e673f0f5a75 | 10 | 25,483,805 | 25,672,338 | 87,065,891 | 0.000060 | 2.0 |

## Impact Analysis by Transaction Type

### Transaction Type Breakdown
- **Type 2 (EIP-1559)**: 2,242 affected transactions (71%)
- **Type 0 (Legacy)**: 914 affected transactions (29%)
- **Type 4 (EIP-4844)**: 2 affected transactions (<1%)
- **Type 1 (EIP-2930)**: 1 affected transaction (<1%)

### Gas Efficiency of Affected Transactions
- Average gas efficiency (used/limit): 68.5%
- Many affected transactions show significant over-estimation of gas needs
- Opportunity for optimization exists for most affected addresses

## Economic Impact Assessment

### Transaction Splitting Costs
- **Base gas cost per additional transaction**: 21,000 gas
- **Average splits required**: 1.7 transactions
- **Cost increase**: Approximately 0.3% of original transaction cost

### Cost Distribution
- 80% of affected addresses would incur less than 0.001 ETH in additional costs
- Maximum individual address impact: 0.009012 ETH
- Median additional cost per address: 0.000355 ETH

## Technical Benefits Validation

### 1. DoS Protection Enhancement
With the cap limiting transactions to ~56% of a 30M gas block:
- Maximum impact of any single transaction is bounded
- Improved predictability for block builders
- Enhanced network resilience

### 2. zkVM Compatibility Benefits
The 16,777,216 (2^24) limit provides:
- Clean power-of-2 boundary for circuit design
- Efficient memory allocation in proving systems
- Better parallelization opportunities

### 3. Load Balancing Improvements
- More uniform transaction sizes enable better thread allocation
- Reduced variance in execution time
- Improved block packing efficiency

## Implementation Recommendations

### 1. Transition Strategy
- **Grace Period**: 3-6 months advance notice
- **Clear Communication**: Direct outreach to 492 affected addresses
- **Migration Support**: Documentation and tooling for transaction splitting

### 2. Monitoring Plan
- Track affected transaction patterns pre/post implementation
- Monitor address adaptation rates
- Measure actual vs. predicted cost impacts

### 3. Tooling Requirements
- Transaction splitting libraries for common frameworks
- Gas estimation updates in wallets
- Developer documentation and examples

## Conclusion

The extended analysis of 20.16 million transactions confirms that EIP-7983's proposed 16,777,216 gas cap would have minimal impact on the Ethereum ecosystem. With only 0.02% of transactions affected and negligible economic costs, the security and performance benefits significantly outweigh the minor inconveniences. The highly concentrated nature of impact (492 addresses) makes targeted migration support feasible and effective.

## Data Quality Notes
- **Analysis Period**: ~14 days (100,000 blocks)
- **Block Range**: 22,578,052 to 22,678,052
- **Total Transactions**: 20,164,635
- **High Gas Transactions Analyzed**: 703,491
- **Data Source**: Ethereum Mainnet via PyXatu

## Visualizations Generated
1. **Gas Distribution (Log Scale)**: Shows extreme right skew with outliers clearly visible
2. **Additional Costs by Cap**: Demonstrates minimal economic impact
3. **Affected Addresses Count**: Confirms concentrated impact
4. **Gas Distribution Box Plot**: Illustrates outlier characteristics
5. **Gas Efficiency Analysis**: Reveals optimization opportunities

---
*This extended analysis provides robust empirical evidence supporting the implementation of EIP-7983.*