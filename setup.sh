#!/bin/bash

# Function to log messages
log_message() {
    local message=$1
    echo "$(date +'%Y-%m-%d %H:%M:%S') - $message"
}

# Function to start opensearch in the background
start_opensearch() {
    # Log current directory
    cd ~/Work/opensearch-2.6.0/bin/ || { log_message "Failed to cd to opensearch directory"; return 1; }

    log_message "Running opensearch silently..."
    # Run opensearch in the background and capture output to log file
    ./opensearch > opensearch.log 2>&1
}

# Main setup script
log_message "Running setup script..."

# Start opensearch
start_opensearch

log_message "Setup script completed; Opensearch process stopped."
