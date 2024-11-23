#!/bin/bash

# Required arguments
ROMS_DIR=""
BOX_ART_DIR=""
SLIDES_DIR=""
LOGOS_DIR=""
CORE_INFO_DIR=""
SYSTEM_MAP_PATH=""
VALID_MUOS_SYSTEM_NAMES_PATH=""
SCREEN_WIDTH=640
SCREEN_HEIGHT=480

# Optional arguments
BACKGROUND_HEX="#000000"
GAP_BETWEEN_SLIDES=10
ICON_HEIGHT_PERCENT=0.5
ICON_WIDTH_PERCENT=0.7
DESELECTED_BRIGHTNESS=0.2
SHADOW_STRENGTH=1

# Path to the Python script
PYTHON_SCRIPT=""

# Run the Python script with all arguments
python3 $PYTHON_SCRIPT \
    --roms_dir "$ROMS_DIR" \
    --box_art_dir "$BOX_ART_DIR" \
    --slides_dir "$SLIDES_DIR" \
    --logos_dir "$LOGOS_DIR" \
    --core_info_dir "$CORE_INFO_DIR" \
    --system_map_path "$SYSTEM_MAP_PATH" \
    --valid_muos_system_names_path "$VALID_MUOS_SYSTEM_NAMES_PATH" \
    --screen_height $SCREEN_HEIGHT \
    --screen_width $SCREEN_WIDTH \
    --background_hex "$BACKGROUND_HEX" \
    --gap_between_slides $GAP_BETWEEN_SLIDES \
    --icon_height_percent $ICON_HEIGHT_PERCENT \
    --icon_width_percent $ICON_WIDTH_PERCENT \
    --deselected_brightness $DESELECTED_BRIGHTNESS \
    --shadow_strength $SHADOW_STRENGTH
