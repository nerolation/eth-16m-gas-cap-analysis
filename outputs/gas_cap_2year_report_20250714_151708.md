# 2 Year Empirical Analysis Report: EIP-7983 Transaction Gas Limit Cap

## Executive Summary

This report presents a comprehensive 2 year empirical analysis of EIP-7983, which proposes capping transaction gas limits at 16,777,216 (2^24). Based on partition-aware processing of 927,778,559 Ethereum mainnet transactions over 180 days, we find that the proposed cap would affect only 0.0681% of transactions.

## Key Findings

### 1. Transaction Impact Over 2 Years
- **Total Transactions Analyzed**: 927,778,559
- **Affected Transactions**: 632,052 (0.0681%)
- **Unique Addresses Affected**: 16,311
- **High Gas Transactions (>1M)**: 24,880,938

### 2. Economic Impact
- **Total Additional Gas Cost**: 13,318,347,000 gas units
- **Total Additional Cost (ETH)**: 297.6999 ETH
- **Average Gas Cost per Affected Transaction**: 21,072 gas units
- **Average Cost per Affected Transaction**: 0.000471 ETH
- **Average Cost per Affected Address**: 0.018251 ETH

### 3. To-Address Concentration
- **Unique To-Addresses**: 6,689
- **Concentration Ratio**: 0.41 to-addresses per from-address
- **Top 10 Recipients**: Receiving 143,722 transactions (22.7% of affected transactions)

### 4. Gas Usage Efficiency
- **Total Transactions with Gas Limit > 2^24**: 632,052
- **Transactions That Could Have Used < 2^24**: 507,434 (80.3%)
- **Average Gas Efficiency**: 24.1%
- **Average Gas Used**: 4,831,537
- **Min/Max Gas Used**: 21,000 / 35,888,566

## Top 50 Most Affected Addresses (2 year Period)

