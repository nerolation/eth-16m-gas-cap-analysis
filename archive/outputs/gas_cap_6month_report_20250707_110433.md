# 6-Month Empirical Analysis Report: EIP-7983 Transaction Gas Limit Cap

## Executive Summary

This report presents a comprehensive 6-month empirical analysis of EIP-7983, which proposes capping transaction gas limits at 16,777,216 (2^24). Based on partition-aware processing of 251,922,669 Ethereum mainnet transactions over 180 days, we find that the proposed cap would affect only 0.0383% of transactions.

## Key Findings

### 1. Transaction Impact Over 6 Months
- **Total Transactions Analyzed**: 251,922,669
- **Affected Transactions**: 96,577 (0.0383%)
- **Unique Addresses Affected**: 4,601
- **High Gas Transactions (>1M)**: 7,395,819

### 2. Economic Impact
- **Total Additional Costs**: 2.2437 ETH
- **Average Cost per Affected Transaction**: 0.000023 ETH if results['total_affected'] > 0 else 'N/A'
- **Average Cost per Affected Address**: 0.000488 ETH if results['unique_addresses'] > 0 else 'N/A'

### 3. To-Address Concentration
- **Unique To-Addresses**: 983
- **Concentration Ratio**: 0.21 to-addresses per from-address
- **Top 10 Recipients**: Receiving 81853/9657700.0% of affected transactions

### 4. Gas Usage Efficiency
- **Total Transactions with Gas Limit > 2^24**: 96,577
- **Transactions That Could Have Used < 2^24**: 18,500 (19.2%)
- **Average Gas Efficiency**: 71.4%
- **Average Gas Used**: 17,667,563
- **Min/Max Gas Used**: 21,000 / 35,888,566

## Top 50 Most Affected Addresses (6-Month Period)

