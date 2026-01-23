#!/usr/bin/env python3
#
# Jan 2026 (w.m.otte@umcutrecht.nl)
#
# Analyse van preken aan de hand van Narratieve Semiotiek (Greimas Actantieel Model)
# Gebaseerd op het werk van A.J. Greimas, Daniel Patte, Rein Bos, en Fleming Rutledge
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
PROMPT_FILE = "prompts/analyze_narratief.md"
OUTPUT_DIR = "outputs"

def validate_input(text):
    """
    Validates if the sermon text is substantial enough for narrative analysis.
    Checks for minimum length and basic structure.
    """
    lines = text.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]

    # Check minimum length (at least 50 non-empty lines for meaningful analysis)
    if len(non_empty_lines) < 50:
        raise ValueError(
            f"Preektekst te kort voor narratieve analyse. "
            f"Gevonden: {len(non_empty_lines)} regels. Minimaal vereist: 50 regels."
        )

    # Estimate word count (rough: avg 8 words per non-empty line)
    estimated_words = sum(len(line.split()) for line in non_empty_lines)
    if estimated_words < 500:
        raise ValueError(
            f"Preektekst te kort voor narratieve analyse. "
            f"Geschat aantal woorden: {estimated_words}. Minimaal vereist: 500 woorden."
        )

    print(f"✓ Preektekst validatie geslaagd: {len(non_empty_lines)} regels, ~{estimated_words} woorden")
    return True

