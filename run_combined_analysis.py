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
import glob
from pathlib import Path

# Configuration
OUTPUT_DIR = "outputs"

# All 9 analysis scripts with their identifiers and output suffixes
ANALYSES = [
    {
        "id": "dekker",
        "name": "Dekker (8 Stellingen)",
        "script": "./analyze_sermon_dekker.py",
        "suffix": "",  # Dekker has no suffix in output filename
        "output_pattern": lambda base: f"{base}_*.json"
    },
    {
        "id": "aristoteles",
        "name": "Aristoteles (Retorische Driehoek)",
        "script": "./analyze_aristoteles.py",
        "suffix": "_aristoteles",
        "output_pattern": lambda base: f"{base}_aristoteles_*.json"
    },
    {
        "id": "kolb",
        "name": "Kolb (Leercyclus)",
        "script": "./analyze_kolb_cyclus.py",
        "suffix": "_kolb",
        "output_pattern": lambda base: f"{base}_kolb_*.json"
    },
    {
        "id": "schulz_von_thun",
        "name": "Schulz von Thun (Communicatie Vierkant)",
        "script": "./analyze_schulz_von_thun.py",
        "suffix": "_schulz_von_thun",
        "output_pattern": lambda base: f"{base}_schulz_von_thun_*.json"
    },
    {
        "id": "transactional",
        "name": "Transactionele Analyse (Berne)",
        "script": "./analyze_transactional.py",
        "suffix": "_transactional",
        "output_pattern": lambda base: f"{base}_transactional_*.json"
    },
    {
        "id": "esthetiek",
        "name": "Esthetiek (Schoonheid en Vorm)",
        "script": "./analyze_esthetiek.py",
        "suffix": "_esthetiek",
        "output_pattern": lambda base: f"{base}_esthetiek_*.json"
    },
    {
        "id": "metafoor",
        "name": "Metafoor (Conceptuele Metafoortheorie)",
        "script": "./analyze_metafoor.py",
        "suffix": "_metafoor",
        "output_pattern": lambda base: f"{base}_metafoor_*.json"
    },
    {
        "id": "narratief",
        "name": "Narratief (Greimas Actantieel Model)",
        "script": "./analyze_narratief.py",
        "suffix": "_narratief",
        "output_pattern": lambda base: f"{base}_narratief_*.json"
    },
    {
        "id": "taalhandeling",
        "name": "Taalhandeling (Speech Act Theory)",
        "script": "./analyze_taalhandeling.py",
        "suffix": "_taalhandeling",
        "output_pattern": lambda base: f"{base}_taalhandeling_*.json"
    },
]


def find_latest_output(base_name, analysis):
    """
    Find the most recent output file for a given analysis type.
    """
    pattern = os.path.join(OUTPUT_DIR, analysis["output_pattern"](base_name))
    files = glob.glob(pattern)

    # For dekker (no suffix), we need to exclude other analysis types
    if analysis["id"] == "dekker":
        exclude_suffixes = ["_aristoteles_", "_kolb_", "_schulz_von_thun_",
                          "_transactional_", "_esthetiek_", "_metafoor_",
                          "_narratief_", "_taalhandeling_"]
        files = [f for f in files if not any(s in f for s in exclude_suffixes)]

    if not files:
        return None

    # Sort by modification time, most recent first
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]


def run_analysis(input_file, analysis, timeout=300):
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
        # Run the analysis script with --no-summary flag if available
        cmd = [sys.executable, script, "--input", input_file, "--no-summary"]
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
  python run_combined_analysis.py --i input/mijn_preek.txt
  python run_combined_analysis.py -i input/preek_02.txt --output-dir outputs
  python run_combined_analysis.py -i input/preek.txt --skip-existing

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
        "--skip-existing",
        action="store_true",
        help="Sla analyses over waarvoor al een output bestand bestaat"
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

        # Check if we should skip existing
        if args.skip_existing:
            existing_file = find_latest_output(base_name, analysis)
            if existing_file:
                print(f"\nSkipping {analysis_name}: output already exists at {existing_file}")
                results["skipped"].append(analysis_id)

                # Load existing data
                try:
                    with open(existing_file, 'r', encoding='utf-8') as f:
                        analyses_data[analysis_id] = json.load(f)
                except Exception as e:
                    warnings.append(f"Kon bestaand bestand niet laden voor {analysis_name}: {e}")
                continue

        # Run the analysis
        success, error_msg = run_analysis(input_file, analysis, timeout=args.timeout)

        if success:
            # Find the output file
            output_file = find_latest_output(base_name, analysis)
            if output_file:
                print(f"Analyse geslaagd: {output_file}")
                results["successful"].append(analysis_id)

                # Load the analysis data
                try:
                    with open(output_file, 'r', encoding='utf-8') as f:
                        analyses_data[analysis_id] = json.load(f)
                except Exception as e:
                    warnings.append(f"Kon output niet laden voor {analysis_name}: {e}")
                    results["failed"].append(analysis_id)
            else:
                warnings.append(f"Analyse {analysis_name} voltooide maar output bestand niet gevonden")
                results["failed"].append(analysis_id)
        else:
            print(f"WAARSCHUWING: Analyse {analysis_name} mislukt: {error_msg}")
            warnings.append(f"Analyse {analysis_name} mislukt: {error_msg}")
            results["failed"].append(analysis_id)

    # Create combined JSON
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
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
    combined_filename = os.path.join(output_dir, f"{base_name}_combined_{timestamp}.json")
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
