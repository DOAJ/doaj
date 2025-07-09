#!/usr/bin/env python3
"""
Script to convert between PO and CSV files for translation purposes

Usage:
  To convert from PO to CSV: python po_csv_converter.py po2csv <po_file> <csv_file>
  To convert from CSV to PO: python po_csv_converter.py csv2po <csv_file> <po_file>
  To update existing PO file from CSV: python po_csv_converter.py update_po <csv_file> <po_file>
"""

import csv
import re
import sys
import os
import shutil
import argparse


def po_to_csv(po_file, csv_file):
    """Convert a PO file to CSV format."""
    with open(po_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract header
    header_match = re.search(r'^msgid ""\nmsgstr "(.+?)"', content, re.DOTALL)
    header = header_match.group(1) if header_match else ""

    # Parse entries
    entries = []
    current_entry = {
        'locations': [],
        'fuzzy': False,
        'msgid': '',
        'msgstr': ''
    }

    in_msgid = False
    in_msgstr = False

    for line in content.split('\n'):
        line = line.strip()

        # Skip empty lines
        if not line:
            if current_entry['msgid']:  # If we have a msgid, this is the end of an entry
                entries.append(current_entry)
                current_entry = {
                    'locations': [],
                    'fuzzy': False,
                    'msgid': '',
                    'msgstr': ''
                }
            in_msgid = False
            in_msgstr = False
            continue

        # Location comment
        if line.startswith('#:'):
            # Extract all locations from the line
            locations = line[2:].strip()
            # Split by spaces and commas to get individual locations
            for loc in re.split(r'[,\s]+', locations):
                if loc:  # Skip empty strings
                    current_entry['locations'].append(loc)
            continue

        # Fuzzy flag
        if line.startswith('#,') and 'fuzzy' in line:
            current_entry['fuzzy'] = True
            continue

        # Message ID
        if line.startswith('msgid '):
            in_msgid = True
            in_msgstr = False
            if line[6:].startswith('"') and line[6:].endswith('"'):
                current_entry['msgid'] = line[7:-1]
            continue

        # Message string
        if line.startswith('msgstr '):
            in_msgid = False
            in_msgstr = True
            if line[7:].startswith('"') and line[7:].endswith('"'):
                current_entry['msgstr'] = line[8:-1]
            continue

        # Continuation of msgid or msgstr
        if line.startswith('"') and line.endswith('"'):
            if in_msgid:
                current_entry['msgid'] += line[1:-1]
            elif in_msgstr:
                current_entry['msgstr'] += line[1:-1]

    # Add the last entry if it exists
    if current_entry['msgid']:
        entries.append(current_entry)

    # Write to CSV
    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['location', 'fuzzy', 'msgid', 'msgstr'])
        for entry in entries:
            writer.writerow([
                '; '.join(entry['locations']),
                'Yes' if entry['fuzzy'] else 'No',
                entry['msgid'],
                entry['msgstr']
            ])

    print(f"Successfully converted {po_file} to {csv_file}")
    print(f"Total entries: {len(entries)}")


def csv_to_po(csv_file, po_file):
    """Convert a CSV file back to PO format."""
    entries = []

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append({
                'location': row['location'],
                'fuzzy': row['fuzzy'].lower() == 'yes',
                'msgid': row['msgid'],
                'msgstr': row['msgstr']
            })

    # Get original PO file to extract header
    original_po_file = None
    if os.path.exists(po_file):
        with open(po_file, 'r', encoding='utf-8') as f:
            original_content = f.read()
            header_match = re.search(r'^msgid ""\nmsgstr "(.+?)"', original_content, re.DOTALL)
            if header_match:
                original_po_file = original_content

    with open(po_file, 'w', encoding='utf-8') as f:
        # Write header
        if original_po_file:
            # Extract header up to the first entry
            header_end = original_content.find('#:', original_content.find('msgstr ""'))
            if header_end > 0:
                f.write(original_content[:header_end])
            else:
                f.write('msgid ""\nmsgstr ""\n')
        else:
            f.write('msgid ""\nmsgstr ""\n')

        f.write('\n')

        # Write entries
        for entry in entries:
            # Location
            if entry['location']:
                # Split locations by semicolon and write each on a new line
                locations = entry['location'].split(';')
                for loc in locations:
                    loc = loc.strip()
                    if loc:  # Skip empty strings
                        f.write(f"#: {loc}\n")

            # Fuzzy flag
            if entry['fuzzy']:
                f.write("#, fuzzy\n")

            # Handle multiline msgid
            msgid = entry['msgid']
            if '\n' in msgid:
                f.write('msgid ""\n')
                for line in msgid.split('\n'):
                    f.write(f'"{line}\\n"\n')
            else:
                f.write(f'msgid "{msgid}"\n')

            # Handle multiline msgstr
            msgstr = entry['msgstr']
            if '\n' in msgstr:
                f.write('msgstr ""\n')
                for line in msgstr.split('\n'):
                    f.write(f'"{line}\\n"\n')
            else:
                f.write(f'msgstr "{msgstr}"\n')

            f.write('\n')

    print(f"Successfully converted {csv_file} to {po_file}")
    print(f"Total entries: {len(entries)}")


