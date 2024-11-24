#!/bin/bash

# Variables
MAIN_FILE="main.py"
OUTPUT_NAME="AutoArtBookNext"
ARCHIVE_DIR="ARCHIVE file format/mnt/mmc/MUOS/task/.AutoArtBookNext"
FINAL_DIR="$ARCHIVE_DIR/$OUTPUT_NAME"
BUILD_DIR="AM-Builds"
VERSION_FILE="$BUILD_DIR/version.txt"
ZIP_NAME=""

# Ensure the build directory exists
mkdir -p "$BUILD_DIR"

# Step 1: Manage versioning
if [ ! -f "$VERSION_FILE" ]; then
    echo "1.0.0" > "$VERSION_FILE"
fi

# Read and parse the version
VERSION=$(cat "$VERSION_FILE")
IFS='.' read -r MAJOR MINOR BUILD <<< "$VERSION"

# Increment the build number
BUILD=$((BUILD + 1))
NEW_VERSION="$MAJOR.$MINOR.$BUILD"
echo "$NEW_VERSION" > "$VERSION_FILE"

# Set the ZIP name with the version
ZIP_NAME="AutoArtBookNext-AM[v$NEW_VERSION].zip"

echo "Building version $NEW_VERSION..."

# Step 2: Run pyinstaller
echo "Running pyinstaller on $MAIN_FILE..."
pyinstaller --onefile --name "$OUTPUT_NAME" "$MAIN_FILE"

# Check if pyinstaller succeeded
if [ $? -ne 0 ]; then
    echo "PyInstaller failed. Exiting..."
    exit 1
fi

# Step 3: Move the binary to the target directory
echo "Moving the resulting binary to $FINAL_DIR..."
mkdir -p "$ARCHIVE_DIR"
mv -f "dist/$OUTPUT_NAME" "$FINAL_DIR"

# Step 4: Zip the mnt directory
echo "Creating a zip archive of the mnt directory..."
cd "ARCHIVE file format" || exit
zip -r "../$BUILD_DIR/$ZIP_NAME" mnt
cd ..

# Step 5: Clean up
echo "Cleaning up temporary files..."
rm -rf build dist __pycache__ "$OUTPUT_NAME.spec"

echo "Build and packaging complete! Saved as $BUILD_DIR/$ZIP_NAME"
