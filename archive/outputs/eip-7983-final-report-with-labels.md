# EIP-7983 Technical Analysis: Affected Entity Identification

## Executive Summary
6-month analysis (251.9M txs) reveals 0.0383% impact across 4,601 addresses. Key finding: 82% of affected volume comes from automated systems (MEV bots, arbitrage, DeFi protocols) already capable of adaptation.

## Affected Entity Breakdown

### Category Distribution (Top 50 Addresses)
| Category | Entities | Transactions | % Impact | Avg Cost/Entity |
|----------|----------|--------------|----------|-----------------|
| MEV Bots | 11 | 8,038 | 23.5% | 0.000011 ETH |
| DeFi Protocols | 9 | 6,410 | 18.7% | 0.000016 ETH |
| Arbitrage Systems | 7 | 6,113 | 17.9% | 0.000010 ETH |
| Batch Operators | 6 | 4,973 | 14.5% | 0.000017 ETH |
| Contract Factories | 3 | 4,739 | 13.8% | 0.000008 ETH |
| Trading Bots | 3 | 1,469 | 4.3% | 0.000010 ETH |
| DeFi Strategies | 3 | 1,090 | 3.2% | 0.000010 ETH |
| Other | 8 | 3,515 | 10.3% | 0.000013 ETH |

## Technical Patterns by Entity Type

### 1. MEV Bots (11 entities, 23.5% impact)
```
Examples: 0x22dcb479..., 0x4fb9bbb1..., 0x70b00f8f...
Pattern: 20-26M gas for sandwich attacks
Current: Single atomic transaction
Post-EIP: 2 transactions (search + execute)
Adaptation: Trivial - already optimize for profit/gas
```

### 2. Arbitrage Systems (7 entities, 17.9% impact)
```
Examples: 0x78ec5c62..., 0x6582b7c8..., 0x75c51351...
Pattern: 25-35M gas for multi-hop paths
Current: Complex DEX routes in one tx
Post-EIP: Split routes or reduce hops
Adaptation: Medium - route optimization required
```

### 3. DeFi Protocols (9 entities, 18.7% impact)
```
Examples: 0x2a8b4976... (DEX Aggregator), 0xcde69d64... (Yield Optimizer)
Pattern: 30-35M gas for cross-protocol operations
Current: Batch all operations
Post-EIP: Chunk by protocol/operation type
Adaptation: Low - implement batching logic
```

### 4. Contract Deployment (3 entities, 13.8% impact)
```
Examples: 0xc87a8df3... (NFT Factory), 0xd6aaaa96... (Smart Contract Factory)
Pattern: 22-25M gas for large bytecode
Current: Single deployment transaction
Post-EIP: Constructor + initialize pattern
Adaptation: Low - standard pattern exists
```

## Economic Impact Analysis

### Cost Distribution
```
Percentile | Additional Cost (ETH)
-----------|---------------------
P50        | 0.000017
P90        | 0.000046
P95        | 0.000089
P99        | 0.000156
Max        | 0.000461
```

### Entity-Specific Impact
- **MEV Bots**: 0.000011 ETH average (negligible vs profits)
- **Arbitrage**: 0.000010 ETH average (< 0.1% of typical profit)
- **DeFi Protocols**: 0.000016 ETH average (passed to users)
- **Factories**: 0.000008 ETH average (one-time cost)

## Migration Complexity Assessment

### Immediate Adaptation (< 1 week)
- MEV Bots: Existing infrastructure supports splitting
- Trading Bots: Already optimize for gas prices
- Batch Operators: Simple loop modification

### Minor Changes Required (1-4 weeks)
- Arbitrage Systems: Route optimization algorithms
- DeFi Protocols: Implement operation chunking
- Contract Factories: Update deployment patterns

### No Manual Intervention
- 78.5% of affected addresses (< 10 txs) likely automated
- Operators will adapt based on economic incentives

## Key Insights

1. **Sophisticated Actors**: 82% of impact on automated systems
2. **Low Individual Burden**: Max 0.000461 ETH additional cost
3. **Existing Adaptability**: Most affected entities already gas-optimize
4. **Market-Driven Migration**: Economic incentives ensure adaptation

## Conclusion

The 4,601 affected addresses are predominantly sophisticated automated systems (MEV bots, arbitrage bots, DeFi protocols) with existing gas optimization capabilities. Maximum additional cost of 0.000461 ETH is negligible compared to operational profits. The 16,777,216 gas cap achieves security objectives with minimal friction for capable actors.

---
*Data: 180-day analysis | Method: Address labeling + pattern analysis*