def update_po(csv_file, po_file):
    """Update an existing PO file with translations from a CSV file."""
    if not os.path.exists(po_file):
        print(f"Error: PO file '{po_file}' does not exist.")
        sys.exit(1)

    # Create a backup of the original file
    backup_file = f"{po_file}_bak"
    shutil.copy2(po_file, backup_file)
    print(f"Created backup of original file at {backup_file}")

    # Read CSV entries into a dictionary for easy lookup
    csv_dict = {}
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            csv_dict[row['msgid']] = row['msgstr']
            print(f"CSV entry: {row['msgid']} -> {row['msgstr']}")

    # Read the PO file
    with open(po_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Process the file line by line
    i = 0
    updated = False
    updated_msgids = []

    # Debug: Print the first 10 lines of the PO file
    print("First 10 lines of PO file:")
    for debug_line in lines[:10]:
        print(f"  {debug_line.strip()}")

    # Debug: Print all msgids in the CSV
    print("All msgids in CSV:")
    for msgid in csv_dict.keys():
        print(f"  '{msgid}'")

    while i < len(lines):
        line = lines[i].strip()

        # Check if this is a msgid line
        if line.startswith('msgid "') and not line.startswith('msgid ""'):
            # Extract the msgid (removing 'msgid "' from start and '"' from end)
            current_msgid = line[7:-1]
            original_i = i

            # Handle multi-line msgid
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith('"') and lines[j].strip().endswith('"'):
                current_msgid += lines[j].strip()[1:-1]
                j += 1
                i = j - 1  # Update i to the last line of the msgid

            # Check if this msgid is in our CSV
            matching_msgid = None
            for csv_msgid in csv_dict.keys():
                # Try exact match first
                if current_msgid == csv_msgid:
                    matching_msgid = csv_msgid
                    break

                # Try normalized match (remove spaces, handle different apostrophes)
                norm_current = current_msgid.replace(' ', '').replace("'", "").replace('"', '')
                norm_csv = csv_msgid.replace(' ', '').replace("'", "").replace('"', '')
                if norm_current == norm_csv:
                    matching_msgid = csv_msgid
                    break

                # Try substring match for specific cases
                if "homepage" in current_msgid and "homepage" in csv_msgid:
                    if "Enter the URL for the journal" in current_msgid and "Enter the URL for the journal" in csv_msgid:
                        matching_msgid = csv_msgid
                        break

            if matching_msgid:
                print(f"Found matching msgid: '{current_msgid}' for CSV entry '{matching_msgid}'")

                # Find the corresponding msgstr line
                msgstr_index = None
                for k in range(i+1, min(i+10, len(lines))):
                    if k < len(lines) and lines[k].strip().startswith('msgstr "'):
                        msgstr_index = k
                        break

                if msgstr_index is not None:
                    # Replace the msgstr
                    new_msgstr = csv_dict[matching_msgid]

                    # First, check for and remove any continuation lines
                    continuation_lines = []
                    next_line_idx = msgstr_index + 1
                    while (next_line_idx < len(lines) and 
                           lines[next_line_idx].strip().startswith('"') and 
                           lines[next_line_idx].strip().endswith('"')):
                        continuation_lines.append(next_line_idx)
                        next_line_idx += 1

                    # Remove continuation lines in reverse order to avoid index shifting
                    for idx in reversed(continuation_lines):
                        lines.pop(idx)

                    # Replace the msgstr line
                    lines[msgstr_index] = f'msgstr "{new_msgstr}"\n'
                    print(f"Updated msgstr for '{current_msgid}' (removed {len(continuation_lines)} continuation lines)")
                    updated = True
                    updated_msgids.append(matching_msgid)
                else:
                    print(f"Warning: Could not find msgstr for msgid '{current_msgid}'")

        i += 1

    # Write the updated content back to the file
    if updated:
        with open(po_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)  # Use writelines instead of join to avoid adding extra newlines
        print(f"Successfully updated translations in {po_file} from {csv_file}")
        print(f"Updated {len(updated_msgids)} out of {len(csv_dict)} entries:")
        for msgid in updated_msgids:
            print(f"  - '{msgid}'")
    else:
        print(f"No translations were updated in {po_file}")

    print(f"Total entries in CSV: {len(csv_dict)}")


def main():
    parser = argparse.ArgumentParser(description='Convert between PO and CSV files for translation purposes')
    parser.add_argument('mode', choices=['po2csv', 'csv2po', 'update_po'], 
                        help='Conversion mode: po2csv, csv2po, or update_po')
    parser.add_argument('input_file', help='Input file path')
    parser.add_argument('output_file', help='Output file path')

    args = parser.parse_args()

    # Check if input file exists
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' does not exist.")
        sys.exit(1)

    # Execute the appropriate function based on mode
    if args.mode == 'po2csv':
        po_to_csv(args.input_file, args.output_file)
    elif args.mode == 'csv2po':
        csv_to_po(args.input_file, args.output_file)
    elif args.mode == 'update_po':
        update_po(args.input_file, args.output_file)


if __name__ == "__main__":
    main()
