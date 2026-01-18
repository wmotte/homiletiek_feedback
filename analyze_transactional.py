#!/usr/bin/env python3
#
# Jan 2026
#
# Analyse van preken aan de hand van Transactionele Analyse (Eric Berne)
# Focus op Ego-posities, Transacties, Games en de Dramadriehoek
#
#####################################################
import os
import json
import datetime
import argparse
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
DEFAULT_INPUT_FILE = "input/preek_01.txt"
PROMPT_FILE = "prompts/analyze_transactional.md"
OUTPUT_DIR = "outputs"

def validate_input(text):
    """
    Validates if the sermon text is substantial enough for analysis.
    """
    lines = text.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]

    if len(non_empty_lines) < 50:
        raise ValueError(
            f"Preektekst te kort voor analyse. "
            f"Gevonden: {len(non_empty_lines)} regels. Minimaal vereist: 50 regels."
        )
    return True

def analyze_sermon_transactional(text, prompt_template):
    """
    Calls Gemini API to analyze the sermon using Transactional Analysis framework.
    """
    if not API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")

    print(f"DEBUG: API Key found. Length: {len(API_KEY)}")
    print(f"DEBUG: Key starts with: {API_KEY[:4]}...")
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-3-pro-preview')

    full_prompt = f"{prompt_template}\n\n--- BEGIN PREEK ---\n{text}\n--- EINDE PREEK ---"

    print("📡 Versturen naar Gemini API voor Transactionele Analyse...")
    print("⚙️  Dit kan enkele seconden duren...")

    response = model.generate_content(
        full_prompt,
        generation_config={
            "response_mime_type": "application/json",
            "temperature": 0.4,
        }
    )

    return response.text

def save_output(input_filename, json_content):
    """
    Saves the JSON content to the outputs directory.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(input_filename))[0]
    output_filename = f"{OUTPUT_DIR}/{base_name}_transactional_{timestamp}.json"

    try:
        parsed_json = json.loads(json_content)
        
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(parsed_json, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Analyse succesvol opgeslagen: {output_filename}")
        
        # Print simple score if available
        if "conclusie_en_aanbeveling" in parsed_json:
            score = parsed_json["conclusie_en_aanbeveling"].get("psychologische_gezondheid_score", 0)
            print(f"🧠 Psychologische Gezondheid Score: {score}/10")

        return output_filename

    except json.JSONDecodeError as e:
        print(f"❌ Error: content returned was not valid JSON: {e}")
        raw_filename = f"{output_filename}.raw"
        with open(raw_filename, 'w', encoding='utf-8') as f:
            f.write(json_content)
        print(f"💾 Raw content saved for debugging: {raw_filename}")
        return None

def print_summary(output_file):
    """
    Prints a brief summary of the TA results.
    """
    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print("\n" + "="*70)
        print("🧠 SAMENVATTING TRANSACTIONELE ANALYSE")
        print("="*70)

        if "ego_posities_scan" in data:
            scan = data["ego_posities_scan"]
            print("\n📊 Ego-posities (10 = Gezond/Vrij):")
            if "dominante_ego_positie" in scan:
                print(f"   🎯 Dominant: {scan['dominante_ego_positie']}")
            
            # Print simple bar charts for key positions if scores exist
            # Note: Scores are now "Positive" (10 = Good/Absent of negative trait)
            positions = {
                "Vrijheid v. Kritische Ouder": scan.get("ouder_parent", {}).get("vrijheid_van_kritische_ouder_CP", {}).get("score", 0),
                "Gezonde Zorg (NP)": scan.get("ouder_parent", {}).get("gezonde_zorg_NP", {}).get("score", 0),
                "Volwassene (A)": scan.get("volwassene_adult", {}).get("score", 0),
                "Vrijheid v. Aangepast Kind": scan.get("kind_child", {}).get("vrijheid_van_aangepast_kind_AC", {}).get("score", 0),
                "Vrij Kind (FC)": scan.get("kind_child", {}).get("vrij_kind_FC", {}).get("score", 0)
            }
            
            for name, score in positions.items():
                if score is not None:
                    # Visual representation: 10 is good, 0 is bad
                    try:
                        score_int = int(score)
                        bar = "█" * score_int + "░" * (10 - score_int)
                        print(f"   {name:30s} {bar} {score}/10")
                    except ValueError:
                        pass

        if "spel_analyse_games" in data:
            games = data["spel_analyse_games"].get("gedetecteerde_spelen", [])
            if games:
                print("\n🎭 Gedetecteerde Spelen:")
                for game in games:
                    name = game.get("naam", "Onbekend")
                    prob = game.get("waarschijnlijkheid", "?")
                    print(f"   - {name} ({prob})")
            else:
                print("\n🎭 Geen destructieve spelen gedetecteerd.")

        if "conclusie_en_aanbeveling" in data:
            conc = data["conclusie_en_aanbeveling"]
            print(f"\n🧠 Gezondheidsscore: {conc.get('psychologische_gezondheid_score', '?')}/10")
            print(f"💡 Advies: {conc.get('advies_voor_game_vrije_communicatie', '')[:100]}...")

        print("="*70 + "\n")

    except Exception as e:
        print(f"⚠️  Kon geen samenvatting genereren: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Analyseer een preek aan de hand van Transactionele Analyse (Eric Berne).",
        formatter_class=argparse.RawDescriptionHelpFormatter
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
    print("🧠 TRANSACTIONELE ANALYSE VOOR HOMILETIEK")
    print("="*70)
    print(f"📖 Input bestand: {input_file}\n")

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            sermon_text = f.read()

        validate_input(sermon_text)

        with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
            prompt_template = f.read()

        json_response = analyze_sermon_transactional(sermon_text, prompt_template)
        output_file = save_output(input_file, json_response)

        if output_file and not args.no_summary:
            print_summary(output_file)

    except FileNotFoundError as e:
        print(f"❌ Bestand niet gevonden: {e}")
    except ValueError as e:
        print(f"❌ Validatie fout: {e}")
    except Exception as e:
        print(f"❌ Fout: {e}")

if __name__ == "__main__":
    main()
