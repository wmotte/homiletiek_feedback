#!/usr/bin/env python3
#
# Jan 2026 (w.m.otte@umcutrecht.nl)
#
# Analyse van preken aan de hand van Taalhandelingstheorie (Speech Act Theory)
# Gebaseerd op het werk van J.L. Austin en John Searle
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

def count_words(text):
    """
    Count the actual number of words in the sermon text.
    Returns the word count.
    """
    words = text.split()
    return len(words)

# Configuration
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
DEFAULT_INPUT_FILE = "input/preek_01.txt"
PROMPT_FILE = "prompts/analyze_taalhandeling.md"
OUTPUT_DIR = "outputs"

def validate_input(text):
    """
    Validates if the sermon text is substantial enough for speech act analysis.
    Checks for minimum length and basic structure.
    """
    lines = text.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]

    # Check minimum length (at least 50 non-empty lines for meaningful analysis)
    if len(non_empty_lines) < 50:
        raise ValueError(
            f"Preektekst te kort voor taalhandelingsanalyse. "
            f"Gevonden: {len(non_empty_lines)} regels. Minimaal vereist: 50 regels."
        )

    # Count actual words
    word_count = count_words(text)
    if word_count < 500:
        raise ValueError(
            f"Preektekst te kort voor taalhandelingsanalyse. "
            f"Aantal woorden: {word_count}. Minimaal vereist: 500 woorden."
        )

    print(f"✓ Preektekst validatie geslaagd: {len(non_empty_lines)} regels, {word_count} woorden")
    return word_count