| Rank | Address | Transactions | Avg Gas Limit | Max Gas Limit | Total Excess Gas | Additional Gas Cost | Est. Additional Cost (ETH) |
|------|---------|--------------|---------------|---------------|------------------|---------------------|----------------------------|
| 1 | 0xbbfc2ed6ade409e263d8bf8f8bd4846919b46fc5 | 6440 | 18,500,000 | 18,500,000 | 11,094,728,960 | 135,240,000 | 0.000643 |
| 2 | 0x61fbb052daf37a3b50616669a10c4778f08f3c6f | 4507 | 18,637,683 | 32,400,000 | 8,385,123,302 | 94,647,000 | 0.000154 |
| 3 | 0x22dcb4798abf95b96c18cb6aade0229ae8dda3e1 | 3860 | 19,967,162 | 20,025,269 | 12,313,191,235 | 81,060,000 | 0.000026 |
| 4 | 0x56d6793c97befbb858ef0d021226e72fb1ed6566 | 3820 | 18,500,000 | 18,500,000 | 6,581,034,880 | 80,220,000 | 0.000742 |
| 5 | 0x666e80b80b8f9611f9b16b9debf4b916260924eb | 3021 | 18,500,000 | 18,500,000 | 5,204,530,464 | 63,441,000 | 0.000509 |
| 6 | 0xc87a8df3d07e06a929dc693245ef02630c848e85 | 2779 | 23,001,248 | 30,000,000 | 17,296,584,405 | 58,359,000 | 0.000062 |
| 7 | 0x5d0e1abce840ccf136c6ac32a0e9661c44767a83 | 2754 | 18,500,000 | 18,500,000 | 4,744,547,136 | 57,834,000 | 0.000404 |
| 8 | 0xfb2a84ebf08e41b4af6fa76ea727a2407c5ace6a | 2686 | 18,500,000 | 18,500,000 | 4,627,397,824 | 56,406,000 | 0.000456 |
| 9 | 0xd1825ae75994aa84e431c3cf838a2257a3e6fa9b | 2577 | 18,500,000 | 18,500,000 | 4,439,614,368 | 54,117,000 | 0.000549 |
| 10 | 0x78ec5c6265b45b9c98cf682665a00a3e8f085ffe | 1866 | 25,687,525 | 36,000,000 | 16,626,637,452 | 39,186,000 | 0.000019 |
| 11 | 0x6271772894ca78c360bf294bcd1bd497e4557dd5 | 1816 | 18,500,000 | 18,500,000 | 3,128,575,744 | 38,136,000 | 0.000671 |
| 12 | 0x4abf0b30452399793ff3a90ac016072b12f5ff32 | 1786 | 20,680,055 | 29,646,825 | 6,970,469,795 | 37,506,000 | 0.000061 |
| 13 | 0xfe44f15d0f81c83647c31ba85c6992718d35375f | 1749 | 18,500,000 | 18,500,000 | 3,013,149,216 | 36,729,000 | 0.000541 |
| 14 | 0x9949d45bca78b76d789b35b1177520559615846d | 1740 | 18,500,000 | 18,500,000 | 2,997,644,160 | 36,540,000 | 0.000567 |
| 15 | 0xcde69d6418004b2e44b101121bf72397adc696ff | 1658 | 23,458,798 | 32,400,000 | 11,078,062,604 | 34,818,000 | 0.000010 |
| 16 | 0x6356d943f7ef8c652e9e5bb0adce6f42409e3e5a | 1603 | 18,500,000 | 18,500,000 | 2,761,622,752 | 33,663,000 | 0.001168 |
| 17 | 0xd3e607d56ef2ab3dc8dcb71a22d8cf5939fa2419 | 1581 | 18,341,442 | 24,000,000 | 2,473,041,504 | 33,201,000 | 0.000093 |
| 18 | 0x76b9adb9b127ac9b2c65c037bc2e78011e20b0b6 | 1517 | 18,500,000 | 18,500,000 | 2,613,463,328 | 31,857,000 | 0.000738 |
| 19 | 0x6c23d555038d97aebdeb9e098677caa049e46763 | 1506 | 18,500,000 | 18,500,000 | 2,594,512,704 | 31,626,000 | 0.000806 |
| 20 | 0x2a8b49767e70fb65d477f8881ecf8023add8941c | 1491 | 34,277,600 | 35,947,097 | 26,093,072,038 | 62,622,000 | 0.000038 |
| 21 | 0x51976c47d8773e50e525be83a20f20b126b2c227 | 1463 | 18,500,000 | 18,500,000 | 2,520,432,992 | 30,723,000 | 0.000780 |
| 22 | 0xdfea5edb756913975eb46f8641e83b6252ed57be | 1426 | 18,500,000 | 18,500,000 | 2,456,689,984 | 29,946,000 | 0.000721 |
| 23 | 0x089fd0d2e73689c14e06530c804287317ed3990c | 1419 | 18,500,000 | 18,500,000 | 2,444,630,496 | 29,799,000 | 0.000978 |
| 24 | 0x02219db014db00a7003525d5b4ec2f58f13eb9de | 1405 | 18,500,000 | 18,500,000 | 2,420,511,520 | 29,505,000 | 0.000636 |
| 25 | 0xad520fd92f366b1e921ad835b14b7beccfe78b5e | 1399 | 18,500,000 | 18,500,000 | 2,410,174,816 | 29,379,000 | 0.000470 |
| 26 | 0x21432daa755aabf2438789415268bed44fa69d99 | 1384 | 18,500,000 | 18,500,000 | 2,384,333,056 | 29,064,000 | 0.000666 |
| 27 | 0x77993a9be9ca1dbc471bb775c2bb2dc1e5aea1c6 | 1377 | 18,500,000 | 18,500,000 | 2,372,273,568 | 28,917,000 | 0.000540 |
| 28 | 0x5fc4d0f9433efd9941bf97f294d7f1e03bfbdfc7 | 1373 | 18,500,000 | 18,500,000 | 2,365,382,432 | 28,833,000 | 0.000454 |
| 29 | 0x21976dffe33bc4324f4ac145e0943d15432e0d8d | 1338 | 18,500,000 | 18,500,000 | 2,305,084,992 | 28,098,000 | 0.000320 |
| 30 | 0xd5e98002a2df69407ee81b2f90aa4e3d3580b012 | 1286 | 18,500,000 | 18,500,000 | 2,215,500,224 | 27,006,000 | 0.000452 |
| 31 | 0x8c7fe73cfe50c5fa9bd7e19b6c253700413bf83c | 1272 | 18,500,000 | 18,500,000 | 2,191,381,248 | 26,712,000 | 0.000906 |
| 32 | 0x02c00f68cdf09ab84cbc3ad55d442e258c533c3a | 1265 | 18,500,000 | 18,500,000 | 2,179,321,760 | 26,565,000 | 0.000614 |
| 33 | 0x47c787264e2055784436e284ddd97af38eca3a52 | 1256 | 18,500,000 | 18,500,000 | 2,163,816,704 | 26,376,000 | 0.000444 |
| 34 | 0x46d70f2b90139361d68423e6b140240526f887a8 | 1219 | 18,500,000 | 18,500,000 | 2,100,073,696 | 25,599,000 | 0.000568 |
| 35 | 0x9e727213361d39bb2c1f626be4ea8ee92f87e7f0 | 1193 | 18,500,000 | 18,500,000 | 2,055,281,312 | 25,053,000 | 0.000444 |
| 36 | 0x23ab825aaffe678f6473133f7a7a90ab49f5b391 | 1191 | 33,471,786 | 35,935,818 | 19,883,232,921 | 25,011,000 | 0.000015 |
| 37 | 0xceebc5ba792a9faf6937bf4f02c7d1efaa4bf35e | 1186 | 18,500,000 | 18,500,000 | 2,043,221,824 | 24,906,000 | 0.001395 |
| 38 | 0xdb051d5f8787084b9f3938719080f0539617acac | 1178 | 18,500,000 | 18,500,000 | 2,029,439,552 | 24,738,000 | 0.000556 |
| 39 | 0x2967f8dbe644d7a4e24689b0da59fa10cf522901 | 1175 | 18,500,000 | 18,500,000 | 2,024,271,200 | 24,675,000 | 0.000536 |
| 40 | 0x91a515faeda894e257d8a8b4ba8f03ca21d298e8 | 1164 | 18,500,000 | 18,500,000 | 2,005,320,576 | 24,444,000 | 0.000534 |
| 41 | 0x0fdbc9e411f80bf8cdb0064d73ae2ed1f4eadb85 | 1162 | 18,500,000 | 18,500,000 | 2,001,875,008 | 24,402,000 | 0.000985 |
| 42 | 0xd6aaaa96ed06389effbf0afb0b028c5b23a5ee77 | 1153 | 24,489,332 | 25,416,303 | 8,892,069,313 | 24,213,000 | 0.000007 |
| 43 | 0xcfba00c42567032daf7a001432fbee3ba2e3ad71 | 1152 | 18,500,000 | 18,500,000 | 1,984,647,168 | 24,192,000 | 0.000733 |
| 44 | 0x8aa834b9ae52b790b025cc4b2ab786fc348d20fe | 1148 | 18,500,000 | 18,500,000 | 1,977,756,032 | 24,108,000 | 0.000478 |
| 45 | 0xde5b0e5b90cc4dd141b5cd2596db10c1c8c239e3 | 1144 | 18,500,000 | 18,500,000 | 1,970,864,896 | 24,024,000 | 0.000522 |
| 46 | 0x639598de2b83a809dc13d1fb675611c9044bd726 | 1131 | 18,500,000 | 18,500,000 | 1,948,468,704 | 23,751,000 | 0.000533 |
| 47 | 0x0229c3aaf7694eb48e4f70c975ca2b6b0f8697f4 | 1106 | 18,500,000 | 18,500,000 | 1,905,399,104 | 23,226,000 | 0.000682 |
| 48 | 0x9735776a06bcf178b3ca198230e178fe74333333 | 1104 | 20,093,911 | 20,094,357 | 3,661,631,637 | 23,184,000 | 0.000009 |
| 49 | 0x503a46e21a45f7bd65f530f4a2def481e565bcb2 | 1103 | 18,500,000 | 18,500,000 | 1,900,230,752 | 23,163,000 | 0.000634 |
| 50 | 0xa54d7d28bba53f816b2d8cf306aa985ddfc427e7 | 1101 | 19,465,411 | 20,000,000 | 2,959,703,184 | 23,121,000 | 0.000024 |


