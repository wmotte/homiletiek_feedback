#!/usr/bin/env python3
#
# Jan 2026 (w.m.otte@umcutrecht.nl)
#
# Runs all 9 domain analyses on a single preek input file,
# stores individual JSONs, and combines them into a single combined JSON.
# The combined JSON includes the source text and warnings for failed analyses.
#
#####################################################
import os
import sys
import json
import datetime
import argparse
import subprocess

# Configuration
OUTPUT_DIR = "outputs"

# All 9 analysis scripts with their identifiers and output suffixes
ANALYSES = [
    {
        "id": "dekker",
        "name": "Dekker (8 Stellingen)",
        "script": "./analyze_sermon_dekker.py",
        "suffix": "_dekker",
    },
    {
        "id": "aristoteles",
        "name": "Aristoteles (Retorische Driehoek)",
        "script": "./analyze_aristoteles.py",
        "suffix": "_aristoteles",
    },
    {
        "id": "kolb",
        "name": "Kolb (Leercyclus)",
        "script": "./analyze_kolb_cyclus.py",
        "suffix": "_kolb",
    },
    {
        "id": "schulz_von_thun",
        "name": "Schulz von Thun (Communicatie Vierkant)",
        "script": "./analyze_schulz_von_thun.py",
        "suffix": "_schulz_von_thun",
    },
    {
        "id": "transactional",
        "name": "Transactionele Analyse (Berne)",
        "script": "./analyze_transactional.py",
        "suffix": "_transactional",
    },
    {
        "id": "esthetiek",
        "name": "Esthetiek (Schoonheid en Vorm)",
        "script": "./analyze_esthetiek.py",
        "suffix": "_esthetiek",
    },
    {
        "id": "metafoor",
        "name": "Metafoor (Conceptuele Metafoortheorie)",
        "script": "./analyze_metafoor.py",
        "suffix": "_metafoor",
    },
    {
        "id": "narratief",
        "name": "Narratief (Greimas Actantieel Model)",
        "script": "./analyze_narratief.py",
        "suffix": "_narratief",
    },
    {
        "id": "taalhandeling",
        "name": "Taalhandeling (Speech Act Theory)",
        "script": "./analyze_taalhandeling.py",
        "suffix": "_taalhandeling",
    },
]


def get_output_file(base_name, analysis, output_dir):
    """
    Get the expected output file path for a given analysis type.
    Output filenames are now fixed (no timestamps).
    """
    return os.path.join(output_dir, f"{base_name}{analysis['suffix']}.json")


