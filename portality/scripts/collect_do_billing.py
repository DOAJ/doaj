#!/usr/bin/env python3
"""
Script to collect DOAJ billing information from Digital Ocean invoices for a specific month.

Usage: python collect_do_billing.py YYYY-MM

This script:
1. Lists invoices for the specified month
2. Downloads CSV data for matching invoices
3. Filters for DOAJ-related items:
   - Items in the DOAJ project
   - Items without project assignment but with 'doaj' in the name (e.g., snapshots)
4. Outputs a summary report with all matching resources and total cost
"""

import sys
import subprocess
import json
import argparse
from datetime import datetime

# Global token variable
DO_TOKEN = None


def run_doctl_command(command):
    """Run a doctl command and return the result."""
    command = f"{command} --access-token {DO_TOKEN}"
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running doctl command: {command}")
        print(f"Error: {e.stderr}")
        sys.exit(1)


def get_invoices():
    """Get list of all invoices in JSON format."""
    print("Fetching invoice list...")
    command = "doctl invoice list --output json"
    output = run_doctl_command(command)
    
    if not output:
        print("No invoices found")
        return []
    
    try:
        data = json.loads(output)
        # The actual format has invoices nested under 'invoices' key
        return data.get('invoices', [])
    except json.JSONDecodeError as e:
        print(f"Error parsing invoice JSON: {e}")
        sys.exit(1)


def find_invoice_for_month(invoices, target_month):
    """Find the invoice for the specified month."""
    for invoice in invoices:
        if invoice.get('invoice_period', '') == target_month:
            print(f"Found invoice for {target_month}")
            return invoice
    
    print(f"No invoice found for {target_month}")
    return None


def get_invoice_items(invoice_uuid):
    """Get invoice items as JSON data."""
    command = f"doctl invoice get {invoice_uuid} --output json"
    
    try:
        output = run_doctl_command(command)
        if not output:
            return []
        
        data = json.loads(output)
        return data.get('invoice_items', [])
    except Exception as e:
        print(f"Error getting invoice items for {invoice_uuid}: {e}")
        return []


def is_doaj_related(item):
    """Check if an item is DOAJ-related based on project or name."""
    project_name = item.get('project_name', '').lower()
    description = item.get('description', '').lower()
    
    # Check if in DOAJ project
    if 'doaj' in project_name:
        return True, 'DOAJ Project'
    
    # Check if no project but has 'doaj' in description/name
    if not project_name and 'doaj' in description:
        return True, 'DOAJ Resource (no project)'
    
    return False, ''


def process_invoice_items(invoice_items):
    """Process invoice items and return DOAJ-related items."""
    doaj_items = []
    
    for item in invoice_items:
        is_doaj, reason = is_doaj_related(item)
        if is_doaj:
            amount = float(item.get('amount', '0'))
            
            doaj_items.append({
                'description': item.get('description', ''),
                'product': item.get('product', ''),
                'amount': amount,
                'project': item.get('project_name', ''),
                'category': item.get('category', ''),
                'reason': reason
            })
    
    print(f"    Processed {len(invoice_items)} items, found {len(doaj_items)} DOAJ items")
    return doaj_items


def print_summary_report(all_doaj_items, target_month):
    """Print a summary report of all DOAJ resources and costs."""
    print(f"\nDOAJ Digital Ocean Billing Summary for {target_month}")
    print("=" * 80)
    
    if not all_doaj_items:
        print("No DOAJ-related resources found for this month.")
        return
    
    # Collect all items
    all_items = []
    for doaj_items in all_doaj_items.values():
        all_items.extend(doaj_items)
    
    if not all_items:
        print("No DOAJ-related resources found for this month.")
        return
    
    # Sort by amount (highest first)
    all_items.sort(key=lambda x: x['amount'], reverse=True)
    
    # Print each resource
    print(f"{'Description':<50} {'Product':<20} {'Project':<15} {'Amount (USD)':>12}")
    print("-" * 80)
    
    total_amount = 0
    for item in all_items:
        description = item['description'][:47] + "..." if len(item['description']) > 50 else item['description']
        product = item['product'][:17] + "..." if len(item['product']) > 20 else item['product']
        project = item['project'][:12] + "..." if len(item['project']) > 15 else item['project']
        amount = item['amount']
        
        total_amount += amount
        
        print(f"{description:<50} {product:<20} {project:<15} ${amount:>10.2f}")
    
    print("-" * 80)
    print(f"{'TOTAL':<87} ${total_amount:>10.2f}")
    
    # Print breakdown by product type
    product_totals = {}
    for item in all_items:
        product = item['product']
        product_totals[product] = product_totals.get(product, 0) + item['amount']
    
    print(f"\nBreakdown by Product Type:")
    print("-" * 40)
    for product, amount in sorted(product_totals.items(), key=lambda x: x[1], reverse=True):
        print(f"{product:<30} ${amount:>8.2f}")


def main():
    """Main function to collect and process DOAJ billing information for a specific month."""
    global DO_TOKEN
    
    parser = argparse.ArgumentParser(description='Collect DOAJ billing data from Digital Ocean for a specific month')
    parser.add_argument('month', help='Month in YYYY-MM format (e.g., 2024-01)')
    parser.add_argument('-t', '--token', required=True, help='DigitalOcean API access token')
    
    args = parser.parse_args()
    target_month = args.month
    DO_TOKEN = args.token
    
    # Validate month format
    try:
        datetime.strptime(target_month, '%Y-%m')
    except ValueError:
        print("Error: Month must be in YYYY-MM format (e.g., 2024-01)")
        sys.exit(1)
    
    # Get invoices and find the one for target month
    all_invoices = get_invoices()
    invoice = find_invoice_for_month(all_invoices, target_month)
    
    if not invoice:
        return
    
    # Process the invoice
    uuid = invoice.get('invoice_uuid', '')
    amount = invoice.get('amount', 0)
    
    print(f"\nProcessing invoice: {uuid} (${amount})")
    
    # Get invoice items
    invoice_items = get_invoice_items(uuid)
    if invoice_items:
        print(f"  Retrieved {len(invoice_items)} invoice items")
        # Process items for DOAJ-related resources
        doaj_items = process_invoice_items(invoice_items)
        if doaj_items:
            doaj_amount = sum(item['amount'] for item in doaj_items)
            print(f"  Found {len(doaj_items)} DOAJ items totaling ${doaj_amount:.2f}")
            
            # Print summary report
            all_doaj_items = {uuid: doaj_items}
            print_summary_report(all_doaj_items, target_month)
        else:
            print(f"\nNo DOAJ-related resources found for {target_month}")
    else:
        print(f"  No invoice items retrieved")


if __name__ == "__main__":
    main()