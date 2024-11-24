#!/bin/bash
# HELP: Generate folder art for Art Book Next Theme
# ICON: sdcard

. /opt/muos/script/var/func.sh

# Required arguments
SD1_ROMS_DIR="/mnt/mmc/ROMS"
SD2_ROMS_DIR="/mnt/sdcard/ROMS"
BOX_ART_DIR="/run/muos/storage/info/catalogue/Folder/box"
SLIDES_DIR="/mnt/mmc/MUOS/task/.AutoArtBookNext/artwork-default"
LOGOS_DIR="/mnt/mmc/MUOS/task/.AutoArtBookNext/logos"
CORE_INFO_DIR="/run/muos/storage/info/core"
SYSTEM_MAP_PATH="/mnt/mmc/MUOS/task/.AutoArtBookNext/muosESmap.json"
VALID_MUOS_SYSTEM_NAMES_PATH="/mnt/mmc/MUOS/task/.AutoArtBookNext/validMuOsSystemNames.txt"
LOG_FILE_OUTPUT_DIR="/mnt/mmc/MUOS/task/.AutoArtBookNext"
FONT_PATH="/mnt/mmc/MUOS/task/.AutoArtBookNext/FallingSkyBdObl.otf"

SCREEN_WIDTH=$(GET_VAR device mux/width)
SCREEN_HEIGHT=$(GET_VAR device mux/height)

# Optional arguments
BACKGROUND_HEX="#202020"
GAP_BETWEEN_SLIDES=7
ICON_HEIGHT_PERCENT=0.5
ICON_WIDTH_PERCENT=0.7
DESELECTED_BRIGHTNESS=0.4
SHADOW_STRENGTH=1
GRADIENT_INTENSITY=235


# Path to the script
SCRIPT="/mnt/mmc/MUOS/task/.AutoArtBookNext/AutoArtBookNext"

# Run the script for SD1 if the SD1_ROMS_DIR exists
if [ -d "$SD1_ROMS_DIR" ]; then
    echo "Running script for SD1..."
    $SCRIPT \
        --roms_dir "$SD1_ROMS_DIR" \
        --box_art_dir "$BOX_ART_DIR" \
        --slides_dir "$SLIDES_DIR" \
        --logos_dir "$LOGOS_DIR" \
        --core_info_dir "$CORE_INFO_DIR" \
        --system_map_path "$SYSTEM_MAP_PATH" \
        --valid_muos_system_names_path "$VALID_MUOS_SYSTEM_NAMES_PATH" \
        --log_file_output_dir "$LOG_FILE_OUTPUT_DIR" \
        --font_path "$FONT_PATH" \
        --screen_height $SCREEN_HEIGHT \
        --screen_width $SCREEN_WIDTH \
        --background_hex "$BACKGROUND_HEX" \
        --gap_between_slides $GAP_BETWEEN_SLIDES \
        --icon_height_percent $ICON_HEIGHT_PERCENT \
        --icon_width_percent $ICON_WIDTH_PERCENT \
        --deselected_brightness $DESELECTED_BRIGHTNESS \
        --shadow_strength $SHADOW_STRENGTH \
        --gradient_intensity $GRADIENT_INTENSITY
else
    echo "Skipping SD1: $SD1_ROMS_DIR does not exist."
fi

# Run the Python script for SD2 if the SD2_ROMS_DIR exists
if [ -d "$SD2_ROMS_DIR" ]; then
    echo "Running script for SD2..."
    $SCRIPT \
        --roms_dir "$SD2_ROMS_DIR" \
        --box_art_dir "$BOX_ART_DIR" \
        --slides_dir "$SLIDES_DIR" \
        --logos_dir "$LOGOS_DIR" \
        --core_info_dir "$CORE_INFO_DIR" \
        --system_map_path "$SYSTEM_MAP_PATH" \
        --valid_muos_system_names_path "$VALID_MUOS_SYSTEM_NAMES_PATH" \
        --log_file_output_dir "$LOG_FILE_OUTPUT_DIR" \
        --font_path "$FONT_PATH" \
        --screen_height $SCREEN_HEIGHT \
        --screen_width $SCREEN_WIDTH \
        --background_hex "$BACKGROUND_HEX" \
        --gap_between_slides $GAP_BETWEEN_SLIDES \
        --icon_height_percent $ICON_HEIGHT_PERCENT \
        --icon_width_percent $ICON_WIDTH_PERCENT \
        --deselected_brightness $DESELECTED_BRIGHTNESS \
        --shadow_strength $SHADOW_STRENGTH \
        --gradient_intensity $GRADIENT_INTENSITY
else
    echo "Skipping SD2: $SD2_ROMS_DIR does not exist."
fi

echo "Sync Filesystem"
sync

echo "All Done!"
sleep 2

pkill -CONT muxtask
exit 0
