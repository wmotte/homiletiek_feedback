#!/usr/bin/env python3
#
# Jan 2026 (w.m.otte@umcutrecht.nl)
#
# Analyse van preken aan de hand van Conceptuele Metafoortheorie (CMT)
# Gebaseerd op het werk van George Lakoff en Mark Johnson
#
#####################################################
import os
import json
import datetime
import re
import argparse
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
DEFAULT_INPUT_FILE = "input/preek_01.txt"
PROMPT_FILE = "prompts/analyze_metafoor.md"
OUTPUT_DIR = "outputs"

def validate_input(text):
    """
    Validates if the sermon text is substantial enough for metaphor analysis.
    Checks for minimum length and basic structure.
    """
    lines = text.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]

    # Check minimum length (at least 50 non-empty lines for meaningful analysis)
    if len(non_empty_lines) < 50:
        raise ValueError(
            f"Preektekst te kort voor metafoor-analyse. "
            f"Gevonden: {len(non_empty_lines)} regels. Minimaal vereist: 50 regels."
        )

    # Estimate word count (rough: avg 8 words per non-empty line)
    estimated_words = sum(len(line.split()) for line in non_empty_lines)
    if estimated_words < 500:
        raise ValueError(
            f"Preektekst te kort voor metafoor-analyse. "
            f"Geschat aantal woorden: {estimated_words}. Minimaal vereist: 500 woorden."
        )

    print(f"✓ Preektekst validatie geslaagd: {len(non_empty_lines)} regels, ~{estimated_words} woorden")
    return True

def analyze_sermon_metaphor(text, prompt_template):
    """
    Calls Gemini API to analyze the sermon using Conceptual Metaphor Theory (CMT).
    """
    if not API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")

    genai.configure(api_key=API_KEY)

    # Use gemini-3-pro-preview for high quality analysis with strong reasoning
    # This model is needed for the comprehensive analytical task
    model = genai.GenerativeModel('gemini-3-pro-preview')

    full_prompt = f"{prompt_template}\n\n--- BEGIN PREEK ---\n{text}\n--- EINDE PREEK ---"

    print("📡 Versturen naar Gemini API voor cognitieve metafooranalyse...")
    print("⚙️  Dit kan 60-90 seconden duren vanwege de complexiteit van de analyse...")

    response = model.generate_content(
        full_prompt,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.3,  # Lower temperature for more analytical/consistent output
        }
    )

    return response.text

