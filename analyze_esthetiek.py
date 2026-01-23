#!/usr/bin/env python3
#
# Jan 2026 (w.m.otte@umcutrecht.nl)
#
# Analyse van preken aan de hand van de Esthetische Wending in de Homiletiek
# Gebaseerd op het werk van Johan Cilliers, Ciska Stark, Gerrit Immink,
# Paul Scott Wilson, Thomas Long, en anderen
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
PROMPT_FILE = "prompts/analyze_esthetiek.md"
OUTPUT_DIR = "outputs"

def validate_input(text):
    """
    Validates if the sermon text is substantial enough for aesthetic analysis.
    Checks for minimum length and basic structure.
    """
    lines = text.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]

    # Check minimum length (at least 50 non-empty lines for meaningful analysis)
    if len(non_empty_lines) < 50:
        raise ValueError(
            f"Preektekst te kort voor esthetische analyse. "
            f"Gevonden: {len(non_empty_lines)} regels. Minimaal vereist: 50 regels."
        )

    # Estimate word count (rough: avg 8 words per non-empty line)
    estimated_words = sum(len(line.split()) for line in non_empty_lines)
    if estimated_words < 500:
        raise ValueError(
            f"Preektekst te kort voor esthetische analyse. "
            f"Geschat aantal woorden: {estimated_words}. Minimaal vereist: 500 woorden."
        )

    print(f"✓ Preektekst validatie geslaagd: {len(non_empty_lines)} regels, ~{estimated_words} woorden")
    return True