| Rank | Address | Transactions | Avg Gas Limit | Max Gas Limit | Total Excess Gas | Est. Additional Cost (ETH) |
|------|---------|--------------|---------------|---------------|------------------|----------------------------|
| 1 | 0x22dcb4798abf95b96c18cb6aade0229ae8dda3e1 | 2555 | 19,940,819 | 20,025,269 | 8,083,004,674 | 0.000014 |
| 2 | 0xc87a8df3d07e06a929dc693245ef02630c848e85 | 2205 | 22,766,999 | 30,000,000 | 13,207,471,377 | 0.000009 |
| 3 | 0x78ec5c6265b45b9c98cf682665a00a3e8f085ffe | 1712 | 25,950,213 | 36,000,000 | 15,704,170,109 | 0.000011 |
| 4 | 0x2a8b49767e70fb65d477f8881ecf8023add8941c | 1559 | 34,411,392 | 35,947,097 | 27,491,679,791 | 0.000022 |
| 5 | 0xcde69d6418004b2e44b101121bf72397adc696ff | 1543 | 23,456,520 | 32,400,000 | 10,306,165,335 | 0.000010 |
| 6 | 0x61fbb052daf37a3b50616669a10c4778f08f3c6f | 1345 | 19,439,482 | 32,400,000 | 3,580,747,569 | 0.000008 |
| 7 | 0x4abf0b30452399793ff3a90ac016072b12f5ff32 | 1287 | 20,403,859 | 25,267,151 | 4,667,490,082 | 0.000012 |
| 8 | 0xd6aaaa96ed06389effbf0afb0b028c5b23a5ee77 | 1189 | 24,467,657 | 25,416,303 | 9,143,934,523 | 0.000007 |
| 9 | 0x7340d1918ff7e6df680745985086ad350a2b5678 | 1100 | 20,093,929 | 20,094,357 | 3,648,384,354 | 0.000008 |
| 10 | 0xb5b3f3f443fe3c1a42b6507ae211df69ac40c8d9 | 1089 | 19,461,632 | 34,508,005 | 2,923,328,635 | 0.000010 |
| 11 | 0x9735776a06bcf178b3ca198230e178fe74333333 | 1031 | 20,093,896 | 20,094,357 | 3,419,497,440 | 0.000009 |
| 12 | 0x23ab825aaffe678f6473133f7a7a90ab49f5b391 | 979 | 34,104,144 | 35,935,818 | 16,963,062,380 | 0.000023 |
| 13 | 0xa54d7d28bba53f816b2d8cf306aa985ddfc427e7 | 924 | 19,500,000 | 19,500,000 | 2,515,852,416 | 0.000010 |
| 14 | 0x70b00f8ffbaccbf662aff76dce82058296b46af9 | 882 | 20,023,997 | 20,025,269 | 2,863,660,451 | 0.000009 |
| 15 | 0x75c51351584199cdb072826c515cd08830ab4a0f | 864 | 30,209,492 | 33,737,454 | 11,605,486,075 | 0.000014 |
| 16 | 0x07a4ae312eb8ba5b4f65de06da50cab3df648573 | 767 | 28,950,916 | 34,200,000 | 9,337,227,594 | 0.000010 |
| 17 | 0x4fb9bbb1838ee0acb7b4d2e519a4c233198499fb | 761 | 26,021,000 | 26,021,000 | 7,034,519,624 | 0.000025 |
| 18 | 0x97d618e3a0afeccfb5c50b5df258cd7e48650510 | 757 | 20,000,000 | 20,000,000 | 2,439,647,488 | 0.000012 |
| 19 | 0xee67263be078df8ce3f55d5bcc1d23eb0cdc61bb | 658 | 26,968,965 | 32,400,000 | 6,706,170,845 | 0.000013 |
| 20 | 0xe81cfa76a9579686de04749c6c0d404e3b4a60b8 | 652 | 20,141,795 | 30,221,102 | 2,193,705,795 | 0.000012 |
| 21 | 0x6582b7c80df319553a988f62436b8a1be6b2b24c | 646 | 32,719,695 | 34,200,000 | 10,298,841,271 | 0.000010 |
| 22 | 0x6896e929ab60d400a58b43fb536d61390b0c297f | 620 | 20,023,590 | 20,023,633 | 2,012,751,636 | 0.000012 |
| 23 | 0xff0581a78019c65f3257429e053863304f555555 | 587 | 20,093,943 | 20,095,305 | 1,946,918,664 | 0.000009 |
| 24 | 0x18ada7d787e0adfbe12ea7b1dfc753d9eef97a01 | 578 | 20,024,706 | 20,025,269 | 1,877,049,072 | 0.000008 |
| 25 | 0x4f9e5e395bb7fa1a738e3bedc4dd7ceb98fc71f9 | 544 | 30,196,654 | 30,222,366 | 7,300,174,467 | 0.000008 |
| 26 | 0xe15e8a83416bb2791ba6c4b7cc51f4bec35198b1 | 530 | 20,023,627 | 20,023,633 | 1,720,597,739 | 0.000010 |
| 27 | 0x13d836ce6353f9aaf99606968775337d0b7411cf | 491 | 30,200,807 | 30,222,366 | 6,590,982,954 | 0.000008 |
| 28 | 0x5fbca865c4fe63967e7ad2cb13d8ffee75c53e09 | 477 | 17,576,565 | 17,661,497 | 381,289,458 | 0.000010 |
| 29 | 0x076f1e43502fa3ee9854eeb34edee2091219e2f6 | 404 | 27,586,077 | 29,323,000 | 4,366,779,736 | 0.000014 |
| 30 | 0x3f240ed97ecedc4cf7491a4e708f978cd98bfb59 | 400 | 25,520,000 | 25,600,000 | 3,497,113,600 | 0.000016 |
| 31 | 0x4ff2edb4076830b3f6aa538b09bca861f63eab29 | 393 | 33,350,399 | 34,681,538 | 6,513,261,056 | 0.000011 |
| 32 | 0xa17d003e0f6853cd146889066209d489795c5d86 | 386 | 34,260,086 | 34,929,945 | 6,748,387,842 | 0.000018 |
| 33 | 0xaa0fe001ed8871aa274d6addaccbd09aea9091af | 385 | 27,637,535 | 29,533,000 | 4,181,222,840 | 0.000011 |
| 34 | 0xd30e217e5747b645386eddb754ef1c7781b4cbe7 | 381 | 27,761,026 | 29,263,000 | 4,184,831,704 | 0.000014 |
| 35 | 0xb9c3b7a17c62f2deacf4aeafe6b10962c660dc5f | 381 | 19,741,732 | 20,000,000 | 1,129,480,704 | 0.000009 |
| 36 | 0xf5da5ccc3c327f62cdea038dafa8ccb152d6866b | 376 | 20,020,867 | 20,023,633 | 1,219,612,940 | 0.000009 |
| 37 | 0x8f1742532dd644441cfb294c66127be2f28cb994 | 373 | 27,468,780 | 28,843,000 | 3,987,953,432 | 0.000008 |
| 38 | 0x1ae49d90b01857899095ff1eb12d45b1d6ce8581 | 366 | 19,774,317 | 20,000,000 | 1,096,938,944 | 0.000009 |
| 39 | 0x26140e0d60126f8987d48ac23329fb9a5bd77f98 | 365 | 25,561,918 | 25,600,000 | 3,206,416,160 | 0.000019 |
| 40 | 0x0565f9bbab0081fa737c560e3fc4e36a92452814 | 364 | 20,008,211 | 20,536,178 | 1,176,082,066 | 0.000010 |
| 41 | 0x2403d61d5f6622cf5db15302beb2babfd2b8400c | 359 | 27,550,883 | 28,983,000 | 3,867,746,456 | 0.000014 |
| 42 | 0x052d2cbc749801b7ab5d0b59a6d27ea382b2a2ee | 358 | 27,428,670 | 28,883,000 | 3,813,220,672 | 0.000007 |
| 43 | 0xf5c08d55a77063ac4e5e18f1a470804088be1ad4 | 354 | 20,000,000 | 20,000,000 | 1,140,865,536 | 0.000046 |
| 44 | 0x0017df12fcc9e50aa5b27b33131d99af69d5dd9f | 353 | 26,807,456 | 28,263,000 | 3,540,674,752 | 0.000018 |
| 45 | 0xf502431dbfe2579f504a7ab8b00bda62bfde465f | 343 | 28,458,469 | 30,242,365 | 4,006,669,640 | 0.000019 |
| 46 | 0x18954f2629930248970989f27448bc6a8102366a | 340 | 27,553,735 | 29,153,000 | 3,664,016,560 | 0.000009 |
| 47 | 0x5a4e7c2067e8b32f01121eb50a0dc51e54915da7 | 340 | 27,336,112 | 28,463,000 | 3,590,024,560 | 0.000016 |
| 48 | 0x3b699ab06538ab79865a733f0f5418d1d57c6a2d | 338 | 27,496,402 | 29,113,000 | 3,623,084,992 | 0.000009 |
| 49 | 0x362ac45cfcb7970876ebe9c40358448c16dbcafc | 328 | 28,356,232 | 29,513,000 | 3,797,917,152 | 0.000019 |
| 50 | 0xe1fbfa8cc8d1735c795097818267708b98037398 | 328 | 27,182,384 | 28,723,000 | 3,412,895,152 | 0.000008 |


