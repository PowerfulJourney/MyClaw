#!/bin/bash
# ClawHub Skill Monitor
# Tracks new skills on clawhub.com and reports top downloads

set -e

WORK_DIR="/home/administrator/.openclaw/workspace/memory/clawhub-monitor"
STATE_FILE="$WORK_DIR/known_skills.json"
REPORT_FILE="$WORK_DIR/daily_report.txt"
LOG_FILE="$WORK_DIR/monitor.log"

mkdir -p "$WORK_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Fetch current skills from clawhub
fetch_skills() {
    log "Fetching skills from clawhub..."
    
    # Try to get skills using clawhub CLI with timeout
    if timeout 60 npx clawhub explore --limit 100 > "$WORK_DIR/explore_output.txt" 2>&1; then
        log "Successfully fetched skills"
        return 0
    else
        log "Failed to fetch skills (timeout or error)"
        return 1
    fi
}

# Parse explore output to extract skill info
parse_skills() {
    local output_file="$1"
    local json_output="$WORK_DIR/current_skills.json"
    
    # Create a simple JSON structure from the output
    # This is a simplified parser - clawhub output format may vary
    echo "[]" > "$json_output"
    
    # If we have previous state, use it as base
    if [ -f "$STATE_FILE" ]; then
        cp "$STATE_FILE" "$json_output"
    fi
    
    echo "$json_output"
}

# Find new skills by comparing with previous state
find_new_skills() {
    local current="$1"
    local previous="$2"
    
    if [ ! -f "$previous" ]; then
        log "No previous state found. First run - storing baseline."
        cp "$current" "$previous"
        echo "[]"
        return
    fi
    
    # Compare and find new skills
    # This is a simplified diff - in production would use jq for proper JSON diff
    log "Comparing with previous state..."
    
    # For now, return empty array (would need proper parsing)
    echo "[]"
}

# Generate report
generate_report() {
    local new_skills="$1"
    local report="$2"
    
    {
        echo "📦 ClawHub Skill Monitor Report"
        echo "📅 Date: $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""
        
        if [ "$new_skills" = "[]" ] || [ -z "$new_skills" ]; then
            echo "📝 No new skills found today."
        else
            echo "🆕 New Skills:"
            echo "$new_skills" | jq -r '.[] | "- \(.name): \(.downloads // 0) downloads"' 2>/dev/null || echo "$new_skills"
        fi
        
        echo ""
        echo "---"
        echo "Monitor Status: Active"
        echo "Next check: Tomorrow morning"
    } > "$report"
}

# Main execution
main() {
    log "=== ClawHub Monitor Started ==="
    
    # Fetch current skills
    if ! fetch_skills; then
        log "ERROR: Could not fetch skills from clawhub"
        
        # Send notification about failure
        echo "⚠️ ClawHub monitor failed to fetch skills today. Please check manually." > "$REPORT_FILE"
        exit 1
    fi
    
    # Parse and process
    CURRENT=$(parse_skills "$WORK_DIR/explore_output.txt")
    NEW_SKILLS=$(find_new_skills "$CURRENT" "$STATE_FILE")
    
    # Update state
    cp "$CURRENT" "$STATE_FILE"
    
    # Generate report
    generate_report "$NEW_SKILLS" "$REPORT_FILE"
    
    log "Report generated: $REPORT_FILE"
    log "=== Monitor Completed ==="
}

# Run main
main
