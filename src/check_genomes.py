#!/usr/bin/env python3

"""
Checks the NCBI RefSeq database for the number of available "complete genomes"
for a given bacterial species name using the NCBI Datasets command-line tool.
"""

import subprocess
import json
import argparse
import sys
from typing import Optional # For type hinting

def check_genome_count(species_name: str) -> Optional[int]:
    """
    Queries NCBI using the 'datasets' tool to find the count of complete
    RefSeq genomes for a given species.

    Args:
        species_name: The scientific name of the species (e.g., "Escherichia coli").

    Returns:
        The number of complete RefSeq genomes found, or None if an error occurred
        or the species was not found. Returns 0 if the query was successful but
        no matching genomes were found.
    """
    print(f"Checking RefSeq for complete genomes of: '{species_name}'")

    command = [
        'datasets',          # The NCBI datasets command-line tool
        'summary',           # Get summary information
        'genome',            # For genomes
        'taxon',             # Query by taxon (species name)
        species_name,        # The actual species name
        '--report', 'counts',# Request just the counts report
        '--assembly-level', 'complete', # Filter for complete genomes only
        '--assembly-source', 'RefSeq'    # Filter for RefSeq assemblies
    ]

    try:
        # Run the command, capture output, decode as text
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False # Don't raise exception on non-zero exit code immediately
        )

        # Check if the command executed successfully
        if result.returncode != 0:
            print(f"Error running NCBI datasets command:", file=sys.stderr)
            print(f"Command: {' '.join(command)}", file=sys.stderr)
            print(f"Return Code: {result.returncode}", file=sys.stderr)
            print(f"Stderr: {result.stderr.strip()}", file=sys.stderr)
            return None

        # Check if we got any output
        if not result.stdout.strip():
             print(f"No output received from NCBI datasets for '{species_name}'. "
                   "Perhaps the species name is misspelled or has no matching assemblies?", file=sys.stderr)
             # Often this means 0 results if the command itself didn't error
             return 0

        # Parse the JSON output
        try:
            data = json.loads(result.stdout)
            # The '--report counts' output should have a 'total_count' field
            count = data.get('total_count', 0) # Default to 0 if key missing
            # Ensure it's an integer
            if isinstance(count, int):
                return count
            else:
                 print(f"Warning: 'total_count' field was not an integer. Value: {count}", file=sys.stderr)
                 # Try to convert if possible, otherwise treat as 0 or error
                 try:
                     return int(count)
                 except (ValueError, TypeError):
                      print(f"Could not convert 'total_count' to integer.", file=sys.stderr)
                      return 0 # Or None, depending on desired strictness

        except json.JSONDecodeError:
            print(f"Error: Failed to decode JSON output from NCBI datasets.", file=sys.stderr)
            print(f"Received output:\n{result.stdout}", file=sys.stderr)
            return None
        except KeyError:
             print(f"Error: 'total_count' key not found in NCBI datasets output.", file=sys.stderr)
             print(f"Received JSON data:\n{data}", file=sys.stderr)
             # This might indicate 0 assemblies if the structure is different
             # Let's check for other possible count fields or assume 0
             if data.get("count", 0) == 0 and not data.get("reports"): # datasets sometimes returns empty report list for 0
                 print("Interpreting lack of 'total_count' as 0 assemblies found.")
                 return 0
             return None # Indicate an unexpected format error

    except FileNotFoundError:
        print(f"Error: The 'datasets' command was not found.", file=sys.stderr)
        print("Please ensure the NCBI Datasets command line tool is installed and in your PATH.", file=sys.stderr)
        print("(It should be included via the conda environment 'ncbi-datasets-cli')", file=sys.stderr)
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return None

def main():
    """
    Main function to parse arguments and run the genome check.
    """
    parser = argparse.ArgumentParser(
        description='Check NCBI RefSeq for the number of complete genomes for a given species.'
    )
    parser.add_argument(
        'species_name',
        type=str,
        help='The scientific name of the species (e.g., "Escherichia coli"). Please enclose in quotes if it contains spaces.'
    )

    args = parser.parse_args()

    genome_count = check_genome_count(args.species_name)

    if genome_count is not None:
        print(f"Found {genome_count} complete RefSeq genome(s) for '{args.species_name}'.")
        # Exit with 0 on success, even if count is 0
        sys.exit(0)
    else:
        print(f"Failed to retrieve genome count for '{args.species_name}'.")
        # Exit with a non-zero status code to indicate failure
        sys.exit(1)

if __name__ == "__main__":
    main()