def analyze_sermon_speech_act(text, prompt_template, word_count):
    """
    Calls Gemini API to analyze the sermon using Speech Act Theory (Austin & Searle).
    """
    if not API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")

    genai.configure(api_key=API_KEY)

    # Use gemini-3-pro-preview for high quality analysis with strong reasoning
    # This model is needed for the comprehensive analytical task
    model = genai.GenerativeModel('gemini-3-pro-preview')

    # Calculate estimated duration (100 words per minute)
    estimated_duration = round(word_count / 100)

    full_prompt = f"""{prompt_template}

--- BELANGRIJKE METADATA ---
Het exacte aantal woorden in deze preek is: {word_count}
Geschatte duur bij 100 woorden/minuut: {estimated_duration} minuten

Gebruik deze exacte waarden in je metadata sectie:
- "geschatte_woordlengte": {word_count}
- "geschatte_tijdsduur_minuten": {estimated_duration}

--- BEGIN PREEK ---
{text}
--- EINDE PREEK ---"""

    print("📡 Versturen naar Gemini API voor taalhandelingsanalyse...")
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
    output_filename = f"{output_dir}/{base_name}_taalhandeling.json"

    try:
        # Ensure json_content is valid JSON string
        parsed_json = json.loads(json_content)

        # Calculate some statistics for confirmation
        classification = ""
        constatief_pct = 0
        performatief_pct = 0
        gebeuren_score = 0

        if "constatief_performatief_diagnose" in parsed_json:
            diag = parsed_json["constatief_performatief_diagnose"]
            classification = diag.get("primaire_classificatie", "?")
            constatief_pct = diag.get("constatief_percentage", "?")
            performatief_pct = diag.get("performatief_percentage", "?")

        if "diagnostische_evaluatie" in parsed_json:
            gebeuren_score = parsed_json["diagnostische_evaluatie"].get("gebeuren_score", 0)

        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(parsed_json, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Analyse succesvol opgeslagen: {output_filename}")
        if classification:
            print(f"📊 Classificatie: {classification}")
        if constatief_pct and performatief_pct:
            print(f"📈 Constatief: {constatief_pct} | Performatief: {performatief_pct}")
        if gebeuren_score:
            print(f"⚡ Gebeuren Score: {gebeuren_score}/10")

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
        print("💬 SAMENVATTING TAALHANDELINGSANALYSE (AUSTIN & SEARLE)")
        print("="*70)

        if "metadata" in data:
            meta = data["metadata"]
            if "titel_preek" in meta:
                print(f"Preek: {meta['titel_preek']}")
            if "bijbeltekst" in meta:
                print(f"Tekst: {meta['bijbeltekst']}")

        # Print verb distribution
        if "werkwoord_analyse" in data:
            print(f"\n📊 Werkwoordverdeling (Searle's Taxonomie):")

            categories = {
                "assertieven": "Assertieven (Constatief)",
                "directieven": "Directieven (Imperatief)",
                "expressieven": "Expressieven",
                "commissieven": "Commissieven (Belofte)",
                "declaratieven": "Declaratieven (Scheppend)"
            }

            for key, label in categories.items():
                if key in data["werkwoord_analyse"]:
                    cat = data["werkwoord_analyse"][key]
                    freq = cat.get("frequentie", 0)
                    pct = cat.get("procent", "?")
                    print(f"   {label:35s} {freq:3d}x ({pct})")

        # Print diagnosis
        if "constatief_performatief_diagnose" in data:
            diag = data["constatief_performatief_diagnose"]
            classification = diag.get("primaire_classificatie", "?")

            print(f"\n⚖️  Primaire Diagnose: {classification}")

            if "constatief_percentage" in diag and "performatief_percentage" in diag:
                const_pct = diag["constatief_percentage"]
                perf_pct = diag["performatief_percentage"]
                print(f"   Constatief:  {const_pct}")
                print(f"   Performatief: {perf_pct}")

            # Toezegging check
            if "toezegging_check" in diag:
                tz = diag["toezegging_check"]
                if "toezegging_aanwezig" in tz:
                    tz_aanwezig = tz["toezegging_aanwezig"]
                    tz_aantal = tz.get("aantal_toezeggen", 0)
                    if tz_aanwezig:
                        print(f"\n✅ Toezegging Aanwezig: {tz_aantal}x")
                    else:
                        print(f"\n⚠️  Toezegging Afwezig")

        # Print scores
        if "diagnostische_evaluatie" in data:
            eval_data = data["diagnostische_evaluatie"]

            if "gebeuren_score" in eval_data:
                score = eval_data["gebeuren_score"]
                bar = "█" * score + "░" * (10 - score)
                print(f"\n⚡ Gebeuren Score:      {bar} {score}/10")

            if "sacramentele_kracht" in eval_data:
                score = eval_data["sacramentele_kracht"]
                bar = "█" * score + "░" * (10 - score)
                print(f"🕊️  Sacramentele Kracht: {bar} {score}/10")

            if "primaire_diagnose" in eval_data:
                diagnose = eval_data["primaire_diagnose"]
                print(f"\n🎯 Type Preek: {diagnose}")

        # Print overall assessment
        if "aanbevelingen" in data and "overall_beoordeling" in data["aanbevelingen"]:
            beoordeling = data["aanbevelingen"]["overall_beoordeling"]
            print(f"\n⭐ Overall Beoordeling: {beoordeling}")

        print("="*70 + "\n")

    except Exception as e:
        print(f"⚠️  Kon geen samenvatting genereren: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Analyseer een preek aan de hand van Taalhandelingstheorie (Speech Act Theory).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Voorbeelden:
  python analyze_taalhandeling.py
  python analyze_taalhandeling.py --input input/mijn_preek.txt
  python analyze_taalhandeling.py -i input/preek_02.txt

Deze tool analyseert de preek op:
  • De drievoudige structuur (Locutie, Illocutie, Perlocutie)
  • Searle's vijf categorieën (Assertief, Directief, Expressief, Commissief, Declaratief)
  • Constatief surplus vs. Performatief deficit
  • Toezegging-check (wordt genade toegezegd OF erover gepraat?)
  • Adressering (2e persoon vs. 3e persoon)
  • Sacramenteel patroon (Indicatief → Imperatief)
  • "Gebeuren" score: Is de preek een event of een lezing?
  • Concrete aanbevelingen voor performatieve intensivering
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
    print("💬 TAALHANDELINGSTHEORIE (SPEECH ACT) ANALYSE")
    print("="*70)
    print(f"📖 Input bestand: {input_file}\n")

    try:
        # Read input file
        with open(input_file, 'r', encoding='utf-8') as f:
            sermon_text = f.read()

        # Validate input
        print("✓ Validatie wordt uitgevoerd...")
        word_count = validate_input(sermon_text)

        # Read prompt template
        print("✓ Prompt template wordt geladen...")
        with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
            prompt_template = f.read()

        # Analyze with Gemini
        print("✓ Analyse wordt gestart met Gemini AI...")
        json_response = analyze_sermon_speech_act(sermon_text, prompt_template)

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