def analyze_sermon_narrative(text, prompt_template):
    """
    Calls Gemini API to analyze the sermon using Greimas's Actantial Model.
    """
    if not API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")

    genai.configure(api_key=API_KEY)

    # Use gemini-3-pro-preview for high quality analysis with strong reasoning
    # This model is needed for the comprehensive analytical task
    model = genai.GenerativeModel('gemini-3-pro-preview')

    full_prompt = f"{prompt_template}\n\n--- BEGIN PREEK ---\n{text}\n--- EINDE PREEK ---"

    print("📡 Versturen naar Gemini API voor narratieve semiotiek analyse...")
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
    output_filename = f"{output_dir}/{base_name}_narratief.json"

    try:
        # Ensure json_content is valid JSON string
        parsed_json = json.loads(json_content)

        # Calculate some statistics for confirmation
        subject = ""
        rutledge_score = 0
        classification = ""

        if "actantiele_analyse" in parsed_json:
            if "primair_narratief_programma" in parsed_json["actantiele_analyse"]:
                prog = parsed_json["actantiele_analyse"]["primair_narratief_programma"]
                if "subject" in prog:
                    subject = prog["subject"].get("identificatie", "?")

        if "grammaticale_analyse" in parsed_json:
            if "subject_check" in parsed_json["grammaticale_analyse"]:
                rutledge_score = parsed_json["grammaticale_analyse"]["subject_check"].get("rutledge_score", 0)

        if "diagnostische_evaluatie" in parsed_json:
            classification = parsed_json["diagnostische_evaluatie"].get("primaire_classificatie", "?")

        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(parsed_json, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Analyse succesvol opgeslagen: {output_filename}")
        if subject:
            print(f"🎭 Primair Subject: {subject}")
        if rutledge_score:
            print(f"📊 Rutledge Score (God as Subject): {rutledge_score}/10")
        if classification:
            print(f"⚖️  Classificatie: {classification}")

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
        print("🎭 SAMENVATTING NARRATIEVE SEMIOTIEK ANALYSE (GREIMAS)")
        print("="*70)

        if "metadata" in data:
            meta = data["metadata"]
            if "titel_preek" in meta:
                print(f"Preek: {meta['titel_preek']}")
            if "bijbeltekst" in meta:
                print(f"Tekst: {meta['bijbeltekst']}")

        # Print actantial structure
        if "actantiele_analyse" in data and "primair_narratief_programma" in data["actantiele_analyse"]:
            prog = data["actantiele_analyse"]["primair_narratief_programma"]
            print(f"\n📊 Primair Narratief Programma:")

            if "subject" in prog:
                subject_id = prog["subject"].get("identificatie", "?")
                subject_freq = prog["subject"].get("frequentie_score", "?")
                print(f"   Subject:      {subject_id} (frequentie: {subject_freq}/10)")

            if "object" in prog:
                object_id = prog["object"].get("identificatie", "?")
                object_aard = prog["object"].get("aard_van_object", "?")
                print(f"   Object:       {object_id} ({object_aard})")

            if "tegenstander" in prog:
                opp_id = prog["tegenstander"].get("identificatie", "?")
                opp_ernst = prog["tegenstander"].get("ernst_tegenstander", "?")
                print(f"   Tegenstander: {opp_id} ({opp_ernst})")

        # Print grammatical analysis
        if "grammaticale_analyse" in data and "subject_check" in data["grammaticale_analyse"]:
            subj_check = data["grammaticale_analyse"]["subject_check"]
            god_count = subj_check.get("god_als_subject_count", 0)
            mens_count = subj_check.get("mens_als_subject_count", 0)
            ratio = subj_check.get("ratio", "?")
            rutledge = subj_check.get("rutledge_score", 0)

            print(f"\n📈 Grammaticale Analyse (Rutledge Rule):")
            print(f"   God als Subject:  {god_count}x")
            print(f"   Mens als Subject: {mens_count}x")
            print(f"   Ratio:            {ratio}")
            bar = "█" * rutledge + "░" * (10 - rutledge)
            print(f"   Rutledge Score:   {bar} {rutledge}/10")

        # Print diagnostic classification
        if "diagnostische_evaluatie" in data:
            diag = data["diagnostische_evaluatie"]
            classification = diag.get("primaire_classificatie", "?")

            print(f"\n⚖️  Diagnostische Classificatie: {classification}")

            if "indicatoren_moralisme" in diag and diag["indicatoren_moralisme"]:
                print(f"\n⚠️  Moralisme Indicatoren: {len(diag['indicatoren_moralisme'])} gevonden")
                for ind in diag["indicatoren_moralisme"][:2]:  # Show first 2
                    indicator = ind.get("indicator", "")
                    ernst = ind.get("ernst", "?")
                    print(f"   • [{ernst}] {indicator}")

            if "indicatoren_genade" in diag and diag["indicatoren_genade"]:
                print(f"\n✅ Genade Indicatoren: {len(diag['indicatoren_genade'])} gevonden")
                for ind in diag["indicatoren_genade"][:2]:  # Show first 2
                    indicator = ind.get("indicator", "")
                    sterkte = ind.get("sterkte", "?")
                    print(f"   • [{sterkte}] {indicator}")

        # Print overall assessment
        if "aanbevelingen" in data and "overall_beoordeling" in data["aanbevelingen"]:
            beoordeling = data["aanbevelingen"]["overall_beoordeling"]
            print(f"\n⭐ Overall Beoordeling: {beoordeling}")

        print("="*70 + "\n")

    except Exception as e:
        print(f"⚠️  Kon geen samenvatting genereren: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Analyseer een preek aan de hand van Narratieve Semiotiek (Greimas Actantieel Model).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Voorbeelden:
  python analyze_narratief.py
  python analyze_narratief.py --input input/mijn_preek.txt
  python analyze_narratief.py -i input/preek_02.txt

Deze tool analyseert de preek op:
  • De 6 actanten (Subject, Object, Zender, Ontvanger, Helper, Tegenstander)
  • De 3 assen (Verlangen, Macht, Overdracht)
  • Grammaticale analyse (God vs. Mens als Subject van werkwoorden)
  • Modale competenties (Moeten, Willen, Weten, Kunnen)
  • Semiotisch vierkant (logische dieptestructuur)
  • Diagnostiek: Moralisme vs. Genade-oriëntatie
  • Fleming Rutledge's "God as Subject" regel
  • Rein Bos' waarschuwing tegen exemplarisme
  • Concrete aanbevelingen voor herpositionering
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
    print("🎭 NARRATIEVE SEMIOTIEK ANALYSE (GREIMAS)")
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
        json_response = analyze_sermon_narrative(sermon_text, prompt_template)

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
