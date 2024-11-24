#!/bin/bash

# Variables
MAIN_FILE="main.py"
OUTPUT_NAME="AutoArtBookNext"
ARCHIVE_DIR="ARCHIVE file format/mnt/mmc/MUOS/task/.AutoArtBookNext"
FINAL_DIR="$ARCHIVE_DIR/$OUTPUT_NAME"
ZIP_NAME="AutoArtBookNext - AM.zip"

# Step 1: Run pyinstaller
echo "Running pyinstaller on $MAIN_FILE..."
pyinstaller --onefile --name "$OUTPUT_NAME" "$MAIN_FILE"

# Check if pyinstaller succeeded
if [ $? -ne 0 ]; then
    echo "PyInstaller failed. Exiting..."
    exit 1
fi

# Step 2: Move the binary to the target directory
echo "Moving the resulting binary to $FINAL_DIR..."
mkdir -p "$ARCHIVE_DIR"
mv -f "dist/$OUTPUT_NAME" "$FINAL_DIR"

# Step 3: Zip the mnt directory
echo "Creating a zip archive of the mnt directory..."
cd "ARCHIVE file format" || exit
zip -r "$ZIP_NAME" mnt

# Step 4: Clean up
echo "Cleaning up temporary files..."
cd ..
rm -rf build dist __pycache__ "$OUTPUT_NAME.spec"

echo "Build and packaging complete!"
