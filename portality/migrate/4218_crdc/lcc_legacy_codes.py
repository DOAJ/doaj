#!/usr/bin/env python3

"""Generate CRDC-structured rows for legacy LCC codes.

This script reads an ``lcc2crdc.csv`` file and selects LC codes where no
CRDC code is present. It then writes an output CSV using the same structure
as the CRDC hierarchy file.
"""

import argparse
import csv


OUTPUT_HEADER = [
	"Level",
	"Hierarchical structure",
	"Code",
	"Parent",
	"Class title",
	"Class definition",
]


def find_unmapped_lc_codes(input_path):
	"""Return (LC code, class term) pairs with no CRDC mapping, preserving input order."""
	lc_codes = []
	seen = set()

	with open(input_path, "r", newline="", encoding="utf-8") as f:
		reader = csv.DictReader(f)
		for row in reader:
			lc_code = (row.get("LC code") or "").strip()
			crdc_code = (row.get("CRDC code") or "").strip()
			class_term = (row.get("Class Term") or "").strip()
			if lc_code and not crdc_code and lc_code not in seen:
				seen.add(lc_code)
				lc_codes.append((lc_code, class_term))

	return lc_codes


def write_output(output_path, lc_codes):
	"""Write legacy LCC hierarchy rows in CRDC CSV format."""
	with open(output_path, "w", newline="", encoding="utf-8") as f:
		writer = csv.writer(f)
		writer.writerow(OUTPUT_HEADER)

		# Root container row for legacy LCC entries.
		writer.writerow(
			[
				"1",
				"Division",
				"LCC",
				"",
				"LCC",
				"LCC Legacy Container",
			]
		)

		for lc_code, class_term in lc_codes:
			writer.writerow(
				[
					"2",
					"Subclass (Field)",
					lc_code,
					"LCC",
					class_term,
					class_term,
				]
			)


def main():
	parser = argparse.ArgumentParser(
		description=(
			"Generate a CRDC-structured CSV containing LC codes with no CRDC mapping."
		)
	)
	parser.add_argument("input_csv", help="Path to lcc2crdc.csv")
	parser.add_argument("output_csv", help="Path to write the output CSV")
	args = parser.parse_args()

	lc_codes = find_unmapped_lc_codes(args.input_csv)
	write_output(args.output_csv, lc_codes)


if __name__ == "__main__":
	main()

