#!/bin/bash

# Function to check if gettext is installed
check_gettext() {
    echo "Checking gettext installation..."

    # Check multiple possible paths and commands
    if command -v gettext &> /dev/null; then
        echo "gettext found in PATH"
    else
        echo "Warning: gettext command not found in PATH"
    fi

    if command -v msgfmt &> /dev/null; then
        echo "msgfmt found in PATH"
        MSGFMT_PATH=$(which msgfmt)
        echo "msgfmt location: $MSGFMT_PATH"
    else
        echo "Warning: msgfmt command not found in PATH"
    fi

    # Check if the package is installed
    if dpkg -l | grep -q gettext; then
        echo "gettext package is installed"
        dpkg -l | grep gettext
    else
        echo "gettext package not found in dpkg"
    fi

    # Try to locate the binary
    if [ -f /usr/bin/msgfmt ]; then
        echo "msgfmt exists at /usr/bin/msgfmt"
        ls -l /usr/bin/msgfmt
    fi

    return 0
}

# Function to extract and update messages
extract_messages() {
    echo "Extracting messages..."
    pybabel extract --ignore-dirs=.* -F ../babel.cfg -o messages.pot .
    if [ $? -ne 0 ]; then
        echo "Error in basic extraction"
        return 1
    fi

    echo "Extracting messages with lazy_gettext..."
    pybabel extract --ignore-dirs=.* -F ../babel.cfg -k lazy_gettext -o messages.pot .
    if [ $? -ne 0 ]; then
        echo "Error in lazy_gettext extraction"
        return 1
    fi

    echo "Updating translations..."
    pybabel update -i messages.pot -d ui/translations
    if [ $? -eq 0 ]; then
        echo "Messages successfully extracted and updated"
    else
        echo "Error updating translations"
        return 1
    fi
}

# Function to show statistics
show_statistics() {
    echo "Attempting to show statistics..."

    # Check if the messages.po file exists
    if [ ! -f "ui/translations/fr/LC_MESSAGES/messages.po" ]; then
        echo "Error: messages.po file not found at ui/translations/fr/LC_MESSAGES/messages.po"
        echo "Current directory: $(pwd)"
        echo "Available files in ui/translations directory:"
        ls -R ui/translations/
        return 1
    fi

    # Try to run statistics with full error output
    echo "Running msgfmt statistics..."
    if ! msgfmt --statistics ui/translations/fr/LC_MESSAGES/messages.po 2>&1; then
        echo "Error running msgfmt. Exit code: $?"
        echo "Trying with absolute path..."
        if [ -f /usr/bin/msgfmt ]; then
            /usr/bin/msgfmt --statistics ui/translations/fr/LC_MESSAGES/messages.po 2>&1
        fi
    fi

}

# Function to compile messages
compile_messages() {
    echo "Compiling messages..."
    pybabel compile -d ui/translations
    if [ $? -eq 0 ]; then
        echo "Messages successfully compiled"
    else
        echo "Error compiling messages"
        return 1
    fi
}

# Main menu function
show_menu() {
    echo ""
    echo "******************************"
    echo "Please select an option:"
    echo "1. Extract and update Messages"
    echo "2. Show statistics"
    echo "3. Compile messages"
    echo "4. Exit"
    echo ""
}

echo "--------------------------------------"
echo "Run the script from 'portality' folder"
echo "--------------------------------------"

# Main loop
while true; do
    show_menu
    read -p "Enter your choice (1-4): " choice

    case $choice in
        1)
            extract_messages
            ;;
        2)
            show_statistics
            ;;
        3)
            compile_messages
            ;;
        4)
            echo "Exiting..."
            exit 0
            ;;
        *)
            echo "Invalid option. Please select 1-4"
            ;;
    esac
done