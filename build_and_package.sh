#!/bin/bash

# Variables
MAIN_FILE="main.py"
OUTPUT_NAME="AutoArtBookNext"
ARCHIVE_DIR="ARCHIVE file format/mnt/mmc/MUOS/task/.AutoArtBookNext"
FINAL_DIR="$ARCHIVE_DIR/$OUTPUT_NAME"
BUILD_DIR="AM-Builds"
VERSION_FILE="$BUILD_DIR/version.txt"
ZIP_NAME=""
BINARY_NAME=""

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

# Set the ZIP name and binary name with the version
ZIP_NAME="AutoArtBookNext-AM[v$NEW_VERSION].zip"
BINARY_NAME="AutoArtBookNext-Binary[v$NEW_VERSION]"

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

# Step 5: Move the binary to the build directory with versioned name
echo "Moving and renaming the binary to $BUILD_DIR/$BINARY_NAME..."
mv -f "$FINAL_DIR" "$BUILD_DIR/$BINARY_NAME"

# Step 6: Transfer ZIP to device (if possible)

ZIP_PATH="$BUILD_DIR/$ZIP_NAME"
ADB_DESTINATION="/mnt/mmc/ARCHIVE/"

echo "Attempting to transfer the ZIP file to the connected device..."

if adb devices | grep -q "device$"; then
    echo "ADB device detected. Transferring ZIP file..."
    adb push "$ZIP_PATH" "$ADB_DESTINATION"
    if [ $? -eq 0 ]; then
        echo "File successfully transferred via ADB to $ADB_DESTINATION."
    else
        echo "ADB transfer failed."
    fi
else
    echo "No ADB device detected."
fi

MTP_MOUNT=$(ls -d /run/user/$(id -u)/gvfs/mtp:* 2>/dev/null | head -n 1)
if [ -n "$MTP_MOUNT" ]; then
    echo "MTP device found at $MTP_MOUNT"
    echo "Transferring ZIP file..."
    cp "$ZIP_PATH" "${MTP_MOUNT}/SD1/ARCHIVE/"
    echo "MTP Transfer complete."
else
    echo "MTP device not mounted."
fi

# Step 7: Clean up
echo "Cleaning up temporary files..."
rm -rf build dist __pycache__ "$OUTPUT_NAME.spec"

echo "Build, packaging, and file transfer complete!"
echo "Saved as: $BUILD_DIR/$ZIP_NAME"
echo "Binary saved as: $BUILD_DIR/$BINARY_NAME"
