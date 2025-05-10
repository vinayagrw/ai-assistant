#!/bin/bash

# Set error handling
set -e

# Configuration
DOCS_REPO="https://github.com/duplocloud/docs.git"
DOCS_BRANCH="main"
DOCS_PATH="getting-started-1/application-focussed-interface"
TEMP_DIR="temp_docs"
FINAL_DIR="docs"


echo -e "}Starting documentation fetch process..."

# Create temporary directory
echo "Creating temporary directory..."
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR

# Clone the repository
echo "Cloning DuploCloud documentation repository..."
git clone --depth 1 --branch $DOCS_BRANCH $DOCS_REPO $TEMP_DIR

# Create final directory
echo "Creating final documentation directory..."
rm -rf $FINAL_DIR
mkdir -p $FINAL_DIR

# Copy specific documentation
echo "Copying documentation files..."
cp -r $TEMP_DIR/$DOCS_PATH/* $FINAL_DIR/

# Clean up
echo "Cleaning up temporary files..."
rm -rf $TEMP_DIR

# Verify the copy
if [ -d "$FINAL_DIR" ] && [ "$(ls -A $FINAL_DIR)" ]; then
    echo -e "Documentation successfully fetched!"
    echo "Files are available in the '$FINAL_DIR' directory"
else
    echo -e "Error: Documentation fetch failed"
    exit 1
fi

# List the fetched files
echo -e "\nFetched files:"
ls -R $FINAL_DIR 