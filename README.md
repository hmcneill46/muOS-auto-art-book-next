# Auto Art Book Next for muOS

**Auto Art Book Next** is a script designed for enhancing your device's interface by customizing **theme** and **box art** settings. This tool is primarily intended to be run on the device using the pre-compiled releases provided on the [Latest Release](https://github.com/hmcneill46/muOS-auto-art-book-next/releases/latest) page. However, if you prefer, you can also run the Python script manually.

---

## 🚀 Features

- **Theme Generation**: Generates a new theme in the style of Art Book Next for your device.
- **Box Art Generation**: Automatically Generates folder box art to match the Art Book Next style.
- **Easy-to-Use Scripts**: Precompiled and ready to run directly on your device.

---

## 📥 Using Precompiled Releases

### On-Device Instructions

1. **Download the Release**  
   Visit the [Latest Release](https://github.com/hmcneill46/muOS-auto-art-book-next/releases/latest) page and download the latest `.zip` file.

2. **Installation**  
   - Place the `.zip` file in the `ARCHIVE` folder of your SD1 or SD2 card.
   - Use the **Archive Manager app** to install the file on your device.
     - This process will place scripts in the `MUOS/task/` directory.

3. **Run the Scripts**  
   - Open the **Task Toolkit app** and choose a script to run:
     - `Auto Art Book Next - Both`: Installs both the theme and box art.
     - `Auto Art Book Next - Theme`: Installs only the theme.
     - `Auto Art Book Next - Folders`: Updates only the box art.

4. **Apply and Configure**  
   - After running the script(s), choose the new theme (`AutoArtBookNext`) in your **Theme Picker**.
   - Adjust the following settings for optimal results:
     - `General Settings -> Interface Options -> Content Box Art` → **Fullscreen + Front**  
     - `General Settings -> Interface Options -> Content Box Art Alignment` → **Middle Right**

---

## 🛠️ Running the Python Script

To manually execute the script, ensure you have Python 3 installed and follow the steps below.

### Usage

Run the script with the following syntax:  
```bash
python3 main.py [args]
```

### Arguments

| Argument                             | Description                                                                                  | Required for Mode   |
|--------------------------------------|----------------------------------------------------------------------------------------------|---------------------|
| `--mode {box_art,theme,both}`        | Specifies what to generate: `box_art`, `theme`, or `both`.                                   | All                |
| `--screen_height SCREEN_HEIGHT`      | Screen height in pixels.                                                                     | All                |
| `--screen_width SCREEN_WIDTH`        | Screen width in pixels.                                                                      | All                |
| `--panels_dir PANELS_DIR`            | Path to the system image panels directory.                                                   | All                |
| `--working_dir WORKING_DIR`          | Directory for temporary files.                                                              | All                |
| `--stylish_font_path STYLISH_FONT_PATH` | Path to the stylish font file.                                                             | All                |
| `--roms_dir ROMS_DIR`                | Path to the ROMs directory. Required if `mode` includes `box_art`.                          | `box_art`, `both`  |
| `--box_art_dir BOX_ART_DIR`          | Path to the box art directory. Required if `mode` includes `box_art`.                       | `box_art`, `both`  |
| `--logos_dir LOGOS_DIR`              | Path to the system image logos directory. Required if `mode` includes `box_art`.            | `box_art`, `both`  |
| `--core_info_dir CORE_INFO_DIR`      | Folder where core associations are stored. Required if `mode` includes `box_art`.           | `box_art`, `both`  |
| `--system_map_path SYSTEM_MAP_PATH`  | File mapping muOS to ES system names. Required if `mode` includes `box_art`.                | `box_art`, `both`  |
| `--valid_muos_system_names_path VALID_MUOS_SYSTEM_NAMES_PATH` | Valid muOS system names file. Required if `mode` includes `box_art`. | `box_art`, `both`  |
| `--theme_shell_dir THEME_SHELL_DIR`  | Directory containing the theme shell. Required if `mode` includes `theme`.                  | `theme`, `both`    |
| `--theme_output_dir THEME_OUTPUT_DIR`| Output directory for themes. Required if `mode` includes `theme`.                           | `theme`, `both`    |
| `--theme_name THEME_NAME`            | Name of the theme to generate. Required if `mode` includes `theme`.                         | `theme`, `both`    |
| `--template_scheme_path TEMPLATE_SCHEME_PATH` | Path to the theme's template scheme file. Required if `mode` includes `theme`.  | `theme`, `both`    |
| `--glyph_assets_dir GLYPH_ASSETS_DIR`| Directory containing glyph assets. Required if `mode` includes `theme`.                     | `theme`, `both`    |
| `--lv_font_conv_path LV_FONT_CONV_PATH` | Path to the `lv_font_conv` tool. Required if `mode` includes `theme`.                     | `theme`, `both`    |
| `--font_ranges_path FONT_RANGES_PATH`| Path to file defining valid font ASCII ranges. Required if `mode` includes `theme`.         | `theme`, `both`    |
| `--font_cache_path FONT_CACHE_PATH`  | Path to cache for valid font ranges. Required if `mode` includes `theme`.                   | `theme`, `both`    |
| `--font_path FONT_PATH`              | Path to a non-stylish font file. Required if `mode` includes `theme`.                        | `theme`, `both`    |
| `--help_off`                         | Disables the help footer in `muxlaunch` and `muxplore`. Defaults to `False`.                 | Optional           |
| `--background_hex BACKGROUND_HEX`    | Background color in hex format (default: `#000000`).                                        | Optional           |
| `--gap_between_panels GAP_BETWEEN_PANELS` | Gap between panels in pixels (default: `7`).                                            | Optional           |
| `--icon_height_percent ICON_HEIGHT_PERCENT` | Icon height as a percentage of screen height (default: `0.5`).                          | Optional           |
| `--icon_width_percent ICON_WIDTH_PERCENT` | Icon width as a percentage of screen width (default: `0.7`).                             | Optional           |
| `--selected_brightness SELECTED_BRIGHTNESS` | Brightness of selected folders as a percentage (default: `87%`: `0.87`).              | Optional           |
| `--deselected_brightness DESELECTED_BRIGHTNESS` | Brightness of deselected folders as a percentage (default: `43%`: `0.43`).          | Optional           |
| `--shadow_strength SHADOW_STRENGTH`  | Drop shadow strength (default: `1`, range: `0-5`).                                         | Optional           |
| `--gradient_intensity GRADIENT_INTENSITY` | Gradient overlay intensity (default: `235`, range: `0-255`).                           | Optional           |

---

## 🏗️ Building the Package

To build the package yourself, run the `build_and_package.sh` script in an **aarch64 Linux environment**:  
```bash
./build_and_package.sh
```

This will generate the `.zip` file for installation on your device, and try to send the file to your device via ADB or MTP.
