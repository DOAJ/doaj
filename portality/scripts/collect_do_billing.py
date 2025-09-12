#!/usr/bin/env python3
"""
Script to collect DOAJ billing information from Digital Ocean invoices for a specific month.

Usage: python collect_do_billing.py YYYY-MM -t TOKEN [-g <GBP paid>] [--hide-total]

This script:
1. Lists invoices for the specified month
2. Accepts a GPB amout paid for the invoice to convert USD to GBP
3. Gets invoice items using doctl API
4. Filters for DOAJ-related items:
   - Items in the DOAJ project
   - Items without project assignment but with 'doaj' in the name (e.g., snapshots)
5. Categorizes resources as Production or Test based on droplet tags and naming conventions
6. Outputs a summary report with environment breakdown

Required DigitalOcean API Token Permissions:
===========================================

This script requires a DigitalOcean API token with the following permissions:

MINIMAL CUSTOM SCOPES (Recommended):
- billing:read    - Access billing invoices and invoice items
- droplet:read    - List droplets and their tags for categorization
- account:read    - Access account-level billing information

ALTERNATIVE (Less Secure):
- Read Only       - Grants read access to all resources in your account
- Full Access     - Grants full access (not recommended for this script)

To create a token with custom scopes:
1. Go to DigitalOcean Control Panel > API > Tokens/Keys
2. Click "Generate New Token"
3. Select "Custom Scopes" 
4. Enable: billing:read, droplet:read, account:read
5. Set appropriate expiration date

Note: You cannot modify token scopes after creation. If you need different 
permissions, you must create a new token.

Security Best Practice: Use the minimal custom scopes rather than Full Access
to follow the principle of least privilege.
"""

import sys
import subprocess
import json
import argparse
import re
from datetime import datetime
from enum import Enum

# Global variables
DO_TOKEN = None

class Envs(Enum):
    PRODUCTION = 'Production'
    TEST = 'Test'

TAG_ENVIRONMENT_MAP = {'doaj-test': Envs.TEST, 'doaj': Envs.PRODUCTION}

# Store the tags for all droplets for lookup later
DROPLET_TAGS = {}


def run_doctl_command(command):
    """Run a doctl command and return the result."""
    # Split command into list for safe execution
    cmd_parts = command.split()
    cmd_parts.extend(['--access-token', DO_TOKEN])
    
    try:
        result = subprocess.run(
            cmd_parts,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running doctl command: {' '.join(cmd_parts[:-2])} --access-token [REDACTED]")
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


def get_droplet_tags():
    """Get droplet names and their tags."""
    command = "doctl compute droplet list --output json"
    
    try:
        output = run_doctl_command(command)
        if not output:
            return {}
        
        droplets = json.loads(output)
        tags_map = {}
        
        for droplet in droplets:
            name = droplet.get('name', '')
            tags = droplet.get('tags', [])
            tags_map[name] = tags
            
        return tags_map
    except Exception as e:
        print(f"Error getting droplet tags: {e}")
        return {}


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


def get_droplet_name_from_description(description):
    """Extract droplet name from invoice description."""
    # Description format is usually "droplet-name (size)" for droplets
    match = re.match(r'^([^(]+)', description)
    return match.group(1).strip() if match else description


def categorize_item_environment(item):
    """Categorize an item as Production or Test using global tag mapping."""
    if item.get('product') == 'Droplets':
        droplet_name = get_droplet_name_from_description(item.get('description', ''))
        tags = DROPLET_TAGS.get(droplet_name, [])
        
        # Check tags against environment mapping
        for tag in tags:
            if env := TAG_ENVIRONMENT_MAP.get(tag):
                return env
        
        # Droplet not in current list - probably a destroyed test server
        if droplet_name not in DROPLET_TAGS:
            # Use naming convention: 4-digit names are test servers
            return Envs.TEST if re.match(r'^\d{4}$', droplet_name) else Envs.PRODUCTION
        else:
            return Envs.PRODUCTION
    else:
        # For non-droplets, use naming convention or default to production
        return Envs.TEST if 'test' in item.get('description', '').lower() else Envs.PRODUCTION


def process_invoice_items(invoice_items):
    """Process invoice items and return DOAJ-related items with environment categorization."""
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
                'reason': reason,
                'environment': categorize_item_environment(item).value
            })
    
    print(f"    Processed {len(invoice_items)} items, found {len(doaj_items)} DOAJ items")
    return doaj_items