## Top 20 Recipient Addresses (To-Address Analysis)

| Rank | To Address | Transactions | Avg Gas Limit | Max Gas Limit |
|------|------------|--------------|---------------|---------------|
| 1 | 0x0de8bf93da2f7eecb3d9169422413a9bef4ef628 | 31406 | 23,605,648 | 36,000,000 |
| 2 | 0x0a252663dbcc0b073063d6420a40319e438cfa59 | 26048 | 28,897,093 | 36,000,000 |
| 3 | 0x0000000000771a79d0fc7f3b7fe270eb4498f20b | 10110 | 20,901,135 | 34,849,371 |
| 4 | 0x2f848984984d6c3c036174ce627703edaf780479 | 6688 | 23,536,096 | 35,838,106 |
| 5 | 0x3328f7f4a1d1c57c35df56bbf0c9dcafca309c49 | 1994 | 29,996,352 | 30,000,000 |
| 6 | 0x0a9077aa8a6e3b6016e9936ae3541a6bf5740eba | 1345 | 19,439,482 | 32,400,000 |
| 7 | 0xc3c7b049678d84081dfd0ba21a6c7fdcc31c226f | 1302 | 25,700,480 | 33,737,454 |
| 8 | 0x4041001020fcd967eac89b060388abc703119c73 | 1130 | 21,437,030 | 26,107,063 |
| 9 | 0xbd8916626c5b1b9f28da68aa0bc4a3d29a0d33d5 | 924 | 19,500,000 | 19,500,000 |
| 10 | 0x4f4495243837681061c4743b74b3eedf548d56a5 | 906 | 20,000,000 | 20,000,000 |
| 11 | 0xd1f3b954608551e0365c248a5a539ef08f9587a3 | 818 | 23,763,265 | 26,101,924 |
| 12 | 0x8d5f7156eb384902b71ae991c563bb9ee47e0d68 | 761 | 26,021,000 | 26,021,000 |
| 13 | 0xf70091dd85e62021c888b4c861c45749b793f869 | 757 | 20,000,000 | 20,000,000 |
| 14 | 0x00000000000000000000000000000000000face7 | 605 | 22,915,920 | 34,266,827 |
| 15 | 0xddc796a66e8b83d0bccd97df33a6ccfba8fd60ea | 553 | 20,000,000 | 20,000,000 |
| 16 | 0x2d5805a423d6ce771f06972ad4499f120902631a | 481 | 24,433,185 | 35,933,443 |
| 17 | 0xfef2359e77df8b769760d62cbb5ee676fe78f6c2 | 416 | 23,989,474 | 33,050,400 |
| 18 | 0x3fc29836e84e471a053d2d9e80494a867d670ead | 385 | 27,714,927 | 34,200,000 |
| 19 | 0xe957ea0b072910f508dd2009f4acb7238c308e29 | 337 | 19,353,185 | 29,396,120 |
| 20 | 0xd152f549545093347a162dce210e7293f1452150 | 328 | 26,067,321 | 35,451,675 |


