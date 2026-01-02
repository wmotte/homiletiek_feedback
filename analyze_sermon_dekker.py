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

def validate_input(text):
    """
    Validates if the sermon text contains scripture readings at the beginning.
    Searches for keywords like 'Lezing', 'Schrift', 'Matteüs', 'Jesaja', etc.
    in the first 50 lines.
    """
    lines = text.split('\n')[:50]
    header_text = '\n'.join(lines).lower()
    
    # Keywords that suggest a scripture reading section
    keywords = [
        r"lezing", r"schrift", r"bijbel", 
        r"matteüs", r"marcus", r"lucas", r"johannes", 
        r"jesaja", r"psalm", r"genesis", r"exodus",
        r"korintiërs", r"romeinen"
    ]
    
    found = False
    for keyword in keywords:
        if re.search(keyword, header_text):
            found = True
            break
            
    if not found:
        # Fallback: check for verse notation like "1:1" or "2-3" combined with a name
        if re.search(r"\d+:\d+", header_text):
            found = True

    if not found:
        raise ValueError("Schriftlezingen niet meegeleverd (of niet herkend in de eerste regels).")
    
    return True

def analyze_sermon(text, prompt_template):
    """
    Calls Gemini API to analyze the sermon.
    """
    if not API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")

    genai.configure(api_key=API_KEY)
    
    # Use gemini-1.5-flash for speed/cost efficiency, or pro if deeper reasoning needed. 
    # User requested gemini-pro-2.5 which doesn't exist yet, assuming they mean 1.5-pro or latest.
    # I'll use gemini-1.5-pro for high quality analysis.
    model = genai.GenerativeModel('gemini-3-pro-preview')

    full_prompt = f"{prompt_template}\n\n--- BEGIN PREEK ---\n{text}\n--- EINDE PREEK ---"

    response = model.generate_content(
        full_prompt,
        generation_config={"response_mime_type": "application/json"}
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
    output_filename = f"{OUTPUT_DIR}/{base_name}_{timestamp}.json"
    
    try:
        # Ensure json_content is valid JSON string
        parsed_json = json.loads(json_content)
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(parsed_json, f, indent=2, ensure_ascii=False)
        print(f"Analysis saved to: {output_filename}")
    except json.JSONDecodeError:
        print("Error: content returned was not valid JSON.")
        # Save raw content for debugging
        with open(f"{output_filename}.raw", 'w', encoding='utf-8') as f:
            f.write(json_content)
        print(f"Raw content saved to: {output_filename}.raw")

def main():
    parser = argparse.ArgumentParser(description="Analyseer een preek aan de hand van de thesen van Dr. W.M. Dekker.")
    parser.add_argument("--i", "--input", type=str, default=DEFAULT_INPUT_FILE, help="Pad naar het inputbestand (.txt)")
    args = parser.parse_index_args() if hasattr(parser, 'parse_index_args') else parser.parse_args()
    
    input_file = args.i

    print(f"Reading input file: {input_file}")
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            sermon_text = f.read()
            
        print("Validating input...")
        validate_input(sermon_text)
        print("Input validated: Scripture readings present.")
        
        print("Reading prompt...")
        with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
            
        print("Analyzing with Gemini...")
        json_response = analyze_sermon(sermon_text, prompt_template)
        
        save_output(input_file, json_response)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except ValueError as e:
        print(f"Validation Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
