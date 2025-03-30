#!/bin/bash

# Script to push changes to GitHub repository
# Repository: https://github.com/prabhavjain2004/business.git

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to display messages with color
print_message() {
    echo -e "${2}${1}${NC}"
}

# Fix for Windows path issues in Git Bash/MINGW
# Set explicit HOME directory to avoid path encoding issues
if [[ "$(uname -s)" == *"MINGW"* ]] || [[ "$(uname -s)" == *"MSYS"* ]]; then
    print_message "Windows environment detected, setting up Git configuration..." "$YELLOW"
    # Get current username without special characters
    WIN_USERNAME=$(whoami | tr -d '\r')
    # Set HOME environment variable explicitly
    export HOME="/c/Users/$WIN_USERNAME"
    # Create .gitconfig if it doesn't exist
    if [ ! -f "$HOME/.gitconfig" ]; then
        touch "$HOME/.gitconfig"
        print_message "Created .gitconfig file in $HOME" "$GREEN"
    fi
    print_message "Using HOME directory: $HOME" "$GREEN"
fi

# Check if git is installed
if ! command -v git &> /dev/null; then
    print_message "Git is not installed. Please install Git first." "$RED"
    exit 1
fi

# Check if .git directory exists, if not initialize git
if [ ! -d ".git" ]; then
    print_message "Initializing Git repository..." "$YELLOW"
    git init
    if [ $? -ne 0 ]; then
        print_message "Failed to initialize Git repository." "$RED"
        exit 1
    fi
    print_message "Git repository initialized successfully." "$GREEN"
fi

# Check if the remote repository is already set up
if ! git remote | grep -q "origin"; then
    print_message "Adding remote repository..." "$YELLOW"
    # Use GIT_CONFIG_NOSYSTEM=1 to avoid system config issues
    GIT_CONFIG_NOSYSTEM=1 git remote add origin https://github.com/prabhavjain2004/business.git
    if [ $? -ne 0 ]; then
        print_message "Failed to add remote repository." "$RED"
        exit 1
    fi
    print_message "Remote repository added successfully." "$GREEN"
else
    # Check if the remote URL is correct
    REMOTE_URL=$(GIT_CONFIG_NOSYSTEM=1 git remote get-url origin 2>/dev/null)
    if [ "$REMOTE_URL" != "https://github.com/prabhavjain2004/business.git" ]; then
        print_message "Updating remote URL..." "$YELLOW"
        GIT_CONFIG_NOSYSTEM=1 git remote set-url origin https://github.com/prabhavjain2004/business.git
        if [ $? -ne 0 ]; then
            print_message "Failed to update remote URL." "$RED"
            exit 1
        fi
        print_message "Remote URL updated successfully." "$GREEN"
    fi
fi

# Ask for commit message
read -p "Enter commit message: " commit_message

if [ -z "$commit_message" ]; then
    commit_message="Update $(date +"%Y-%m-%d %H:%M:%S")"
    print_message "No commit message provided. Using default: $commit_message" "$YELLOW"
fi

# Add all changes
print_message "Adding all changes..." "$YELLOW"
GIT_CONFIG_NOSYSTEM=1 git add .
if [ $? -ne 0 ]; then
    print_message "Failed to add changes." "$RED"
    exit 1
fi
print_message "Changes added successfully." "$GREEN"

# Commit changes
print_message "Committing changes..." "$YELLOW"
GIT_CONFIG_NOSYSTEM=1 git commit -m "$commit_message"
if [ $? -ne 0 ]; then
    print_message "Failed to commit changes." "$RED"
    exit 1
fi
print_message "Changes committed successfully." "$GREEN"

# Push changes
print_message "Pushing changes to remote repository..." "$YELLOW"
GIT_CONFIG_NOSYSTEM=1 git push -u origin master
if [ $? -ne 0 ]; then
    print_message "Failed to push changes. Trying with 'main' branch instead..." "$YELLOW"
    GIT_CONFIG_NOSYSTEM=1 git push -u origin main
    if [ $? -ne 0 ]; then
        print_message "Failed to push changes to remote repository." "$RED"
        print_message "You might need to set up authentication or check your branch name." "$YELLOW"
        exit 1
    fi
fi
print_message "Changes pushed successfully!" "$GREEN"

print_message "All done! Your changes have been pushed to https://github.com/prabhavjain2004/business.git" "$GREEN"