def run_analysis(input_file, analysis, output_dir, timeout=300):
    """
    Run a single analysis script and return success status.
    """
    script = analysis["script"]
    name = analysis["name"]

    if not os.path.exists(script):
        return False, f"Script niet gevonden: {script}"

    print(f"\n{'='*60}")
    print(f"Running: {name}")
    print(f"{'='*60}")

    try:
        # Run the analysis script with --output-dir and --no-summary flags
        cmd = [sys.executable, script, "--input", input_file, "--output-dir", output_dir, "--no-summary"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            print(f"STDERR: {result.stderr}")
            return False, f"Script retourneerde foutcode {result.returncode}"

        print(result.stdout)
        return True, None

    except subprocess.TimeoutExpired:
        return False, f"Timeout na {timeout} seconden"
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(
        description="Voer alle 9 domeinanalyses uit op een preektekst en combineer de resultaten.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Voorbeelden:
  python run_combined_analysis.py -i input/mijn_preek.txt
  python run_combined_analysis.py -i input/preek_02.txt --output-dir my_output
  python run_combined_analysis.py -i input/preek.txt --force  # heranalyse alles

Deze tool voert alle 9 analyses uit:
  1. Dekker (8 Stellingen)
  2. Aristoteles (Retorische Driehoek)
  3. Kolb (Leercyclus)
  4. Schulz von Thun (Communicatie Vierkant)
  5. Transactionele Analyse (Berne)
  6. Esthetiek (Schoonheid en Vorm)
  7. Metafoor (Conceptuele Metafoortheorie)
  8. Narratief (Greimas Actantieel Model)
  9. Taalhandeling (Speech Act Theory)

Output:
  - Individuele JSON-bestanden per analyse in de outputs directory
  - Een gecombineerd JSON-bestand met alle analyses en de brontekst
        """
    )
    parser.add_argument(
        "-i", "--i",
        type=str,
        required=True,
        help="Pad naar het preek inputbestand (.txt)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=OUTPUT_DIR,
        help=f"Output directory voor JSON bestanden (default: {OUTPUT_DIR})"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Voer alle analyses opnieuw uit, ook als output al bestaat"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout per analyse in seconden (default: 300)"
    )

    args = parser.parse_args()
    input_file = args.i
    output_dir = args.output_dir

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    print("="*70)
    print("GECOMBINEERDE HOMILETISCHE ANALYSE")
    print("="*70)
    print(f"Input bestand: {input_file}")
    print(f"Output directory: {output_dir}")
    print(f"Aantal analyses: {len(ANALYSES)}")
    print("="*70)

    # Read the source text
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            source_text = f.read()
        print(f"Brontekst geladen: {len(source_text)} karakters")
    except FileNotFoundError:
        print(f"FOUT: Inputbestand niet gevonden: {input_file}")
        sys.exit(1)
    except Exception as e:
        print(f"FOUT: Kon inputbestand niet lezen: {e}")
        sys.exit(1)

    # Get base name for output files
    base_name = os.path.splitext(os.path.basename(input_file))[0]

    # Track results
    results = {
        "successful": [],
        "failed": [],
        "skipped": []
    }
    analyses_data = {}
    warnings = []

    # Run each analysis
    for analysis in ANALYSES:
        analysis_id = analysis["id"]
        analysis_name = analysis["name"]
        expected_output = get_output_file(base_name, analysis, output_dir)

        # Check if output already exists
        output_exists = os.path.exists(expected_output)

        # Skip if output exists (unless --force is set)
        if output_exists and not args.force:
            print(f"\nSkipping {analysis_name}: output already exists at {expected_output}")
            results["skipped"].append(analysis_id)

            # Load existing data
            try:
                with open(expected_output, 'r', encoding='utf-8') as f:
                    analyses_data[analysis_id] = json.load(f)
            except Exception as e:
                warnings.append(f"Kon bestaand bestand niet laden voor {analysis_name}: {e}")
            continue

        # Run the analysis
        success, error_msg = run_analysis(input_file, analysis, output_dir, timeout=args.timeout)

        if success:
            # Check the output file
            if os.path.exists(expected_output):
                print(f"Analyse geslaagd: {expected_output}")
                results["successful"].append(analysis_id)

                # Load the analysis data
                try:
                    with open(expected_output, 'r', encoding='utf-8') as f:
                        analyses_data[analysis_id] = json.load(f)
                except Exception as e:
                    warnings.append(f"Kon output niet laden voor {analysis_name}: {e}")
                    results["failed"].append(analysis_id)
            else:
                warnings.append(f"Analyse {analysis_name} voltooide maar output bestand niet gevonden: {expected_output}")
                results["failed"].append(analysis_id)
        else:
            print(f"WAARSCHUWING: Analyse {analysis_name} mislukt: {error_msg}")
            warnings.append(f"Analyse {analysis_name} mislukt: {error_msg}")
            results["failed"].append(analysis_id)

    # Create combined JSON (no timestamp in filename)
    combined_output = {
        "metadata": {
            "type": "combined_analysis",
            "version": "1.0",
            "datum_analyse": datetime.datetime.now().isoformat(),
            "input_bestand": os.path.basename(input_file),
            "aantal_analyses_geslaagd": len(results["successful"]),
            "aantal_analyses_mislukt": len(results["failed"]),
            "aantal_analyses_overgeslagen": len(results["skipped"])
        },
        "source": source_text,
        "analyses": analyses_data,
        "warnings": warnings if warnings else [],
        "available_analyses": list(analyses_data.keys())
    }

    # Save combined JSON
    combined_filename = os.path.join(output_dir, f"{base_name}_combined.json")
    try:
        with open(combined_filename, 'w', encoding='utf-8') as f:
            json.dump(combined_output, f, indent=2, ensure_ascii=False)
        print(f"\nGecombineerd bestand opgeslagen: {combined_filename}")
    except Exception as e:
        print(f"FOUT: Kon gecombineerd bestand niet opslaan: {e}")
        sys.exit(1)

    # Print summary
    print("\n" + "="*70)
    print("SAMENVATTING")
    print("="*70)
    print(f"Geslaagd:     {len(results['successful'])}/{len(ANALYSES)}")
    print(f"Mislukt:      {len(results['failed'])}/{len(ANALYSES)}")
    print(f"Overgeslagen: {len(results['skipped'])}/{len(ANALYSES)}")

    if results["successful"]:
        print(f"\nGeslaagde analyses: {', '.join(results['successful'])}")

    if results["failed"]:
        print(f"\nMislukte analyses: {', '.join(results['failed'])}")
        print("\nWAARSCHUWINGEN:")
        for w in warnings:
            print(f"  - {w}")

    print(f"\nGecombineerd bestand: {combined_filename}")
    print("="*70)

    # Exit with error if any analyses failed
    if results["failed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
