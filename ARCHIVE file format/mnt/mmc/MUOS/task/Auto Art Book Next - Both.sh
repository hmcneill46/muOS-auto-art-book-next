#!/bin/bash
# HELP: Generate folder art for Art Book Next Theme
# ICON: sdcard

. /opt/muos/script/var/func.sh

# Required arguments
MODE="both"

SCREEN_WIDTH=$(GET_VAR device mux/width)
SCREEN_HEIGHT=$(GET_VAR device mux/height)

PANELS_DIR="/mnt/mmc/MUOS/task/.AutoArtBookNext/artwork-default"
WORKING_DIR="/mnt/mmc/MUOS/task/.AutoArtBookNext"
STYLISH_FONT_PATH="/mnt/mmc/MUOS/task/.AutoArtBookNext/FallingSkyBdObl.otf"

# Folder Box Art Required arguments
SD1_ROMS_DIR="/mnt/mmc/ROMS"
SD2_ROMS_DIR="/mnt/sdcard/ROMS"
BOX_ART_DIR="/run/muos/storage/info/catalogue/Folder/box"
LOGOS_DIR="/mnt/mmc/MUOS/task/.AutoArtBookNext/logos"
CORE_INFO_DIR="/run/muos/storage/info/core"
SYSTEM_MAP_PATH="/mnt/mmc/MUOS/task/.AutoArtBookNext/muosESmap.json"
VALID_MUOS_SYSTEM_NAMES_PATH="/mnt/mmc/MUOS/task/.AutoArtBookNext/validMuOsSystemNames.txt"

# Theme Required arguments
THEME_OUTPUT_DIR="/run/muos/storage/theme"
THEME_SHELL_DIR="/mnt/mmc/MUOS/task/.AutoArtBookNext/ThemeShell"
GLYPH_ASSETS_DIR="/mnt/mmc/MUOS/task/.AutoArtBookNext/glyph[5x]"
THEME_NAME="AutoArtBookNext"
TEMPLATE_SCHEME_PATH="/mnt/mmc/MUOS/task/.AutoArtBookNext/TemplateSchemeFile.txt"
LV_FONT_CONV_BIN="/mnt/mmc/MUOS/task/.AutoArtBookNext/lv_font_conv/lv_font_conv_binary"
FONT_RANGES_PATH="/mnt/mmc/MUOS/task/.AutoArtBookNext/lv_font_conv/ranges.txt"
FONT_CACHE_PATH="/mnt/mmc/MUOS/task/.AutoArtBookNext/lv_font_conv/font_ranges_cache.json"
FONT_PATH="/mnt/mmc/MUOS/task/.AutoArtBookNext/FallingSkyBd.otf"

# Optional arguments
BACKGROUND_HEX="#202020"
GAP_BETWEEN_PANELS=5
ICON_HEIGHT_PERCENT=0.5
ICON_WIDTH_PERCENT=0.7
DESELECTED_BRIGHTNESS=0.43
SELECTED_BRIGHTNESS=0.86667
SHADOW_STRENGTH=0
GRADIENT_INTENSITY=0


# Path to the script
SCRIPT="/mnt/mmc/MUOS/task/.AutoArtBookNext/AutoArtBookNext"

# Run the script for SD1 if the SD1_ROMS_DIR exists
if [ -d "$SD1_ROMS_DIR" ]; then
    echo "Running script for SD1..."
    $SCRIPT \
        --mode "$MODE" \
        --screen_height $SCREEN_HEIGHT \
        --screen_width $SCREEN_WIDTH \
        --panels_dir "$PANELS_DIR" \
        --working_dir "$WORKING_DIR" \
        --stylish_font_path "$STYLISH_FONT_PATH" \
        --roms_dir "$SD1_ROMS_DIR" \
        --box_art_dir "$BOX_ART_DIR" \
        --logos_dir "$LOGOS_DIR" \
        --core_info_dir "$CORE_INFO_DIR" \
        --system_map_path "$SYSTEM_MAP_PATH" \
        --valid_muos_system_names_path "$VALID_MUOS_SYSTEM_NAMES_PATH" \
        --theme_output_dir "$THEME_OUTPUT_DIR" \
        --theme_shell_dir "$THEME_SHELL_DIR" \
        --glyph_assets_dir "$GLYPH_ASSETS_DIR" \
        --theme_name "$THEME_NAME" \
        --template_scheme_path "$TEMPLATE_SCHEME_PATH" \
        --lv_font_conv_path "$LV_FONT_CONV_BIN" \
        --font_ranges_path "$FONT_RANGES_PATH" \
        --font_cache_path "$FONT_CACHE_PATH" \
        --font_path "$FONT_PATH" \
        --background_hex "$BACKGROUND_HEX" \
        --gap_between_panels $GAP_BETWEEN_PANELS \
        --icon_height_percent $ICON_HEIGHT_PERCENT \
        --icon_width_percent $ICON_WIDTH_PERCENT \
        --deselected_brightness $DESELECTED_BRIGHTNESS \
        --selected_brightness $SELECTED_BRIGHTNESS \
        --shadow_strength $SHADOW_STRENGTH \
        --gradient_intensity $GRADIENT_INTENSITY
        # --help_off
else
    echo "Skipping SD1: $SD1_ROMS_DIR does not exist."
fi

# Run the Python script for SD2 if the SD2_ROMS_DIR exists
if [ -d "$SD2_ROMS_DIR" ]; then
    echo "Running script for SD2..."
    $SCRIPT \
        --mode "box_art" \
        --screen_height $SCREEN_HEIGHT \
        --screen_width $SCREEN_WIDTH \
        --panels_dir "$PANELS_DIR" \
        --working_dir "$WORKING_DIR" \
        --stylish_font_path "$STYLISH_FONT_PATH" \
        --roms_dir "$SD2_ROMS_DIR" \
        --box_art_dir "$BOX_ART_DIR" \
        --logos_dir "$LOGOS_DIR" \
        --core_info_dir "$CORE_INFO_DIR" \
        --system_map_path "$SYSTEM_MAP_PATH" \
        --valid_muos_system_names_path "$VALID_MUOS_SYSTEM_NAMES_PATH" \
        --background_hex "$BACKGROUND_HEX" \
        --gap_between_panels $GAP_BETWEEN_PANELS \
        --icon_height_percent $ICON_HEIGHT_PERCENT \
        --icon_width_percent $ICON_WIDTH_PERCENT \
        --deselected_brightness $DESELECTED_BRIGHTNESS \
        --selected_brightness $SELECTED_BRIGHTNESS \
        --shadow_strength $SHADOW_STRENGTH \
        --gradient_intensity $GRADIENT_INTENSITY
else
    echo "Skipping SD2: $SD2_ROMS_DIR does not exist."
fi


######################
# If you wish to hide the help in the footer for muxplore and muxlaunch, you can change the following lines above this comment:
#
# --gradient_intensity $GRADIENT_INTENSITY -> --gradient_intensity $GRADIENT_INTENSITY \
# # --help_off -> --help_off
######################

echo "Sync Filesystem"
sync

echo "All Done!"
sleep 2

pkill -CONT muxtask
exit 0
