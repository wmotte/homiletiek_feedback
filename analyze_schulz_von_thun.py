#!/usr/bin/env python3
#
# Jan 2026 (w.m.otte@umcutrecht.nl)
#
# Analyse van preken aan de hand van het Vier-Zijden-Model van Schulz von Thun
# Zakelijke inhoud, Zelf-onthulling, Relatie en Appel
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
PROMPT_FILE = "prompts/analyze_schulz_von_thun.md"
OUTPUT_DIR = "outputs"

def validate_input(text):
    """
    Validates if the sermon text is substantial enough for rhetorical analysis.
    Checks for minimum length and basic structure.
    """
    lines = text.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]

    # Check minimum length (at least 50 non-empty lines for meaningful analysis)
    if len(non_empty_lines) < 50:
        raise ValueError(
            f"Preektekst te kort voor analyse. "
            f"Gevonden: {len(non_empty_lines)} regels. Minimaal vereist: 50 regels."
        )

    # Estimate word count (rough: avg 8 words per non-empty line)
    estimated_words = sum(len(line.split()) for line in non_empty_lines)
    if estimated_words < 500:
        raise ValueError(
            f"Preektekst te kort voor analyse. "
            f"Geschat aantal woorden: {estimated_words}. Minimaal vereist: 500 woorden."
        )

    print(f"✓ Preektekst validatie geslaagd: {len(non_empty_lines)} regels, ~{estimated_words} woorden")
    return True

def analyze_sermon_schulz(text, prompt_template):
    """
    Calls Gemini API to analyze the sermon using Schulz von Thun's framework.
    """
    if not API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")

    genai.configure(api_key=API_KEY)

    # Use gemini-3-pro-preview for high quality analysis
    model = genai.GenerativeModel('gemini-3-pro-preview')

    full_prompt = f"{prompt_template}\n\n--- BEGIN PREEK ---\n{text}\n--- EINDE PREEK ---"

    print("📡 Versturen naar Gemini API voor Schulz von Thun analyse...")
    print("⚙️  Dit kan 30-60 seconden duren...")

    response = model.generate_content(
        full_prompt,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.4,
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
    output_filename = f"{output_dir}/{base_name}_schulz_von_thun.json"

    try:
        # Ensure json_content is valid JSON string
        parsed_json = json.loads(json_content)

        # Calculate some statistics for confirmation
        total_scores = []
        if "schulz_von_thun_analyse" in parsed_json:
            sides = parsed_json["schulz_von_thun_analyse"]
            for side_key in ["zakelijk_inhoud_blauw", "zelf_onthulling_groen", "relatie_aspect_geel", "appel_aspect_rood"]:
                if side_key in sides and "score" in sides[side_key]:
                    total_scores.append(sides[side_key]["score"])

        avg_score = sum(total_scores) / len(total_scores) if total_scores else 0

        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(parsed_json, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Analyse succesvol opgeslagen: {output_filename}")
        if avg_score > 0:
            print(f"📊 Gemiddelde score over 4 zijden: {avg_score:.1f}/10")

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
        print("📋 SAMENVATTING SCHULZ VON THUN ANALYSE")
        print("="*70)

        if "metadata" in data:
            meta = data["metadata"]
            if "titel_preek" in meta:
                print(f"Preek: {meta['titel_preek']}")
            if "bijbeltekst" in meta:
                print(f"Tekst: {meta['bijbeltekst']}")

        if "totaalbeeld" in data:
            totaal = data["totaalbeeld"]
            if "overall_communicatie_score" in totaal:
                score = totaal["overall_communicatie_score"]
                print(f"\n⭐ Overall Communicatie Score: {score}/10")

        if "congruentie_en_interactie" in data:
            interactie = data["congruentie_en_interactie"]
            if "dominante_zijde" in interactie:
                print(f"🎯 Dominante zijde: {interactie['dominante_zijde']}")
            if "verwaarloosde_zijde" in interactie:
                print(f"⚠️ Verwaarloosde zijde: {interactie['verwaarloosde_zijde']}")

        # Print 4 Zijden scores
        if "schulz_von_thun_analyse" in data:
            print(f"\n📊 Scores per Zijde:")
            sides_map = {
                "zakelijk_inhoud_blauw": "Zakelijk (Blauw)",
                "zelf_onthulling_groen": "Zelf-onthulling (Groen)",
                "relatie_aspect_geel": "Relatie (Geel)",
                "appel_aspect_rood": "Appel (Rood)"
            }
            
            sides = data["schulz_von_thun_analyse"]
            for key, naam in sides_map.items():
                if key in sides:
                    score = sides[key].get("score", 0)
                    # Handle float scores for the bar visualization
                    display_score = int(round(float(score)))
                    bar = "█" * display_score + "░" * (10 - display_score)
                    print(f"   {naam:30s} {bar} {score}/10")

        if "congruentie_en_interactie" in data and "congruentie_analyse" in data["congruentie_en_interactie"]:
             print(f"\n⚖️  Congruentie: {data['congruentie_en_interactie']['congruentie_analyse'][:100]}...")

        print("="*70 + "\n")

    except Exception as e:
        print(f"⚠️  Kon geen samenvatting genereren: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Analyseer een preek aan de hand van het Vier-Zijden-Model van Schulz von Thun.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Voorbeelden:
  python analyze_schulz_von_thun.py
  python analyze_schulz_von_thun.py --input input/mijn_preek.txt

Deze tool analyseert de preek op:
  • Zakelijk (Blauw): Feiten, inhoud, exegese
  • Zelf-onthulling (Groen): Authenticiteit, persoonlijkheid
  • Relatie (Geel): Houding tot de gemeente
  • Appel (Rood): Oproep tot actie of geloof
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
    print("📡 SCHULZ VON THUN COMMUNICATIE ANALYSE")
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
        json_response = analyze_sermon_schulz(sermon_text, prompt_template)

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
