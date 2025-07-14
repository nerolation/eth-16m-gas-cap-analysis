#!/usr/bin/env python3
"""
Create and save the CDF chart
"""

import json
import matplotlib.pyplot as plt
import numpy as np
import glob
import os
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser(description='Create CDF chart from gas limit data')
parser.add_argument('-o', '--output', type=str, default='outputs',
                    help='Output directory (default: outputs)')
args = parser.parse_args()

OUTPUT_DIR = args.output

# Define color palette
COLORS = {
    'primary': '#2E86AB',
    'secondary': '#A23B72',
    'accent': '#F18F01',
    'success': '#51CF66',
    'danger': '#FF6B6B',
    'warning': '#FFD93D',
    'info': '#4ECDC4',
    'dark': '#2D3436',
    'light': '#DFE6E9',
    'neutral': '#636E72'
}

PROPOSED_GAS_CAP = int(2**24)

# Find and load CDF data
# First check in outputs/cdf_analysis/data, then in current directory for backward compatibility
cdf_files = sorted(glob.glob(os.path.join(OUTPUT_DIR, 'cdf_analysis/data/gas_limit_cdf_*.json')))
if not cdf_files:
    cdf_files = sorted(glob.glob('gas_limit_cdf_*.json'))
if not cdf_files:
    print("Error: CDF data not found!")
    exit(1)

cdf_file = cdf_files[-1]
print(f"Loading CDF data from: {cdf_file}")

with open(cdf_file, 'r') as f:
    cdf_data = json.load(f)

# Extract data
cdf_points = cdf_data['cdf_data']
cap_percentage = cdf_data['cap_percentage']
total_transactions = cdf_data['total_transactions']

# Prepare data for plotting
gas_limits = [point['gas_limit'] for point in cdf_points]
cumulative_pcts = [point['cumulative_percentage'] for point in cdf_points]

# Add points for smooth line
gas_limits_extended = [0] + gas_limits + [max(gas_limits) * 1.2]
cumulative_pcts_extended = [0] + cumulative_pcts + [100]

# Create the line chart
fig, ax = plt.subplots(1, 1, figsize=(14, 8))
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

# Plot the CDF as a line chart
ax.plot(gas_limits_extended, cumulative_pcts_extended, 
        linewidth=3, 
        color=COLORS['primary'], 
        label='CDF of Transaction Gas Limits',
        marker='o',
        markersize=6,
        markevery=slice(1, -1, 1))

# Add vertical dashed line at the proposed cap
ax.axvline(x=PROPOSED_GAS_CAP, 
           color=COLORS['danger'], 
           linestyle='--', 
           linewidth=2.5,
           alpha=0.8,
           label=f'Proposed Cap: {PROPOSED_GAS_CAP:,} ({PROPOSED_GAS_CAP/1e6:.2f}M)')

# Add horizontal dashed line at the cap percentage
ax.axhline(y=cap_percentage, 
           color=COLORS['danger'], 
           linestyle='--', 
           linewidth=2.5,
           alpha=0.8)

# Mark the intersection point
ax.scatter(PROPOSED_GAS_CAP, cap_percentage, 
           color=COLORS['danger'], 
           s=200, 
           zorder=5,
           edgecolor='white',
           linewidth=2)

# Add annotations
ax.annotate(f'{cap_percentage:.2f}%',
            xy=(PROPOSED_GAS_CAP, cap_percentage),
            xytext=(PROPOSED_GAS_CAP * 0.7, cap_percentage + 5),
            fontsize=14,
            fontweight='bold',
            color=COLORS['danger'],
            arrowprops=dict(arrowstyle='->', 
                          connectionstyle='arc3,rad=-0.2',
                          color=COLORS['danger'],
                          lw=2))

# Affected percentage annotation
affected_pct = 100 - cap_percentage
ax.text(PROPOSED_GAS_CAP * 1.3, 85,
        f'Only {affected_pct:.2f}% of transactions\nwould be affected by the cap',
        fontsize=13,
        fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.8', 
                 facecolor=COLORS['info'], 
                 alpha=0.9, 
                 edgecolor='none'),
        ha='left')

# Set logarithmic scale for x-axis
ax.set_xscale('log')

# Format the plot
ax.set_xlabel('Gas Limit (log scale)', fontsize=14, fontweight='bold')
ax.set_ylabel('Cumulative Percentage of Transactions (%)', fontsize=14, fontweight='bold')
ax.set_title(f'Cumulative Distribution Function of Transaction Gas Limits\nBased on {total_transactions:,} transactions over 6 months', 
             fontsize=16, fontweight='bold', pad=20)

# Set axis limits
ax.set_xlim(10000, 100000000)
ax.set_ylim(-2, 102)

# Customize grid
ax.grid(True, which='major', color='lightgray', alpha=0.5, linestyle='-')
ax.grid(True, which='minor', color='lightgray', alpha=0.2, linestyle=':')

# Remove top and right spines
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_linewidth(1.5)
ax.spines['bottom'].set_linewidth(1.5)

# Customize legend
ax.legend(loc='lower right', 
          frameon=True, 
          fancybox=True,
          shadow=True,
          facecolor='white', 
          edgecolor='lightgray',
          fontsize=12)

# Customize x-axis ticks
major_ticks = [21000, 100000, 1000000, 10000000, PROPOSED_GAS_CAP, 30000000]
ax.set_xticks(major_ticks)
ax.set_xticklabels([f'{x/1e6:.2f}M' if x >= 1e6 else f'{x/1e3:.0f}K' for x in major_ticks], 
                    fontsize=11)

# Add minor ticks
ax.minorticks_on()

# Customize y-axis
y_ticks = [0, 20, 40, 60, 80, 90, 95, 99, 100]
ax.set_yticks(y_ticks)
ax.set_yticklabels([f'{y}%' for y in y_ticks], fontsize=11)

plt.tight_layout()

# Ensure output directory exists
os.makedirs(os.path.join(OUTPUT_DIR, 'cdf_analysis'), exist_ok=True)

# Save the figure
output_file = os.path.join(OUTPUT_DIR, 'cdf_analysis/gas_limit_cdf_chart.png')
plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
print(f"\nChart saved to: {output_file}")

# Also save as PDF for higher quality
pdf_file = os.path.join(OUTPUT_DIR, 'cdf_analysis/gas_limit_cdf_chart.pdf')
plt.savefig(pdf_file, bbox_inches='tight', facecolor='white')
print(f"PDF version saved to: {pdf_file}")

# Show the plot
plt.show()

print("\nSummary:")
print(f"- {cap_percentage:.2f}% of transactions have gas limit ≤ {PROPOSED_GAS_CAP:,}")
print(f"- Only {100 - cap_percentage:.2f}% would be affected by the cap")