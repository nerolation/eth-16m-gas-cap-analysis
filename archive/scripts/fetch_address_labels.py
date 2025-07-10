#!/usr/bin/env python3
"""
Fetch address labels from Etherscan for top affected addresses
"""

import pandas as pd
import time
import requests
from bs4 import BeautifulSoup
import json

def fetch_etherscan_label(address):
    """
    Fetch label from Etherscan for a given address
    """
    url = f"https://etherscan.io/address/{address}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for the main label/name
            # Try multiple selectors as Etherscan's HTML structure can vary
            
            # Method 1: Look for the name tag
            name_tag = soup.find('span', {'class': 'text-secondary'})
            if name_tag and name_tag.text.strip():
                return name_tag.text.strip()
            
            # Method 2: Look for contract name
            contract_name = soup.find('div', {'class': 'mt-1'})
            if contract_name:
                name_span = contract_name.find('span')
                if name_span and name_span.text.strip():
                    return name_span.text.strip()
            
            # Method 3: Look for token name
            token_tracker = soup.find('a', {'class': 'text-primary'})
            if token_tracker and 'Token:' in str(token_tracker):
                return token_tracker.text.strip()
            
            return "Unknown"
        else:
            return "Error"
    except Exception as e:
        print(f"Error fetching {address}: {e}")
        return "Error"

def get_top_50_addresses():
    """Load top 50 addresses from CSV"""
    df = pd.read_csv('gas_cap_6month_top50_20250707_080912.csv')
    return df

def main():
    """Fetch labels for top 50 addresses"""
    print("Loading top 50 addresses...")
    top50_df = get_top_50_addresses()
    
    # Known labels (you mentioned you already have some)
    known_labels = {
        "0x22dcb4798abf95b96c18cb6aade0229ae8dda3e1": "MEV Bot",
        "0x4fb9bbb1838ee0acb7b4d2e519a4c233198499fb": "MEV Bot", 
        "0x78ec5c6265b45b9c98cf682665a00a3e8f085ffe": "Arbitrage Bot",
        "0x2a8b49767e70fb65d477f8881ecf8023add8941c": "DEX Aggregator Router",
        "0x70b00f8ffbaccbf662aff76dce82058296b46af9": "MEV Bot",
        "0xee67263be078df8ce3f55d5bcc1d23eb0cdc61bb": "MEV Bot",
        "0xff0581a78019c65f3257429e053863304f555555": "MEV Bot",
        "0xb9c3b7a17c62f2deacf4aeafe6b10962c660dc5f": "MEV Bot",
        "0xf5c08d55a77063ac4e5e18f1a470804088be1ad4": "DeFi Protocol: Batch Processor",
        "0x6582b7c80df319553a988f62436b8a1be6b2b24c": "Flashloan Arbitrage Bot"
    }
    
    # Add label column
    top50_df['label'] = top50_df['address'].map(known_labels).fillna('')
    
    print("\nFetching labels from Etherscan for unlabeled addresses...")
    unlabeled = top50_df[top50_df['label'] == '']
    
    for idx, row in unlabeled.iterrows():
        if row['label'] == '':
            print(f"Fetching label for {row['address']}...")
            label = fetch_etherscan_label(row['address'])
            top50_df.at[idx, 'label'] = label
            time.sleep(1)  # Rate limiting
    
    # Save updated data
    output_file = 'top50_affected_with_labels.csv'
    top50_df.to_csv(output_file, index=False)
    print(f"\nSaved labeled data to {output_file}")
    
    # Create JSON for easy integration
    labels_dict = dict(zip(top50_df['address'], top50_df['label']))
    with open('address_labels.json', 'w') as f:
        json.dump(labels_dict, f, indent=2)
    
    # Print summary
    print("\nLabel Summary:")
    label_counts = top50_df['label'].value_counts()
    for label, count in label_counts.items():
        if label and label != 'Unknown' and label != 'Error':
            print(f"  {label}: {count}")

if __name__ == "__main__":
    main()