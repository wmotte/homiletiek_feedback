#!/bin/bash
#
# Batch Analysis Script for All Theologians
# Runs homiletic analyses on sermons from augustine, solle, brueggemann, keller, taylor, and rutledge
#
# Usage: ./batch_analyze_all.sh [theologian] [analysis]
#        theologian: augustine, solle, brueggemann, keller, taylor, rutledge, or 'all' (default)
#        analysis:   dekker, aristoteles, schulz_von_thun, kolb, esthetiek, or 'all' (default)
#
# Examples:
#   ./batch_analyze_all.sh                      # Run all analyses on all theologians
#   ./batch_analyze_all.sh taylor               # Run all analyses on Taylor only
#   ./batch_analyze_all.sh taylor dekker        # Run only Dekker analysis on Taylor
#   ./batch_analyze_all.sh all aristoteles      # Run Aristoteles analysis on all theologians
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Directories
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
OUTPUT_DIR="${SCRIPT_DIR}/outputs"
TEMP_DIR="${SCRIPT_DIR}/temp_sermons"

# Portable timeout function (works on macOS and Linux)
run_with_timeout() {
    local timeout_seconds=$1
    shift

    # Try gtimeout (macOS with coreutils), then timeout (Linux)
    if command -v gtimeout &> /dev/null; then
        gtimeout "$timeout_seconds" "$@"
    elif command -v timeout &> /dev/null; then
        timeout "$timeout_seconds" "$@"
    else
        # Fallback: run without timeout
        "$@"
    fi
}

# Analysis scripts
SCRIPTS=(
    "analyze_sermon_dekker.py"
    "analyze_aristoteles.py"
    "analyze_schulz_von_thun.py"
    "analyze_kolb_cyclus.py"
    "analyze_esthetiek.py"
)

# Analysis names for reporting
ANALYSIS_NAMES=(
    "Dekker's Theses"
    "Aristotelian Modes"
    "Schulz von Thun"
    "Kolb's Learning Cycle"
    "Aesthetic Turn"
)

# Parse arguments
THEOLOGIAN="${1:-all}"
ANALYSIS="${2:-all}"

# Validate theologian argument
if [[ ! "$THEOLOGIAN" =~ ^(augustine|solle|brueggemann|keller|taylor|rutledge|all)$ ]]; then
    echo -e "${RED}Error: Invalid theologian. Use: augustine, solle, brueggemann, keller, taylor, rutledge, or all${NC}"
    exit 1
fi

# Validate analysis argument
if [[ ! "$ANALYSIS" =~ ^(dekker|aristoteles|schulz_von_thun|kolb|esthetiek|all)$ ]]; then
    echo -e "${RED}Error: Invalid analysis. Use: dekker, aristoteles, schulz_von_thun, kolb, esthetiek, or all${NC}"
    exit 1
fi

# Determine which theologians to process
if [ "$THEOLOGIAN" = "all" ]; then
    THEOLOGIANS=("augustine" "solle" "brueggemann" "keller" "taylor" "rutledge")
else
    THEOLOGIANS=("$THEOLOGIAN")
fi

# Determine which analyses to run
if [ "$ANALYSIS" = "all" ]; then
    SELECTED_SCRIPTS=("${SCRIPTS[@]}")
    SELECTED_NAMES=("${ANALYSIS_NAMES[@]}")
else
    # Map analysis name to script and display name
    case "$ANALYSIS" in
        "dekker")
            SELECTED_SCRIPTS=("analyze_sermon_dekker.py")
            SELECTED_NAMES=("Dekker's Theses")
            ;;
        "aristoteles")
            SELECTED_SCRIPTS=("analyze_aristoteles.py")
            SELECTED_NAMES=("Aristotelian Modes")
            ;;
        "schulz_von_thun")
            SELECTED_SCRIPTS=("analyze_schulz_von_thun.py")
            SELECTED_NAMES=("Schulz von Thun")
            ;;
        "kolb")
            SELECTED_SCRIPTS=("analyze_kolb_cyclus.py")
            SELECTED_NAMES=("Kolb's Learning Cycle")
            ;;
        "esthetiek")
            SELECTED_SCRIPTS=("analyze_esthetiek.py")
            SELECTED_NAMES=("Aesthetic Turn")
            ;;
    esac
fi