def print_summary_report(all_doaj_items, target_month, exchange_rate=None):
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
    print(f"{'Description':<45} {'Product':<18} {'Environment':<12} {'Amount (USD)':>12} {'Amount (GBP)':>12}")
    print("-" * 102)
    
    total_amount = 0
    for item in all_items:
        description = item['description'][:42] + "..." if len(item['description']) > 45 else item['description']
        product = item['product'][:15] + "..." if len(item['product']) > 18 else item['product']
        environment = item['environment']
        amount = item['amount']
        gbp = amount / exchange_rate if exchange_rate else 0.0
        
        total_amount += amount
        
        print(f"{description:<45} {product:<18} {environment:<12} ${amount:>10.2f} £{gbp:>10.2f}")

    total_gbp = total_amount / exchange_rate if exchange_rate else 0.0
    print("-" * 102)
    print(f"{'TOTAL':<77} ${total_amount:>10.2f} £{total_gbp:>10.2f}")
    
    # Print breakdown by product type
    product_totals = {}
    for item in all_items:
        product = item['product']
        product_totals[product] = product_totals.get(product, 0) + item['amount']
    
    print(f"\nBreakdown by Product Type:")
    print("-" * 48)
    for product, amount in sorted(product_totals.items(), key=lambda x: x[1], reverse=True):
        gbp = amount / exchange_rate if exchange_rate else 0.0
        print(f"{product:<30} ${amount:>8.2f} £{gbp:>8.2f}")
    
    # Print breakdown by Environment
    env_totals = {}
    for item in all_items:
        env = item['environment']
        env_totals[env] = env_totals.get(env, 0) + item['amount']
    
    print(f"\nBreakdown by Environment:")
    print("-" * 48)
    for env, amount in sorted(env_totals.items(), key=lambda x: x[1], reverse=True):
        gbp = amount / exchange_rate if exchange_rate else 0.0
        print(f"{env:<30} ${amount:>8.2f} ${gbp:>8.2f}")


def main():
    """Main function to collect and process DOAJ billing information for a specific month."""
    global DO_TOKEN
    
    parser = argparse.ArgumentParser(description='Collect DOAJ billing data from Digital Ocean for a specific month')
    parser.add_argument('month', help='Month in YYYY-MM format (e.g., 2024-01)')
    parser.add_argument('-t', '--token', required=True, help='DigitalOcean API access token')
    parser.add_argument('-g', '--gbp', required=False, help='GBP Amount paid for this invoice')
    parser.add_argument('--hide-total', action='store_true', help='Hide the total invoice amount')
    
    args = parser.parse_args()
    target_month = args.month
    DO_TOKEN = args.token
    gbp_amount = float(args.gbp) if args.gbp else None
    
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
    
    # Get droplet tags for categorization
    print("Fetching droplet tags...")
    global DROPLET_TAGS
    DROPLET_TAGS = get_droplet_tags()
    print(f"Retrieved tags for {len(DROPLET_TAGS)} droplets")
    
    # Process the invoice
    uuid = invoice.get('invoice_uuid', '')
    total_info = "" if args.hide_total else f" (Total: ${invoice['amount']})"
    
    print(f"\nProcessing invoice: {uuid}{total_info}")
    
    # Get invoice items
    invoice_items = get_invoice_items(uuid)
    if invoice_items:
        print(f"  Retrieved {len(invoice_items)} invoice items")
        # Process items for DOAJ-related resources
        doaj_items = process_invoice_items(invoice_items)

        total_invoice = float(invoice['amount'])
        if not args.hide_total: print(f"  Invoice total amount: ${total_invoice:.2f}")
        exchange_rate = None
        if gbp_amount:
            print(f"  GBP Amount provided: £{gbp_amount:.2f}")
            exchange_rate = total_invoice / gbp_amount if gbp_amount != 0 else 0
            print(f"  Implied Exchange Rate: {exchange_rate:.4f} USD/GBP")

        if doaj_items:
            doaj_amount = sum(item['amount'] for item in doaj_items)
            gbp_tot = f" (£{doaj_amount / exchange_rate:.2f})" if exchange_rate else ""
            print(f"  Found {len(doaj_items)} DOAJ items totaling ${doaj_amount:.2f}{gbp_tot}")
            
            # Print summary report
            all_doaj_items = {uuid: doaj_items}
            print_summary_report(all_doaj_items, target_month, exchange_rate)
        else:
            print(f"\nNo DOAJ-related resources found for {target_month}")
    else:
        print(f"  No invoice items retrieved")


if __name__ == "__main__":
    main()