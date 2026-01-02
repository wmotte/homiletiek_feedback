#!/usr/bin/env python3
#
# Dec 2025/Jan 2026 (w.m.otte@umcutrecht.nl)
#
# Analyse van preken aan de hand van Kolbs Leercyclus
# Gebaseerd op de homiletische toepassing door Kenton Anderson en Richard Osmer
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
PROMPT_FILE = "prompts/analyze_kolb_cyclus.md"
OUTPUT_DIR = "outputs"

def validate_input(text):
    """
    Validates if the sermon text is substantial enough for Kolb analysis.
    Checks for minimum length and basic structure.
    """
    lines = text.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]

    # Check minimum length (at least 50 non-empty lines for meaningful analysis)
    if len(non_empty_lines) < 50:
        raise ValueError(
            f"Preektekst te kort voor Kolb-analyse. "
            f"Gevonden: {len(non_empty_lines)} regels. Minimaal vereist: 50 regels."
        )

    # Estimate word count (rough: avg 8 words per non-empty line)
    estimated_words = sum(len(line.split()) for line in non_empty_lines)
    if estimated_words < 500:
        raise ValueError(
            f"Preektekst te kort voor Kolb-analyse. "
            f"Geschat aantal woorden: {estimated_words}. Minimaal vereist: 500 woorden."
        )

    print(f"✓ Preektekst validatie geslaagd: {len(non_empty_lines)} regels, ~{estimated_words} woorden")
    return True

def analyze_sermon_kolb(text, prompt_template):
    """
    Calls Gemini API to analyze the sermon using Kolb's Learning Cycle framework.
    """
    if not API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")

    genai.configure(api_key=API_KEY)

    # Use gemini-3-pro-preview for high quality analysis with strong reasoning
    # This model is needed for the comprehensive analytical task
    model = genai.GenerativeModel('gemini-3-pro-preview')

    full_prompt = f"{prompt_template}\n\n--- BEGIN PREEK ---\n{text}\n--- EINDE PREEK ---"

    print("📡 Versturen naar Gemini API voor analyse...")
    print("⚙️  Dit kan 30-60 seconden duren vanwege de complexiteit van de analyse...")

    response = model.generate_content(
        full_prompt,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.4,  # Slightly lower for more consistent analytical output
        }
    )

    return response.text

def save_output(input_filename, json_content):
    """
    Saves the JSON content to the outputs directory with a timestamp.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(input_filename))[0]
    output_filename = f"{OUTPUT_DIR}/{base_name}_kolb_{timestamp}.json"

    try:
        # Ensure json_content is valid JSON string
        parsed_json = json.loads(json_content)

        # Calculate some statistics for confirmation
        total_scores = []
        if "kolb_fasen_analyse" in parsed_json:
            for fase in parsed_json["kolb_fasen_analyse"].values():
                if "score" in fase:
                    total_scores.append(fase["score"])

        avg_score = sum(total_scores) / len(total_scores) if total_scores else 0

        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(parsed_json, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Analyse succesvol opgeslagen: {output_filename}")
        if avg_score > 0:
            print(f"📊 Gemiddelde score Kolb-fasen: {avg_score:.1f}/10")

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
        print("📋 SAMENVATTING KOLB-ANALYSE")
        print("="*70)

        if "metadata" in data:
            meta = data["metadata"]
            if "titel_preek" in meta:
                print(f"Preek: {meta['titel_preek']}")
            if "bijbeltekst" in meta:
                print(f"Tekst: {meta['bijbeltekst']}")

        if "totaalbeeld" in data:
            totaal = data["totaalbeeld"]
            if "overall_kolb_score" in totaal:
                score = totaal["overall_kolb_score"]
                print(f"\n⭐ Overall Kolb Score: {score}/10")

            if "primaire_homiletische_stijl" in totaal:
                print(f"🎯 Primaire stijl: {totaal['primaire_homiletische_stijl']}")

            if "primaire_leerstijl_aangesproken" in totaal:
                print(f"🎓 Primaire leerstijl: {totaal['primaire_leerstijl_aangesproken']}")

        # Print Kolb fase scores
        if "kolb_fasen_analyse" in data:
            print(f"\n📊 Scores per Kolb-fase:")
            fase_namen = {
                "fase_1_concrete_ervaring": "Concrete Ervaring (CE)",
                "fase_2_reflectieve_observatie": "Reflectieve Observatie (RO)",
                "fase_3_abstracte_conceptualisering": "Abstracte Conceptualisering (AC)",
                "fase_4_actief_experimenteren": "Actief Experimenteren (AE)"
            }
            for key, naam in fase_namen.items():
                if key in data["kolb_fasen_analyse"]:
                    score = data["kolb_fasen_analyse"][key].get("score", 0)
                    bar = "█" * score + "░" * (10 - score)
                    print(f"   {naam:35s} {bar} {score}/10")

        print("="*70 + "\n")

    except Exception as e:
        print(f"⚠️  Kon geen samenvatting genereren: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Analyseer een preek aan de hand van Kolbs Leercyclus en de homiletische toepassing door Anderson en Osmer.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Voorbeelden:
  python analyze_kolb_cyclus.py
  python analyze_kolb_cyclus.py --input input/mijn_preek.txt
  python analyze_kolb_cyclus.py -i input/preek_02.txt

Deze tool analyseert de preek op:
  • De 4 fasen van Kolb (CE, RO, AC, AE)
  • De 4 structuren van Anderson (Declaratief, Pragmatisch, Narratief, Visionair)
  • De 4 taken van Osmer (Descriptief, Interpretatief, Normatief, Pragmatisch)
  • Welke leerstijlen worden aangesproken
  • De integraliteit van de cyclus (Homiletic Window)
        """
    )
    parser.add_argument(
        "-i", "--input",
        type=str,
        default=DEFAULT_INPUT_FILE,
        help="Pad naar het inputbestand (.txt)"
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Onderdruk de samenvatting in de console"
    )

    args = parser.parse_args()
    input_file = args.input

    print("="*70)
    print("🔍 KOLB LEERCYCLUS ANALYSE VOOR HOMILETIEK")
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
        json_response = analyze_sermon_kolb(sermon_text, prompt_template)

        # Save output
        output_file = save_output(input_file, json_response)

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