## Top 20 Recipient Addresses (To-Address Analysis)

| Rank | To Address | Transactions | Avg Gas Limit | Max Gas Limit |
|------|------------|--------------|---------------|---------------|
| 1 | 0x0de8bf93da2f7eecb3d9169422413a9bef4ef628 | 58140 | 22,830,430 | 36,000,000 |
| 2 | 0x0a252663dbcc0b073063d6420a40319e438cfa59 | 36354 | 27,928,680 | 36,000,000 |
| 3 | 0x0000000000771a79d0fc7f3b7fe270eb4498f20b | 16110 | 20,915,017 | 34,849,371 |
| 4 | 0x2f848984984d6c3c036174ce627703edaf780479 | 8759 | 22,849,039 | 35,838,106 |
| 5 | 0x7363e9fcfb0ec50ad62af7307b9312ceb0215e43 | 6440 | 18,500,000 | 18,500,000 |
| 6 | 0x0a9077aa8a6e3b6016e9936ae3541a6bf5740eba | 4484 | 18,576,342 | 32,400,000 |
| 7 | 0x3b3c6ba253aeeba42ad332963ab369528965c292 | 3840 | 18,500,000 | 18,500,000 |
| 8 | 0xd994baab91f87bf597520c3e255573929eba81fd | 3820 | 18,500,000 | 18,500,000 |
| 9 | 0xcb18c3bb1adbdd79362c352db945ba71434ac0d2 | 3021 | 18,500,000 | 18,500,000 |
| 10 | 0xaa7820a8f40cc2fba3f6915b9520dd8f093efb53 | 2754 | 18,500,000 | 18,500,000 |
| 11 | 0x184aaf087ca6dd17eb1200dbfbee9f671bd906fc | 2577 | 18,500,000 | 18,500,000 |
| 12 | 0xb48eb8368c9c6e9b0734de1ef4ceb9f484b80b9c | 2513 | 26,137,980 | 30,000,000 |
| 13 | 0x3328f7f4a1d1c57c35df56bbf0c9dcafca309c49 | 2484 | 28,466,465 | 30,000,000 |
| 14 | 0xfef2359e77df8b769760d62cbb5ee676fe78f6c2 | 2354 | 25,078,776 | 33,050,400 |
| 15 | 0xc3c7b049678d84081dfd0ba21a6c7fdcc31c226f | 1845 | 24,057,412 | 33,737,454 |
| 16 | 0x35c8941c294e9d60e0742cb9f3d58c0d1ba2dec4 | 1815 | 23,896,162 | 30,000,000 |
| 17 | 0xc4d6fbecdf22a32542ae9ef4fea807787630743d | 1740 | 18,500,000 | 18,500,000 |
| 18 | 0x5161f77d1279ffe4373841057adb962323acc750 | 1603 | 18,500,000 | 18,500,000 |
| 19 | 0xd0d49a9e152f2a8d33403ede4f07653c220cca14 | 1517 | 18,500,000 | 18,500,000 |
| 20 | 0x81452d1bb6dba3589f2e1c6244964a07552b7a73 | 1506 | 18,500,000 | 18,500,000 |


## Analysis Methodology

### Data Processing Strategy
- **Analysis Period**: 720 days (24 months)
- **Processing Method**: Partition-aligned queries (1000-block partitions)
- **Batch Size**: 10,000 blocks per batch
- **Total Batches Processed**: 519

### Partition-Aware Optimization
1. Queries aligned to 1000-block partition boundaries
2. Smaller query ranges prevent timeouts
3. Aggregation without loading full dataset
4. JSON caching for fault tolerance

## Long-Term Trends

### Transaction Volume
- Average daily transactions: 1,288,581
- Average daily affected transactions: 877.9
- Consistent impact rate: 0.0681%

### Address Analysis
- Most affected addresses show persistent high-gas usage
- Top 50 addresses account for significant portion of impact
- Address concentration enables targeted migration support
- To-address concentration shows centralization around key contracts

### Gas Efficiency Insights
- 80.3% of high gas limit transactions didn't actually need > 2^24 gas
- Average efficiency of 24.1% indicates significant overprovisioning
- Many users set gas limits conservatively high without actual need

---
*Generated: 20250714_151708*
*Analysis based on partition-aware processing of 24 months of Ethereum mainnet data*