## Analysis Methodology

### Data Processing Strategy
- **Analysis Period**: 180 days (6 months)
- **Processing Method**: Partition-aligned queries (1000-block partitions)
- **Batch Size**: 10,000 blocks per batch
- **Total Batches Processed**: 130

### Partition-Aware Optimization
1. Queries aligned to 1000-block partition boundaries
2. Smaller query ranges prevent timeouts
3. Aggregation without loading full dataset
4. JSON caching for fault tolerance

## Long-Term Trends

### Transaction Volume
- Average daily transactions: 1,399,570
- Average daily affected transactions: 536.5
- Consistent impact rate: 0.0383%

### Address Analysis
- Most affected addresses show persistent high-gas usage
- Top 50 addresses account for significant portion of impact
- Address concentration enables targeted migration support
- To-address concentration shows centralization around key contracts

### Gas Efficiency Insights
- 19.2% of high gas limit transactions didn't actually need > 2^24 gas
- Average efficiency of 71.4% indicates significant overprovisioning
- Many users set gas limits conservatively high without actual need

## Conclusions

The 6-month analysis confirms minimal and manageable impact:
1. **Stable Low Impact**: 0.0383% affected rate
2. **Concentrated Effect**: 4601 unique addresses
3. **Negligible Costs**: 2.2437 ETH total
4. **Predictable Patterns**: Consistent behavior over extended period
5. **Overprovisioning Common**: Many transactions set unnecessarily high gas limits

## Implementation Recommendations

1. **Timeline**: 6-month data supports proposed implementation schedule
2. **Outreach**: Direct communication to 4601 affected addresses
3. **Tooling**: Prioritize top 100 addresses for migration support
4. **Monitoring**: Continue tracking patterns post-implementation
5. **Education**: Help users understand appropriate gas limit setting

---
*Generated: 20250707_110433*
*Analysis based on partition-aware processing of 6 months of Ethereum mainnet data*
