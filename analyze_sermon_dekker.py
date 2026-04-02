#!/usr/bin/env python3
#
# Dec 2025/Jan 2026 (w.m.otte@umcutrecht.nl)
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
PROMPT_FILE = "prompts/analyze_sermon_dekker.md"
OUTPUT_DIR = "outputs"

def count_words(text):
    """
    Count the actual number of words in the sermon text.
    Returns the word count.
    """
    # Remove extra whitespace and count words
    words = text.split()
    return len(words)

def validate_input(text):
    """
    Validates if the sermon text is substantial enough for Dekker analysis.
    Checks for minimum length and basic structure.
    Returns the word count.
    """
    lines = text.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]

    # Check minimum length (at least 50 non-empty lines for meaningful analysis)
    if len(non_empty_lines) < 50:
        raise ValueError(
            f"Preektekst te kort voor Dekker-analyse. "
            f"Gevonden: {len(non_empty_lines)} regels. Minimaal vereist: 50 regels."
        )

    # Count actual words
    word_count = count_words(text)
    if word_count < 500:
        raise ValueError(
            f"Preektekst te kort voor Dekker-analyse. "
            f"Aantal woorden: {word_count}. Minimaal vereist: 500 woorden."
        )

    print(f"✓ Preektekst validatie geslaagd: {len(non_empty_lines)} regels, {word_count} woorden")
    return word_count

def analyze_sermon(text, prompt_template, word_count):
    """
    Calls Gemini API to analyze the sermon.
    """
    if not API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")

    genai.configure(api_key=API_KEY)

    # Use gemini-1.5-flash for speed/cost efficiency, or pro if deeper reasoning needed.
    # User requested gemini-pro-2.5 which doesn't exist yet, assuming they mean 1.5-pro or latest.
    # I'll use gemini-1.5-pro for high quality analysis.
    model = genai.GenerativeModel('gemini-3.1-pro-preview')

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

    response = model.generate_content(
        full_prompt,
        generation_config={"response_mime_type": "application/json"}
    )

    return response.text

def save_output(input_filename, json_content, output_dir=OUTPUT_DIR):
    """
    Saves the JSON content to the specified output directory.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    base_name = os.path.splitext(os.path.basename(input_filename))[0]
    output_filename = f"{output_dir}/{base_name}_dekker.json"

    try:
        # Ensure json_content is valid JSON string
        parsed_json = json.loads(json_content)
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(parsed_json, f, indent=2, ensure_ascii=False)
        print(f"✅ Analysis saved to: {output_filename}")
        return output_filename
    except json.JSONDecodeError:
        print("❌ Error: content returned was not valid JSON.")
        # Save raw content for debugging
        raw_filename = f"{output_filename}.raw"
        with open(raw_filename, 'w', encoding='utf-8') as f:
            f.write(json_content)
        print(f"💾 Raw content saved to: {raw_filename}")
        return None

def main():
    parser = argparse.ArgumentParser(
        description="Analyseer een preek aan de hand van de thesen van Dr. W.M. Dekker.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Voorbeelden:
  python analyze_sermon_dekker.py
  python analyze_sermon_dekker.py --input input/mijn_preek.txt
  python analyze_sermon_dekker.py -i input/preek_02.txt --output-dir my_output
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
    print("📖 DEKKER ANALYSE VOOR HOMILETIEK")
    print("="*70)
    print(f"📖 Input bestand: {input_file}\n")

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            sermon_text = f.read()

        print("✓ Validatie wordt uitgevoerd...")
        word_count = validate_input(sermon_text)

        print("✓ Prompt template wordt geladen...")
        with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
            prompt_template = f.read()

        print("✓ Analyse wordt gestart met Gemini AI...")
        json_response = analyze_sermon(sermon_text, prompt_template, word_count)

        save_output(input_file, json_response, output_dir)

    except FileNotFoundError as e:
        print(f"❌ Bestand niet gevonden: {e}")
    except ValueError as e:
        print(f"❌ Validatie fout: {e}")
    except Exception as e:
        print(f"❌ Er is een onverwachte fout opgetreden: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