def save_output(input_filename, json_content, output_dir=OUTPUT_DIR):
    """
    Saves the JSON content to the specified output directory.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    base_name = os.path.splitext(os.path.basename(input_filename))[0]
    output_filename = f"{output_dir}/{base_name}_metafoor.json"

    try:
        # Ensure json_content is valid JSON string
        parsed_json = json.loads(json_content)

        # Calculate some statistics for confirmation
        total_metaphors = 0
        dominant_domains = []
        if "primaire_analyse" in parsed_json:
            if "metafoor_inventaris" in parsed_json["primaire_analyse"]:
                total_metaphors = len(parsed_json["primaire_analyse"]["metafoor_inventaris"])
            if "dominante_domeinen" in parsed_json["primaire_analyse"]:
                dominant_domains = [d.get("domein_type", "?") for d in parsed_json["primaire_analyse"]["dominante_domeinen"]]

        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(parsed_json, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Analyse succesvol opgeslagen: {output_filename}")
        if total_metaphors > 0:
            print(f"🔍 Aantal geanalyseerde metaforen: {total_metaphors}")
        if dominant_domains:
            print(f"📊 Dominante domeinen: {', '.join(dominant_domains)}")

        return output_filename

    except json.JSONDecodeError as e:
        print(f"❌ Error: content returned was not valid JSON: {e}")
        # Save raw content for debugging
        raw_filename = f"{output_filename}.raw"
        with open(raw_filename, 'w', encoding='utf-8') as f:
            f.write(json_content)
        print(f"💾 Raw content saved for debugging: {raw_filename}")
        return None

def print_summary(output_file):
    """
    Prints a brief summary of the analysis results.
    """
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print("\n" + "="*70)
        print("🔍 SAMENVATTING COGNITIEVE METAFOOR-ANALYSE (CMT)")
        print("="*70)

        if "metadata" in data:
            meta = data["metadata"]
            if "titel_preek" in meta:
                print(f"Preek: {meta['titel_preek']}")
            if "bijbeltekst" in meta:
                print(f"Tekst: {meta['bijbeltekst']}")

        # Print dominant domains
        if "primaire_analyse" in data and "dominante_domeinen" in data["primaire_analyse"]:
            print(f"\n📊 Dominante Metaforische Domeinen:")
            for domein in data["primaire_analyse"]["dominante_domeinen"]:
                dtype = domein.get("domein_type", "?")
                score = domein.get("prominentie_score", 0)
                metafoor = domein.get("conceptuele_metafoor", "")
                bar = "█" * score + "░" * (10 - score)
                print(f"   {dtype:25s} {bar} {score}/10")
                if metafoor:
                    print(f"      → {metafoor}")

        # Print coherence assessment
        if "diagnostische_evaluatie" in data and "coherentie_analyse" in data["diagnostische_evaluatie"]:
            coherence = data["diagnostische_evaluatie"]["coherentie_analyse"]
            if "overall_coherentie" in coherence:
                coh_status = coherence["overall_coherentie"]
                print(f"\n🎯 Metaforische Coherentie: {coh_status}")

            if "incoherentie_punten" in coherence and coherence["incoherentie_punten"]:
                print(f"\n⚠️  Incoherentie-punten gevonden: {len(coherence['incoherentie_punten'])}")
                for punt in coherence["incoherentie_punten"][:2]:  # Show first 2
                    ernst = punt.get("ernst", "?")
                    metafoor_a = punt.get("metafoor_a", "")
                    metafoor_b = punt.get("metafoor_b", "")
                    print(f"   • [{ernst}] {metafoor_a} ↔ {metafoor_b}")

        # Print overall assessment
        if "aanbevelingen" in data and "overall_beoordeling" in data["aanbevelingen"]:
            beoordeling = data["aanbevelingen"]["overall_beoordeling"]
            print(f"\n⭐ Overall Beoordeling: {beoordeling}")

        # Print key strengths and risks
        if "diagnostische_evaluatie" in data:
            if "sterktes" in data["diagnostische_evaluatie"] and data["diagnostische_evaluatie"]["sterktes"]:
                print(f"\n✅ Sterktes: {len(data['diagnostische_evaluatie']['sterktes'])} geïdentificeerd")

            if "risicos" in data["diagnostische_evaluatie"] and data["diagnostische_evaluatie"]["risicos"]:
                print(f"⚠️  Risico's: {len(data['diagnostische_evaluatie']['risicos'])} geïdentificeerd")

        print("="*70 + "\n")

    except Exception as e:
        print(f"⚠️  Kon geen samenvatting genereren: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Analyseer een preek aan de hand van Conceptuele Metafoortheorie (CMT) van Lakoff en Johnson.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Voorbeelden:
  python analyze_metafoor.py
  python analyze_metafoor.py --input input/mijn_preek.txt
  python analyze_metafoor.py -i input/preek_02.txt

Deze tool analyseert de preek op:
  • Dominante metaforische domeinen (Economisch, Medisch, Militair, Relationeel, etc.)
  • Bron→Doel mappings en entailments
  • Metaforische coherentie en incoherentie
  • Levende vs. dode metaforen
  • Cognitieve en theologische implicaties
  • Text world theory en schema disruption
  • Concrete aanbevelingen voor verbetering
        """
    )
    parser.add_argument(
        "-i", "--input",
        type=str,
        default=DEFAULT_INPUT_FILE,
        help="Pad naar het inputbestand (.txt)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=OUTPUT_DIR,
        help=f"Output directory voor JSON bestanden (default: {OUTPUT_DIR})"
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Onderdruk de samenvatting in de console"
    )

    args = parser.parse_args()
    input_file = args.input
    output_dir = args.output_dir

    print("="*70)
    print("🧠 CONCEPTUELE METAFOORTHEORIE (CMT) ANALYSE")
    print("="*70)
    print(f"📖 Input bestand: {input_file}\n")

    try:
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            sermon_text = f.read()

        # Validate input
        print("✓ Validatie wordt uitgevoerd...")
        validate_input(sermon_text)

        # Read prompt template
        print("✓ Prompt template wordt geladen...")
        with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
            prompt_template = f.read()

        # Analyze with Gemini
        print("✓ Analyse wordt gestart met Gemini AI...")
        json_response = analyze_sermon_metaphor(sermon_text, prompt_template)

        # Save output
        output_file = save_output(input_file, json_response, output_dir)

        # Print summary
        if output_file and not args.no_summary:
            print_summary(output_file)

    except FileNotFoundError as e:
        print(f"❌ Bestand niet gevonden: {e}")
        print(f"   Zorg dat het bestand '{input_file}' bestaat.")
    except ValueError as e:
        print(f"❌ Validatie fout: {e}")
    except Exception as e:
        print(f"❌ Er is een onverwachte fout opgetreden: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