ANALYSIS_COUNT=${#SELECTED_SCRIPTS[@]}
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        BATCH ANALYSIS: SERMON ANALYSIS FRAMEWORK                   ║${NC}"
printf "${BLUE}║        Running %d analysis(es) per sermon                           ║${NC}\n" ${ANALYSIS_COUNT}
echo -e "${BLUE}║        Theologian: $(printf '%-47s' "${THEOLOGIAN}") ║${NC}"
echo -e "${BLUE}║        Analysis:   $(printf '%-47s' "${ANALYSIS}") ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Python scripts exist
echo -e "${YELLOW}Checking for analysis scripts...${NC}"
for script in "${SELECTED_SCRIPTS[@]}"; do
    if [ ! -f "${SCRIPT_DIR}/${script}" ]; then
        echo -e "${RED}✗ Error: ${script} not found${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Found ${script}${NC}"
done
echo ""

# Create necessary directories
mkdir -p "${OUTPUT_DIR}"
mkdir -p "${TEMP_DIR}"

# Create error log
ERROR_LOG="${OUTPUT_DIR}/batch_errors.log"
: > "${ERROR_LOG}"  # Clear previous error log

# Global counters
TOTAL_COMPLETED=0
TOTAL_FAILED=0
TOTAL_SKIPPED=0
START_TIME=$(date +%s)

# Process each theologian
for theo in "${THEOLOGIANS[@]}"; do
    SERMON_DIR="${SCRIPT_DIR}/sermons_${theo}/sermons"

    # Check if sermon directory exists
    if [ ! -d "$SERMON_DIR" ]; then
        echo -e "${RED}✗ Warning: Directory not found: ${SERMON_DIR}${NC}"
        echo -e "${YELLOW}  Skipping ${theo}...${NC}"
        continue
    fi

    # Count sermon files
    SERMON_FILES=(${SERMON_DIR}/*.json)
    SERMON_COUNT=${#SERMON_FILES[@]}

    if [ ${SERMON_COUNT} -eq 0 ]; then
        echo -e "${YELLOW}No sermons found for ${theo}. Skipping...${NC}"
        continue
    fi

    echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}Processing theologian: $(echo "$theo" | tr '[:lower:]' '[:upper:]') (${SERMON_COUNT} sermons)${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════════${NC}"
    echo ""

    # Verify temp directory is accessible
    if [ ! -d "${TEMP_DIR}" ] || [ ! -w "${TEMP_DIR}" ]; then
        echo -e "${YELLOW}Recreating temp directory...${NC}"
        mkdir -p "${TEMP_DIR}" || {
            echo -e "${RED}✗ Failed to create temp directory: ${TEMP_DIR}${NC}"
            continue
        }
    fi

    # Counters for this theologian
    COMPLETED=0
    FAILED=0
    SKIPPED=0
    SERMON_NUMBER=0

    # Process each sermon
    for sermon_json in "${SERMON_FILES[@]}"; do
        SERMON_NUMBER=$((SERMON_NUMBER + 1))
        SERMON_ID=$(printf "%02d" ${SERMON_NUMBER})
        SERMON_BASENAME=$(basename "${sermon_json}" .json)

        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${BLUE}Processing: ${theo}_${SERMON_ID} (${SERMON_BASENAME})${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

        # Extract sermon title
        SERMON_TITLE=$(python3 -c "import json; f=open('${sermon_json}'); d=json.load(f); print(d.get('title', 'Unknown')); f.close()")
        echo -e "Title: ${YELLOW}${SERMON_TITLE}${NC}"
        echo ""

        # Extract text from JSON and create temporary txt file
        TEMP_TXT="${TEMP_DIR}/${SERMON_BASENAME}.txt"

        # Remove old temp file if it exists
        rm -f "${TEMP_TXT}"

        python3 -c "
import json
import sys

try:
    with open('${sermon_json}', 'r', encoding='utf-8') as f:
        data = json.load(f)

    title = data.get('title', 'Untitled')

    # Try all known content fields
    content = data.get('main_text') or data.get('content') or data.get('text') or data.get('body', '')

    sermon_text = f\"Title: {title}\\n\\n{content}\"

    with open('${TEMP_TXT}', 'w', encoding='utf-8') as f:
        f.write(sermon_text)

    sys.exit(0)
except Exception as e:
    print(f'Error extracting sermon text: {e}', file=sys.stderr)
    sys.exit(1)
" 2>> "${ERROR_LOG}"
        EXTRACT_STATUS=$?

        # Check if extraction failed or file wasn't created
        if [ $EXTRACT_STATUS -ne 0 ] || [ ! -f "${TEMP_TXT}" ]; then
            echo -e "${RED}✗ Failed to extract text from ${sermon_json} (exit code: ${EXTRACT_STATUS})${NC}"
            echo "[$(date)] Failed to extract ${sermon_json} (exit code: ${EXTRACT_STATUS})" >> "${ERROR_LOG}"
            FAILED=$((FAILED + ${#SELECTED_SCRIPTS[@]}))
            continue
        fi

        # Verify temp file has content
        if [ ! -s "${TEMP_TXT}" ]; then
            echo -e "${RED}✗ Extracted file is empty: ${TEMP_TXT}${NC}"
            echo "[$(date)] Empty extraction for ${sermon_json}" >> "${ERROR_LOG}"
            FAILED=$((FAILED + ${#SELECTED_SCRIPTS[@]}))
            continue
        fi

        # Run each analysis script
        for i in "${!SELECTED_SCRIPTS[@]}"; do
            SCRIPT="${SELECTED_SCRIPTS[$i]}"
            ANALYSIS_NAME="${SELECTED_NAMES[$i]}"

            # Determine the output suffix for this analysis
            case ${SCRIPT} in
                "analyze_sermon_dekker.py")
                    SUFFIX="_dekker"
                    ;;
                "analyze_aristoteles.py")
                    SUFFIX="_aristoteles"
                    ;;
                "analyze_schulz_von_thun.py")
                    SUFFIX="_schulz_von_thun"
                    ;;
                "analyze_kolb_cyclus.py")
                    SUFFIX="_kolb"
                    ;;
                "analyze_esthetiek.py")
                    SUFFIX="_esthetiek"
                    ;;
            esac

            # Check if output file already exists
            EXPECTED_OUTPUT="${OUTPUT_DIR}/${theo}_${SERMON_ID}${SUFFIX}.json"

            if [ -f "${EXPECTED_OUTPUT}" ]; then
                echo -e "${BLUE}  ⊙ ${ANALYSIS_NAME} already exists (skipped)${NC}"
                SKIPPED=$((SKIPPED + 1))
                continue
            fi

            echo -ne "${YELLOW}  ⟳ Running ${ANALYSIS_NAME}...${NC}"

            # Run the analysis with suppressed summary, theologian and sermon-id parameters
            # Redirect errors to log file for debugging
            if run_with_timeout 120 python3 "${SCRIPT_DIR}/${SCRIPT}" --input "${TEMP_TXT}" --theologian "${theo}" --sermon-id "${SERMON_ID}" --no-summary > /dev/null 2>> "${ERROR_LOG}"; then
                echo -e "\r${GREEN}  ✓ ${ANALYSIS_NAME} completed${NC}"
                COMPLETED=$((COMPLETED + 1))
            else
                ANALYSIS_EXIT_CODE=$?
                if [ $ANALYSIS_EXIT_CODE -eq 124 ]; then
                    echo -e "\r${RED}  ✗ ${ANALYSIS_NAME} timed out (120s)${NC}"
                    echo "[$(date)] Timeout: ${theo}_${SERMON_ID} - ${ANALYSIS_NAME}" >> "${ERROR_LOG}"
                else
                    echo -e "\r${RED}  ✗ ${ANALYSIS_NAME} failed (code: ${ANALYSIS_EXIT_CODE})${NC}"
                    echo "[$(date)] Failed: ${theo}_${SERMON_ID} - ${ANALYSIS_NAME} (exit code: ${ANALYSIS_EXIT_CODE})" >> "${ERROR_LOG}"
                fi
                FAILED=$((FAILED + 1))
            fi
        done

        # Clean up temp file for this sermon
        rm -f "${TEMP_TXT}"

        echo ""

        # Show progress for this theologian
        PROGRESS=$((COMPLETED + FAILED + SKIPPED))
        TOTAL_ANALYSES=$((SERMON_COUNT * ${#SELECTED_SCRIPTS[@]}))
        PERCENT=$((PROGRESS * 100 / TOTAL_ANALYSES))
        echo -e "${BLUE}Progress (${theo}): ${PROGRESS}/${TOTAL_ANALYSES} analyses (${PERCENT}%) | ✓ ${GREEN}${COMPLETED}${NC} | ⊙ ${BLUE}${SKIPPED}${NC} | ✗ ${RED}${FAILED}${NC}"
        echo ""
    done

    # Update global counters
    TOTAL_COMPLETED=$((TOTAL_COMPLETED + COMPLETED))
    TOTAL_FAILED=$((TOTAL_FAILED + FAILED))
    TOTAL_SKIPPED=$((TOTAL_SKIPPED + SKIPPED))

    echo -e "${GREEN}✓ Completed ${theo}: ${COMPLETED} analyses${NC}"
    if [ ${SKIPPED} -gt 0 ]; then
        echo -e "${BLUE}⊙ Skipped ${theo}: ${SKIPPED} analyses (already exist)${NC}"
    fi
    if [ ${FAILED} -gt 0 ]; then
        echo -e "${RED}✗ Failed ${theo}: ${FAILED} analyses${NC}"
    fi
    echo ""
done

# Clean up temporary files
echo -e "${YELLOW}Cleaning up temporary files...${NC}"
rm -rf "${TEMP_DIR}"
echo -e "${GREEN}✓ Cleanup complete${NC}"
echo ""

# Calculate elapsed time
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED / 60))
SECONDS=$((ELAPSED % 60))

# Final summary
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                         BATCH ANALYSIS COMPLETE                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}✓ Completed:${NC} ${TOTAL_COMPLETED} analyses"
if [ ${TOTAL_SKIPPED} -gt 0 ]; then
    echo -e "${BLUE}⊙ Skipped:${NC} ${TOTAL_SKIPPED} analyses (already exist)"
fi
if [ ${TOTAL_FAILED} -gt 0 ]; then
    echo -e "${RED}✗ Failed:${NC} ${TOTAL_FAILED} analyses"
fi
echo -e "${BLUE}⏱  Time elapsed:${NC} ${MINUTES}m ${SECONDS}s"
echo ""
echo -e "${YELLOW}Output files saved to:${NC} ${OUTPUT_DIR}/"
if [ ${TOTAL_FAILED} -gt 0 ]; then
    echo -e "${YELLOW}Error log saved to:${NC} ${ERROR_LOG}"
fi
echo ""

# Generate index file for web interface
echo -e "${YELLOW}Generating file index for web interface...${NC}"
INDEX_FILE="${SCRIPT_DIR}/docs/file_index.json"

# Create JSON array of filenames (works without jq)
TEMP_LIST=$(mktemp)
find "${OUTPUT_DIR}" -name "*.json" -type f ! -name "batch_errors.log" -exec basename {} \; | sort > "${TEMP_LIST}"

FILE_COUNT=$(wc -l < "${TEMP_LIST}" | tr -d ' ')

if [ "${FILE_COUNT}" -eq 0 ]; then
    echo "[]" > "${INDEX_FILE}"
else
    echo "[" > "${INDEX_FILE}"
    while IFS= read -r filename; do
        if [ -n "$filename" ]; then
            echo "  \"${filename}\"," >> "${INDEX_FILE}"
        fi
    done < "${TEMP_LIST}"
    # Remove trailing comma from last entry and close array
    sed -i.bak '$ s/,$//' "${INDEX_FILE}" && rm -f "${INDEX_FILE}.bak"
    echo "]" >> "${INDEX_FILE}"
fi

rm -f "${TEMP_LIST}"

echo -e "${GREEN}✓ Index file created: ${INDEX_FILE} (${FILE_COUNT} files)${NC}"
echo ""

# List output files by analysis type
echo -e "${YELLOW}Output summary by analysis type:${NC}"
for i in "${!SCRIPTS[@]}"; do
    SCRIPT="${SCRIPTS[$i]}"
    ANALYSIS_NAME="${ANALYSIS_NAMES[$i]}"

    # Determine the suffix used by each script
    case ${SCRIPT} in
        "analyze_sermon_dekker.py")
            SUFFIX="_dekker"
            ;;
        "analyze_aristoteles.py")
            SUFFIX="_aristoteles"
            ;;
        "analyze_schulz_von_thun.py")
            SUFFIX="_schulz_von_thun"
            ;;
        "analyze_kolb_cyclus.py")
            SUFFIX="_kolb"
            ;;
        "analyze_esthetiek.py")
            SUFFIX="_esthetiek"
            ;;
    esac

    COUNT=$(ls -1 "${OUTPUT_DIR}/"*"${SUFFIX}.json" 2>/dev/null | wc -l | tr -d ' ')
    echo -e "  ${ANALYSIS_NAME}: ${GREEN}${COUNT}${NC} files"
done

echo ""
echo -e "${GREEN}All analyses complete!${NC}"
echo ""