def analyze_sermon_esthetiek(text, prompt_template):
    """
    Calls Gemini API to analyze the sermon using aesthetic homiletic framework.
    """
    if not API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")

    genai.configure(api_key=API_KEY)

    # Use gemini-3-pro-preview for high quality aesthetic analysis
    # This model is needed for nuanced understanding of literary and aesthetic elements
    model = genai.GenerativeModel('gemini-3-pro-preview')

    full_prompt = f"{prompt_template}\n\n--- BEGIN PREEK ---\n{text}\n--- EINDE PREEK ---"

    print("📡 Versturen naar Gemini API voor esthetische analyse...")
    print("⚙️  Dit kan 30-60 seconden duren vanwege de diepgang van de analyse...")

    response = model.generate_content(
        full_prompt,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.4,  # Slightly lower for more consistent analytical output
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
    output_filename = f"{output_dir}/{base_name}_esthetiek.json"

    try:
        # Ensure json_content is valid JSON string
        parsed_json = json.loads(json_content)

        # Calculate some statistics for confirmation
        total_scores = []

        # Collect scores from both domains (A and B only)
        if "domein_a_poetica_van_de_taal" in parsed_json:
            domein_a = parsed_json["domein_a_poetica_van_de_taal"]
            for criterium_key in ["criterium_a1_beeldend_taalgebruik",
                                  "criterium_a2_zorgvuldigheid_en_precisie",
                                  "criterium_a3_muzikaliteit_en_ritme"]:
                if criterium_key in domein_a and "score" in domein_a[criterium_key]:
                    total_scores.append(domein_a[criterium_key]["score"])

        if "domein_b_dramaturgie_van_de_structuur" in parsed_json:
            domein_b = parsed_json["domein_b_dramaturgie_van_de_structuur"]
            for criterium_key in ["criterium_b1_narratieve_spanningsboog",
                                  "criterium_b2_integratie_tekst_en_context",
                                  "criterium_b3_openheid_vs_geslotenheid"]:
                if criterium_key in domein_b and "score" in domein_b[criterium_key]:
                    total_scores.append(domein_b[criterium_key]["score"])

        avg_score = sum(total_scores) / len(total_scores) if total_scores else 0

        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(parsed_json, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Analyse succesvol opgeslagen: {output_filename}")
        if avg_score > 0:
            print(f"📊 Gemiddelde esthetische score: {avg_score:.1f}/10")

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
        print("🎨 SAMENVATTING ESTHETISCHE ANALYSE")
        print("="*70)

        if "metadata" in data:
            meta = data["metadata"]
            if "titel_preek" in meta:
                print(f"Preek: {meta['titel_preek']}")
            if "bijbeltekst" in meta:
                print(f"Tekst: {meta['bijbeltekst']}")

        if "totaalbeeld_esthetiek" in data:
            totaal = data["totaalbeeld_esthetiek"]
            if "overall_esthetische_score" in totaal:
                score = totaal["overall_esthetische_score"]
                print(f"\n⭐ Overall Esthetische Score: {score}/10")

            if "primaire_esthetische_stijl" in totaal:
                print(f"🎯 Primaire stijl: {totaal['primaire_esthetische_stijl']}")

        # Print Domein scores
        print(f"\n📊 Scores per Domein:")

        if "domein_a_poetica_van_de_taal" in data:
            domein_a = data["domein_a_poetica_van_de_taal"]
            if "gemiddelde_score_taal" in domein_a:
                score = domein_a["gemiddelde_score_taal"]
                display_score = int(round(float(score)))
                bar = "█" * display_score + "░" * (10 - display_score)
                print(f"   {'Poëtica van de Taal':30s} {bar} {score}/10")

        if "domein_b_dramaturgie_van_de_structuur" in data:
            domein_b = data["domein_b_dramaturgie_van_de_structuur"]
            if "gemiddelde_score_structuur" in domein_b:
                score = domein_b["gemiddelde_score_structuur"]
                display_score = int(round(float(score)))
                bar = "█" * display_score + "░" * (10 - display_score)
                print(f"   {'Dramaturgie Structuur':30s} {bar} {score}/10")

        # Print Anti-kitsch and Space for Grace scores
        if "kitsch_diagnose" in data and "anti_kitsch_score" in data["kitsch_diagnose"]:
            anti_kitsch = data["kitsch_diagnose"]["anti_kitsch_score"]
            display_score = int(round(float(anti_kitsch)))
            bar = "█" * display_score + "░" * (10 - display_score)
            print(f"   {'Anti-Kitsch':30s} {bar} {anti_kitsch}/10")

        if "ruimte_voor_genade_analyse" in data and "ruimte_score" in data["ruimte_voor_genade_analyse"]:
            ruimte = data["ruimte_voor_genade_analyse"]["ruimte_score"]
            display_score = int(round(float(ruimte)))
            bar = "█" * display_score + "░" * (10 - display_score)
            print(f"   {'Ruimte voor Genade':30s} {bar} {ruimte}/10")

        # Print top 3 strengths and improvement points
        if "totaalbeeld_esthetiek" in data:
            totaal = data["totaalbeeld_esthetiek"]
            if "sterke_punten_top_3" in totaal:
                print(f"\n✨ Top 3 Sterke Punten:")
                for i, punt in enumerate(totaal["sterke_punten_top_3"][:3], 1):
                    print(f"   {i}. {punt[:80]}...")

            if "verbeterpunten_top_3" in totaal:
                print(f"\n🔧 Top 3 Verbeterpunten:")
                for i, punt in enumerate(totaal["verbeterpunten_top_3"][:3], 1):
                    print(f"   {i}. {punt[:80]}...")

        print("="*70 + "\n")

    except Exception as e:
        print(f"⚠️  Kon geen samenvatting genereren: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Analyseer een preek aan de hand van de Esthetische Wending in de Homiletiek.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Voorbeelden:
  python analyze_esthetiek.py
  python analyze_esthetiek.py --input input/mijn_preek.txt
  python analyze_esthetiek.py -i input/preek_02.txt

Deze tool analyseert de preek op esthetische kwaliteit:

  DOMEIN A - Poëtica van de Taal (Micro-Esthetiek):
    • Beeldend taalgebruik (imagery & metaphor)
    • Zorgvuldigheid en precisie (stewardship of language)
    • Muzikaliteit en ritme

  DOMEIN B - Dramaturgie van de Structuur (Macro-Esthetiek):
    • Narratieve spanningsboog (plot)
    • Integratie van tekst en context (reframing)
    • Openheid vs. geslotenheid (open kunstwerk)

  Speciale analyses:
    • Anti-kitsch score (afwezigheid van religieuze kitsch en sentiment)
    • Ruimte voor genade (Cilliers' centrale concept)

Gebaseerd op het werk van:
  Johan Cilliers, Ciska Stark, Gerrit Immink, Albrecht Grözinger,
  Paul Scott Wilson, Thomas Long, Marilyn Chandler McEntyre
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
    print("🎨 ESTHETISCHE ANALYSE VOOR HOMILETIEK")
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
        json_response = analyze_sermon_esthetiek(sermon_text, prompt_template)

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
