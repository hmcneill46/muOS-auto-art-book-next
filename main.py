import argparse
import os
import subprocess
import sys
import json
import logging
import re
import shutil
import hashlib
from PIL import Image, ImageDraw, ImageEnhance, ImageOps, ImageFilter, ImageFont

def ceil(n):
    """
    Returns the smallest integer greater than or equal to n.
    :param n: Number to round up.
    :return: Rounded up integer.
    """
    return int(n) if n == int(n) else int(n) + 1
def floor(n):
    """
    Returns the largest integer less than or equal to n.
    :param n: Number to round down.
    :return: Rounded down integer.
    """
    return int(n) if n >= 0 or n == int(n) else int(n) - 1


def setup_logger(log_file_output_dir, log_file_name="AutoArtBookNextLog.log"):
    # Ensure the output directory exists
    os.makedirs(log_file_output_dir, exist_ok=True)
    
    # Define the full path to the log file
    log_file_path = os.path.join(log_file_output_dir, log_file_name)
    
    # Create a custom logging configuration
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.DEBUG,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),  # Send logs to the console
        ],
    )
    
    # Return the logger instance
    return logging.getLogger(__name__)

class Config(object):
    def __init__(self, args, logger):
        self.logger = logger
        self.roms_dir = args.roms_dir
        self.box_art_dir = args.box_art_dir
        self.panels_dir = args.panels_dir
        self.logos_dir = args.logos_dir
        self.core_info_dir = args.core_info_dir
        self.system_map_path = args.system_map_path
        with open(self.system_map_path, "r") as file:
            self.system_map = json.load(file)
        self.valid_muos_system_names_path = args.valid_muos_system_names_path
        self.font_path = args.font_path
        self.screen_height = args.screen_height
        self.screen_width = args.screen_width
        self.background_hex = args.background_hex
        self.gap_between_panels = args.gap_between_panels
        self.icon_height_percent = args.icon_height_percent
        self.icon_width_percent = args.icon_width_percent
        self.max_icon_height = (self.screen_height * self.icon_height_percent)
        self.max_icon_width = (self.screen_width * self.icon_width_percent) 
        self.deselected_brightness = args.deselected_brightness
        self.shadow_strength = args.shadow_strength
        self.gradient_intensity = args.gradient_intensity

        self.folders = get_folders(self.roms_dir)
        self.folder_console_associations = get_folder_core_associations(self.folders, self.core_info_dir)
        self.example_panel_image = Image.open(os.path.join(self.panels_dir, f"_default.png")).convert("RGBA")
        self.panel_height = self.example_panel_image.height
        self.panel_width = self.example_panel_image.width

        first_row = list(self.example_panel_image.getdata())[0:self.example_panel_image.width]
        alpha_threshold = 200
        self.real_panel_width = sum(1 for pixel in first_row if pixel[3] > alpha_threshold)

        self.gradient_overlay_image = None
        self.special_cases = {r'^ngp$': 'es_systems/ngp',
                              r'neo.*?geo.*?pocket(?!.*?colou?r)': 'es_systems/ngp'}
    def log_config(self):
        # Log directories
        self.logger.info("=" * 50)  # Divider line
        self.logger.info("Directories:")
        self.logger.info("=" * 50)
        self.logger.info(f"ROMs Directory: {self.roms_dir}")
        self.logger.info(f"Box Art Directory: {self.box_art_dir}")
        self.logger.info(f"System Image Panels Directory: {self.panels_dir}")
        self.logger.info(f"System Image Logos Directory: {self.logos_dir}")
        self.logger.info(f"Folder Core Association Directory: {self.core_info_dir}")

        self.logger.info("=" * 50)  # Divider line
        self.logger.info("Device Settings:")
        self.logger.info("=" * 50)

        self.logger.info(f"Screen Width: {self.screen_width}")
        self.logger.info(f"Screen Height: {self.screen_height}")

        # Log results
        self.logger.info("=" * 50)  # Divider line
        self.logger.info("Optional settings:")
        self.logger.info("=" * 50)
        self.logger.info(f"  Background colour: {self.background_hex}")
        self.logger.info(f"  Gap between panels: {self.gap_between_panels}px")
        self.logger.info(f"  Icon height max percent of screen height: {self.icon_height_percent*100}%")
        self.logger.info(f"  Icon width max percent of screen width: {self.icon_width_percent*100}%")
        self.logger.info(f"  Calculated max icon height: {self.max_icon_height}px")
        self.logger.info(f"  Calculated max icon width: {self.max_icon_width}px")
    def log_associations(self):
        for folder in self.folder_console_associations.keys():
            self.logger.info(f"  {folder}: {self.folder_console_associations[folder]}")
    def get_gradient_overlay_image(self, width, height, start_colour, end_colour, gradient_height_percent):
        if self.gradient_overlay_image is None:
            self.gradient_overlay_image = generateGradientImage(width, height, start_colour, end_colour, gradient_height_percent, self)
        return self.gradient_overlay_image
    def update_folders(self, folders):
        self.folders = folders
        self.folder_console_associations = get_folder_core_associations(self.folders, self.core_info_dir)

def generateGradientImage(width, height, start_colour, end_colour, gradient_height_percent,config:Config):
    """
    Generate a smooth vertical gradient image using PIL.
    
    Parameters:
        width (int): The width of the image.
        height (int): The height of the image.
        start_colour (tuple): RGBA tuple for the colour at the top of the gradient.
        end_colour (tuple): RGBA tuple for the colour at the bottom of the gradient.
        gradient_height_percent (float): The percentage of the image height that the gradient covers (0.0 to 1.0).
    
    Returns:
        Image: A PIL Image object containing the gradient.
    """
    config.logger.info(f"Generating Gradient Image")
    # Create a new image with an RGBA mode
    gradient = Image.new("RGBA", (width, height), end_colour)
    if start_colour != end_colour:
        gradient_height = int(height * gradient_height_percent)

        # Calculate the colour difference for the gradient
        delta_r = end_colour[0] - start_colour[0]
        delta_g = end_colour[1] - start_colour[1]
        delta_b = end_colour[2] - start_colour[2]
        delta_a = end_colour[3] - start_colour[3]

        for y in range(gradient_height):
            # Calculate the interpolation factor
            t = y / gradient_height
            # Interpolate the colour
            r = int(start_colour[0] + t * delta_r)
            g = int(start_colour[1] + t * delta_g)
            b = int(start_colour[2] + t * delta_b)
            a = int(start_colour[3] + t * delta_a)

            # Draw a horizontal line with the calculated colour
            for x in range(width):
                gradient.putpixel((x, y), (r, g, b, a))

    return gradient


def generateFolderImage(folder_name:str, config:Config):
    """
    Generate a folder image for the given folder name. In the style of Art Book Next.
    :param folder_name: Name of the folder.
    :param config: Configuration object.
    :return: Image object.
    """
    config.logger.info(f"Generating Image for {folder_name}")
    height_multiplier = config.panel_height/config.screen_height
    width_multiplier = config.panel_width/config.screen_width
    rendered_image_multiplier = max(height_multiplier, width_multiplier)
    rendered_image_width, rendered_image_height = int(config.screen_width*rendered_image_multiplier), int(config.screen_height*rendered_image_multiplier)
    image = Image.new("RGBA", (rendered_image_width, rendered_image_height), config.background_hex)

    muOS_system_name = config.folder_console_associations[folder_name.lower()]

    all_es_item_names = []
    for working_folder_name in config.folders:
        working_muOS_system_name = config.folder_console_associations[working_folder_name.lower()]
        # draw the correct panel image in the middle of the screen
        if os.path.exists(os.path.join(config.panels_dir, f"{working_folder_name.lower()}.png")):
            working_es_system_image_name = f"{working_folder_name.lower()}.png"
        elif os.path.exists(os.path.join(config.panels_dir, f"auto-{working_folder_name.lower()}.png")):
            working_es_system_image_name= f"auto-{working_folder_name.lower()}.png"
        else:
            working_es_system_image_name = get_es_system_name(working_folder_name, working_muOS_system_name, config)
        all_es_item_names.append(working_es_system_image_name)

    combinedPanelImage = generateArtBookNextImage(config.folders.index(folder_name),
                                                  all_es_item_names,
                                                  rendered_image_width,
                                                  rendered_image_height,
                                                  rendered_image_multiplier,
                                                  config.gap_between_panels,
                                                  config.real_panel_width,
                                                  config.panels_dir,
                                                  config.panel_width,
                                                  config.panel_height,
                                                  config.deselected_brightness)
    image.alpha_composite(combinedPanelImage, (0,0))
    
    gradient = config.get_gradient_overlay_image(image.width,image.height,(0,0,0,config.gradient_intensity),(0,0,0,0),0.75)
    image.alpha_composite(gradient,(0,0))

    if check_for_special_case(folder_name, config.special_cases) != None:
        special_muOS_system_name = check_for_special_case(folder_name, config.special_cases)
        logo_image = generateLogoImage(folder_name,
                                       special_muOS_system_name,
                                       rendered_image_width,
                                       rendered_image_height,
                                       config.logger,
                                       config.logos_dir,
                                       int(config.max_icon_height*rendered_image_multiplier),
                                       int(config.max_icon_width*rendered_image_multiplier),
                                       config.font_path,
                                       config.shadow_strength)
    else:
        logo_image = generateLogoImage(folder_name,
                                       muOS_system_name,
                                       rendered_image_width,
                                       rendered_image_height,
                                       config.logger,
                                       config.logos_dir,
                                       int(config.max_icon_height*rendered_image_multiplier),
                                       int(config.max_icon_width*rendered_image_multiplier),
                                       config.font_path,
                                       config.shadow_strength)
    image.alpha_composite(logo_image, (0,0))

    return(image.resize((config.screen_width, config.screen_height), Image.LANCZOS))

def generateMenuImage(index, menu_names, es_system_images, config:Config):
    """
    Generate a folder image for the given folder name. In the style of Art Book Next.
    :param folder_name: Name of the folder.
    :param config: Configuration object.
    :return: Image object.
    """
    config.logger.info(f"Generating Menu Image for {menu_names[index]}")
    height_multiplier = config.panel_height/config.screen_height
    width_multiplier = config.panel_width/config.screen_width
    rendered_image_multiplier = max(height_multiplier, width_multiplier)
    rendered_image_width, rendered_image_height = int(config.screen_width*rendered_image_multiplier), int(config.screen_height*rendered_image_multiplier)
    image = Image.new("RGBA", (rendered_image_width, rendered_image_height), config.background_hex)

    combinedPanelImage = generateArtBookNextImage(index,
                                                  es_system_images,
                                                  rendered_image_width,
                                                  rendered_image_height,
                                                  rendered_image_multiplier,
                                                  config.gap_between_panels,
                                                  config.real_panel_width,
                                                  config.panels_dir,
                                                  config.panel_width,
                                                  config.panel_height,
                                                  config.deselected_brightness)
    image.alpha_composite(combinedPanelImage, (0,0))
    
    gradient = config.get_gradient_overlay_image(image.width,image.height,(0,0,0,config.gradient_intensity),(0,0,0,0),0.75)
    image.alpha_composite(gradient,(0,0))

    return(image.resize((config.screen_width, config.screen_height), Image.LANCZOS))

def fillTempThemeFolder(theme_folder_dir, template_scheme_file_path, lv_font_conv, ranges_file, cache_file, config:Config):
    """
    Generate a folder image for the given folder name. In the style of Art Book Next.
    :param folder_name: Name of the folder.
    :param config: Configuration object.
    :return: Image object.
    """
    config.logger.info(f"Generating Theme Images")

    muxlaunch_images = {
            "explore": "auto-allgames.png",
            "favourite": "auto-favorites.png",
            "history": "auto-lastplayed.png",
            "apps": "library.png",
            "info": "apfm1000.png",
            "config": "tools.png",
            "reboot": "auto-simulation.png",
            "shutdown": "sufami.png"
        }
    muxlaunch_image_dir = os.path.join(theme_folder_dir, "image", "static", "muxlaunch")
    os.makedirs(muxlaunch_image_dir, exist_ok=True)
    for index, (item, image) in enumerate(muxlaunch_images.items()):
        current_theme_image = generateMenuImage(index, list(muxlaunch_images.keys()), list(muxlaunch_images.values()), config)
        current_theme_image.save(os.path.join(muxlaunch_image_dir, f"{item}.png"))
        if index == 0:
            preview_size = (int(config.screen_width*0.45), int(config.screen_height*0.45))
            if config.screen_width == 720 and config.screen_height == 720:
                preview_size = (340, 340)
            logo = generateLogoImage("Explore Content",
                                     "default",
                                     preview_size[0],
                                     preview_size[1],
                                     config.logger,
                                     config.logos_dir,
                                     preview_size[1]*config.icon_height_percent,
                                     preview_size[0]*config.icon_width_percent,
                                     config.font_path,
                                     config.shadow_strength)
            current_theme_image = current_theme_image.resize(preview_size, Image.LANCZOS)
            current_theme_image.alpha_composite(logo, (0,0))
            current_theme_image.save(os.path.join(theme_folder_dir, "preview.png"))
        config.logger.info(f"Successfully generated theme image for system: {item}")
    fillSchemeFiles(os.path.join(theme_folder_dir, "scheme"), template_scheme_file_path, config)

    os.makedirs(os.path.join(theme_folder_dir,"image","wall"), exist_ok=True)

    defaultimage = generatePilImageDefaultScreen(config.background_hex[1:],config.screen_width,config.screen_height)
    defaultimage.save(os.path.join(theme_folder_dir,"image","wall","default.png"), format='PNG')

    chargingimage = generatePilImageBootScreen(config.background_hex[1:],
                                               "ffffff",
                                               "Charging...",
                                               config.screen_width,
                                               config.screen_height,
                                               config.font_path)
    chargingimage.save(os.path.join(theme_folder_dir,"image","wall","muxcharge.png"), format='PNG')

    loadingimage = generatePilImageBootScreen(config.background_hex[1:],
                                              "ffffff",
                                              "Loading...",
                                              config.screen_width,
                                              config.screen_height,
                                              config.font_path)
    loadingimage.save(os.path.join(theme_folder_dir,"image","wall","muxstart.png"), format='PNG')

    shutdownimage = generatePilImageBootScreen(config.background_hex[1:],
                                               "ffffff",
                                               "Shutting Down...",
                                               config.screen_width,
                                               config.screen_height,
                                               config.font_path)
    shutdownimage.save(os.path.join(theme_folder_dir,"image","shutdown.png"), format='PNG')

    rebootimage = generatePilImageBootScreen(config.background_hex[1:],
                                             "ffffff",
                                             "Rebooting...",
                                             config.screen_width,
                                             config.screen_height,
                                             config.font_path)
    rebootimage.save(os.path.join(theme_folder_dir,"image","reboot.png"), format='PNG')

    bootlogoimage = generatePilImageBootScreen(config.background_hex[1:],
                                               "ffffff",
                                               "muOS",
                                               config.screen_width,
                                               config.screen_height,
                                               config.font_path)
    bootlogoimage.save(os.path.join(theme_folder_dir,"image","bootlogo.bmp"), format='BMP')

    fillFontFolder(os.path.join(theme_folder_dir, "font"),
                   config.font_path,
                   lv_font_conv,
                   ranges_file,
                   cache_file,
                   config)

def fillFontFolder(font_folder_dir, font_path, lv_font_conv, ranges_file, cache_file, config:Config):
    font_size = {}
    font_size["header"] = {}
    font_size["footer"] = {}
    font_size["panel"] = {}

    font_size["header"]["default"] = 20
    font_size["footer"]["default"] = 20
    font_size["panel"]["default"] = 20

    font_size["panel"]["muxtheme"] = 18
    font_size["panel"]["muxarchive"] = 18

    scaled_font_size = min(
        150 * (config.screen_width / 1440),
        150 * (config.screen_height / 810),
    )
    font_size["panel"]["muxlaunch"] = scaled_font_size

    for folder in font_size.keys():
        for font in font_size[folder].keys():
            font_size_int = int(font_size[folder][font])
            font_name = f"{font}.bin"
            output_file = os.path.join(font_folder_dir, folder, font_name)
            generateFontBinary(font_path,
                               lv_font_conv,
                               font_size_int,
                               output_file,
                               ranges_file,
                               cache_file,
                               config.logger)
    default_font_size = 20
    font_name = f"default.bin"
    output_file = os.path.join(font_folder_dir, font_name)
    generateFontBinary(font_path,
                        lv_font_conv,
                        default_font_size,
                        output_file,
                        ranges_file,
                        cache_file,
                        config.logger)

def generateFontBinary(font_path, lv_font_conv, font_size, output_path, ranges_file, cache_file, logger):
    ranges = parse_ranges_file(ranges_file)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    supported_ranges = check_supported_ranges(font_path, ranges, cache_file, lv_font_conv)
    if not supported_ranges:
        print("No supported ranges found for the font.")
        return
    print("Supported ranges:")
    for unicode_range, block_name in supported_ranges.items():
        print(f"{unicode_range} ({block_name})")
    
    command = [
       lv_font_conv,
        "--bpp", "4",
        "--size", f"{font_size}",
        "--font", font_path,
        "-r", ",".join(supported_ranges.keys()),
        "--format", "bin",
        "--no-compress",
        "--no-prefilter",
        "-o", output_path,
    ]
    print(f"Generating binary for size {font_size} -> {output_path}")
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error generating binary for size {font_size}: {e}")

def parse_ranges_file(file_path):
    """Parse ranges.txt and return a dictionary of ranges and block names."""
    ranges_dict = {}
    range_pattern = re.compile(r"range=U\+([0-9A-F]+)..U\+([0-9A-F]+)")
    name_pattern = re.compile(r"name=\[\[([^|\]]+)")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = content.split("{{Unicode blocks/row")
    for block in blocks:
        range_match = range_pattern.search(block)
        name_match = name_pattern.search(block)
        if range_match and name_match:
            start = int(range_match.group(1), 16)
            end = int(range_match.group(2), 16)
            block_name = name_match.group(1)
            ranges_dict[f"0x{start:04X}-0x{end:04X}"] = block_name

    return ranges_dict

def check_supported_ranges(font_path, ranges, cache_file, lv_font_conv_binary):
    """Check supported ranges for the font, using cache if available."""
    cache = load_cache(cache_file)
    font_hash = calculate_file_hash(font_path)

    # Check if the font's hash is already in the cache
    if font_hash in cache:
        print(f"Using cached ranges for font: {font_path}")
        return cache[font_hash]["supported_ranges"]

    # Test ranges with lv_font_conv
    print(f"Checking supported ranges for font: {font_path}")
    supported_ranges = {}
    for unicode_range, block_name in ranges.items():
        try:
            command = [
                lv_font_conv_binary,
                "--bpp", "4",
                "--size", "20",  # Arbitrary size for testing ranges
                "--font", font_path,
                "-r", unicode_range,
                "--format", "bin",
                "--no-compress",
                "--no-prefilter",
                "-o", os.devnull,  # Discard output
            ]
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            supported_ranges[unicode_range] = block_name
        except subprocess.CalledProcessError:
            print(f"Font does not support range: {unicode_range} ({block_name})")

    # Save the result to the cache
    cache[font_hash] = {
        "font_name": os.path.basename(font_path),
        "supported_ranges": supported_ranges,
    }
    save_cache(cache, cache_file)

    return supported_ranges

def load_cache(cache_file):
    """Load the font ranges cache from a JSON file."""
    if os.path.exists(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_cache(cache, cache_file):
    """Save the font ranges cache to a JSON file."""
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=4)

def calculate_file_hash(file_path):
    """Calculate the SHA256 hash of a file."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def percentage_colour(hex1, hex2, percentage):
    # Convert hex colours to RGB
    rgb1 = hex_to_rgb(hex1)
    rgb2 = hex_to_rgb(hex2)
    
    # Calculate the interpolated colour for each component
    interp_rgb = tuple(interpolate_colour_component(c1, c2, percentage) for c1, c2 in zip(rgb1, rgb2))
    
    # Convert interpolated RGB back to hex
    return rgb_to_hex(interp_rgb)

def hex_to_rgb(hex_colour,alpha = 1.0):
    # Convert hex to RGB
    rgb = tuple(int(hex_colour[i:i+2], 16) for i in (0, 2, 4))
    return (rgb[0], rgb[1], rgb[2], int(alpha * 255))

def rgb_to_hex(rgb_colour):
    # Convert RGB to hex
    return '{:02x}{:02x}{:02x}'.format(*rgb_colour)

def interpolate_colour_component(c1, c2, factor):
    # Interpolate a single colour component
    return int(c1 + (c2 - c1) * factor)

def round_to_nearest_odd(number):
    high_odd = (number // 2) * 2 + 1
    low_odd = high_odd - 2
    return int(high_odd) if abs(number - high_odd) < abs(number-low_odd) else int(low_odd)

def fillSchemeFiles(scheme_files_dir, template_scheme_file_path, config:Config):
    os.makedirs(scheme_files_dir, exist_ok=True)

    stringsToReplace = []

    # Read the template file and search for all instances of strings enclosed in {}
    with open(template_scheme_file_path, 'r') as file:
        content = file.read()
        # Find all occurrences of patterns like {some_string}
        matches = re.findall(r'\{[^}]+\}', content)
        # Convert matches to a set to keep only unique values, then back to a list
        stringsToReplace = list(set(matches))

    replacementStringMap = {}

    replacementStringMap["default"] = {}
    for n in stringsToReplace:
        replacementStringMap["default"][n] = None

    ############ Set up variables ############
    # Colours
    accent_hex = "ffffff"
    base_hex = config.background_hex[1:]
    blend_hex = percentage_colour(base_hex,accent_hex,0.5)
    muted_hex = percentage_colour(base_hex,accent_hex,0.25)
    battery_charging_hex = "2eb774"
    footer_background_hex = "000000"

    # General
    aprox_header_height_inc_gap = int((44/480)*config.screen_height)
    footer_height = int((55/480)*config.screen_height)
    content_item_count = 9 if config.screen_height == 480 else round_to_nearest_odd(9 * (config.screen_height / 480))
    content_item_height = floor((config.screen_height-aprox_header_height_inc_gap-footer_height)/content_item_count)
    content_height = content_item_count*content_item_height
    header_height_inc_gap = config.screen_height-content_height-footer_height

    header_icon_padding = 5
    clock_padding = 5
    
    # Set up default colours that should be the same everywhere
    replacementStringMap["default"]["{accent_hex}"] = accent_hex
    replacementStringMap["default"]["{base_hex}"] = base_hex
    replacementStringMap["default"]["{blend_hex}"] = blend_hex
    replacementStringMap["default"]["{muted_hex}"] = muted_hex
    replacementStringMap["default"]["{battery_charging_hex}"] = battery_charging_hex

    # Grid Settings
    replacementStringMap["default"]["{grid_navigation_type}"] = 4
    replacementStringMap["default"]["{grid_background}"] = base_hex
    replacementStringMap["default"]["{grid_background_alpha}"] = 0
    replacementStringMap["default"]["{grid_location_x}"] = 0
    replacementStringMap["default"]["{grid_location_y}"] = 0
    replacementStringMap["default"]["{grid_column_count}"] = 0
    replacementStringMap["default"]["{grid_row_count}"] = 0
    replacementStringMap["default"]["{grid_row_height}"] = 0
    replacementStringMap["default"]["{grid_column_width}"] = 0
    replacementStringMap["default"]["{grid_cell_width}"] = 200
    replacementStringMap["default"]["{grid_cell_height}"] = 200
    replacementStringMap["default"]["{grid_cell_radius}"] = 10
    replacementStringMap["default"]["{grid_cell_border_width}"] = 0
    replacementStringMap["default"]["{grid_cell_image_padding_top}"] = 0
    replacementStringMap["default"]["{grid_cell_text_padding_bottom}"] = 0
    replacementStringMap["default"]["{grid_cell_text_padding_side}"] = 0
    replacementStringMap["default"]["{grid_cell_text_line_spacing}"] = 0
    replacementStringMap["default"]["{grid_cell_default_background}"] = base_hex
    replacementStringMap["default"]["{grid_cell_default_background_alpha}"] = 0
    replacementStringMap["default"]["{grid_cell_default_border}"] = base_hex
    replacementStringMap["default"]["{grid_cell_default_border_alpha}"] = 0
    replacementStringMap["default"]["{grid_cell_default_image_alpha}"] = 255
    replacementStringMap["default"]["{grid_cell_default_image_recolour}"] = accent_hex
    replacementStringMap["default"]["{grid_cell_default_image_recolour_alpha}"] = 255
    replacementStringMap["default"]["{grid_cell_default_text}"] = blend_hex
    replacementStringMap["default"]["{grid_cell_default_text_alpha}"] = 0
    replacementStringMap["default"]["{grid_cell_focus_background}"] = blend_hex
    replacementStringMap["default"]["{grid_cell_focus_background_alpha}"] = int(255*0.133)
    replacementStringMap["default"]["{grid_cell_focus_border}"] = blend_hex
    replacementStringMap["default"]["{grid_cell_focus_border_alpha}"] = 0
    replacementStringMap["default"]["{grid_cell_focus_image_alpha}"] = 255
    replacementStringMap["default"]["{grid_cell_focus_image_recolour}"] = accent_hex
    replacementStringMap["default"]["{grid_cell_focus_image_recolour_alpha}"] = 255
    replacementStringMap["default"]["{grid_cell_focus_text}"] = accent_hex
    replacementStringMap["default"]["{grid_cell_focus_text_alpha}"] = 0

    # Footer settings
    replacementStringMap["default"]["{footer_height}"] = footer_height
    replacementStringMap["default"]["{footer_alpha}"] = 255
    replacementStringMap["default"]["{footer_background}"] = footer_background_hex

    # Header settings
    replacementStringMap["default"]["{header_height}"] = header_height_inc_gap-2
    replacementStringMap["default"]["{header_text_alpha}"] = 0
    replacementStringMap["default"]["{status_padding_left}"] = header_icon_padding
    replacementStringMap["default"]["{status_padding_right}"] = header_icon_padding
    replacementStringMap["default"]["{date_padding_left}"] = clock_padding
    replacementStringMap["default"]["{date_padding_right}"] = clock_padding

    # Content settings
    content_alignment_map = {"Left": 0, "Centre": 1, "Right": 2}
    replacementStringMap["default"]["{content_alignment}"] = content_alignment_map["Left"]
    replacementStringMap["default"]["{content_height}"] = content_height
    replacementStringMap["default"]["{content_item_height}"] = content_item_height-2
    replacementStringMap["default"]["{content_width}"] = config.screen_width
    replacementStringMap["default"]["{content_item_count}"] = content_item_count
    replacementStringMap["default"]["{content_padding_top}"] = (header_height_inc_gap)-header_height_inc_gap
    replacementStringMap["default"]["{content_padding_left}"] = 0
    replacementStringMap["default"]["{content_size_to_content}"] = 0
    replacementStringMap["default"]["{navigation_type}"] = 0

    # Random Settings
    replacementStringMap["default"]["{boot_text_y_pos}"] = int(int(config.screen_height)*(165/480))
    replacementStringMap["default"]["{default_radius}"] = 5

    #Bar settings
    replacementStringMap["default"]["{bar_height}"] = 42
    replacementStringMap["default"]["{bar_progress_width}"] = int(config.screen_width) - 90
    replacementStringMap["default"]["{bar_y_pos}"] = int(config.screen_height) - (30+footer_height)
    replacementStringMap["default"]["{bar_width}"] = int(config.screen_width) - 25
    replacementStringMap["default"]["{bar_progress_height}"] = 16

    # Text settings
    replacementStringMap["default"]["{selected_font_hex}"] = accent_hex
    replacementStringMap["default"]["{deselected_font_hex}"] = blend_hex
    replacementStringMap["default"]["{list_text_alpha}"] = 255
    replacementStringMap["default"]["{font_list_pad_left}"] = 5
    replacementStringMap["default"]["{font_list_pad_right}"] = 5

    # Glyph Settings
    replacementStringMap["default"]["{list_glyph_alpha}"] = 0
    replacementStringMap["default"]["{glyph_padding_left}"] = 0

    # Counter Settings
    counter_alignment_map = {"Left": 0, "Centre": 1, "Right": 2}
    replacementStringMap["default"]["{counter_alignment}"] = counter_alignment_map["Right"]
    replacementStringMap["default"]["{counter_padding_top}"] = header_height_inc_gap
    
    missingValues = []

    for n in replacementStringMap["default"].keys():
        if replacementStringMap["default"][n] == None:
            missingValues.append(n)
    if missingValues:
        missingValuesString = ""
        for n in missingValues:
            missingValuesString += n+"\n"
        raise ValueError(f"Replacement string(s) \n{missingValuesString} not set")
    
    ## Overrides:
    replacementStringMap["muxlaunch"] = {}
    replacementStringMap["muxlaunch"]["{list_glyph_alpha}"] = 0
    replacementStringMap["muxlaunch"]["{content_height}"] = config.screen_height
    replacementStringMap["muxlaunch"]["{content_item_height}"] = config.screen_height-2
    replacementStringMap["muxlaunch"]["{content_item_count}"] = 1
    replacementStringMap["muxlaunch"]["{content_padding_top}"] = 0-header_height_inc_gap
    replacementStringMap["muxlaunch"]["{navigation_type}"] = 1
    replacementStringMap["muxlaunch"]["{content_size_to_content}"] = 1
    replacementStringMap["muxlaunch"]["{content_alignment}"] = content_alignment_map["Centre"]

    replacementStringMap["muxplore"] = {}
    replacementStringMap["muxplore"]["{grid_navigation_type}"] = 2
    replacementStringMap["muxplore"]["{grid_location_y}"] = header_height_inc_gap
    replacementStringMap["muxplore"]["{grid_column_count}"] = 1
    replacementStringMap["muxplore"]["{grid_row_count}"] = content_item_count
    replacementStringMap["muxplore"]["{grid_row_height}"] = content_item_height
    replacementStringMap["muxplore"]["{grid_column_width}"] = config.screen_width
    replacementStringMap["muxplore"]["{grid_cell_width}"] = config.screen_width
    replacementStringMap["muxplore"]["{grid_cell_height}"] = content_item_height
    replacementStringMap["muxplore"]["{grid_cell_radius}"] = 0
    replacementStringMap["muxplore"]["{grid_cell_focus_text_alpha}"] = 255
    replacementStringMap["muxplore"]["{grid_cell_default_text_alpha}"] = 255
    replacementStringMap["muxplore"]["{grid_cell_focus_image_alpha}"] = 0
    replacementStringMap["muxplore"]["{grid_cell_default_image_alpha}"] = 0
    replacementStringMap["muxplore"]["{grid_cell_focus_background_alpha}"] = 0


    replacementStringMap["muxgov"] = {}

    replacementStringMap["muassign"] = {}

    replacementStringMap["muxsearch"] = {}
        
    for fileName in replacementStringMap.keys():
        shutil.copy2(template_scheme_file_path,os.path.join(scheme_files_dir,f"{fileName}.txt"))
        for stringToBeReplaced in replacementStringMap["default"].keys():
            replacement = replacementStringMap[fileName].get(stringToBeReplaced,replacementStringMap["default"][stringToBeReplaced])
            replace_in_file(os.path.join(scheme_files_dir,f"{fileName}.txt"), stringToBeReplaced, str(replacement))

def generateArtBookNextImage(current_index,
                             all_es_item_names,
                             rendered_image_width,
                             rendered_image_height,
                             rendered_image_multiplier,
                             gap_between_panels,
                             real_panel_width,
                             panels_dir,
                             panel_width,
                             panel_height,
                             deselected_brightness):
    image = Image.new("RGBA", (rendered_image_width, rendered_image_height), (0,0,0,0))

    change_in_x = int(real_panel_width+(gap_between_panels*(rendered_image_multiplier)))

    panels_per_screen = ceil(rendered_image_width/change_in_x)+1

    current_es_item_name = all_es_item_names[current_index]
    panel_image = Image.open(os.path.join(panels_dir, f"{current_es_item_name}")).resize((panel_width, panel_height), Image.LANCZOS)

    image_middle_x = int((rendered_image_width - panel_image.width) / 2)
    image.alpha_composite(panel_image, (image_middle_x, 0))
    panels_left = panels_per_screen-1
    panels_to_the_left = ceil(panels_left/2)
    panels_to_the_right = ceil(panels_left/2)
    index=1
    while index <= panels_to_the_left:
        # draw the correct panel image in the middle of the screen
        working_item_index = (current_index+index)%len(all_es_item_names)

        working_es_item_name = all_es_item_names[working_item_index]
        working_panel_image = Image.open(os.path.join(panels_dir, f"{working_es_item_name}")).resize((panel_width, panel_height), Image.LANCZOS)
        enhancer = ImageEnhance.Brightness(working_panel_image)
        # to reduce brightness by 50%, use factor 0.5
        working_panel_image = enhancer.enhance(deselected_brightness)
        image.alpha_composite(working_panel_image, (image_middle_x+index*change_in_x, 0))
        index += 1
    index=1
    while index <= panels_to_the_right:
        # draw the correct panel image in the middle of the screen
        working_item_index = (current_index-index)%len(all_es_item_names)

        working_es_item_name = all_es_item_names[working_item_index]
        working_panel_image = Image.open(os.path.join(panels_dir, f"{working_es_item_name}")).resize((panel_width, panel_height), Image.LANCZOS)

        enhancer = ImageEnhance.Brightness(working_panel_image)
        # to reduce brightness by 50%, use factor 0.5
        working_panel_image = enhancer.enhance(deselected_brightness)
        image.alpha_composite(working_panel_image, (image_middle_x-index*change_in_x, 0))
        index += 1
    return(image)


def generatePilImageBootScreen(base_hex, accent_hex, display_text, screen_width, screen_height, font_path, icon_path=None):
    base_rgb = hex_to_rgb(base_hex)
    image = Image.new("RGBA", (screen_width, screen_height), base_rgb)
    draw = ImageDraw.Draw(image)
    
    screen_x_middle, screen_y_middle = int(screen_width/2), int(screen_height/2)

    from_middle_padding = 0
    
    if icon_path != None:
        if os.path.exists(icon_path):
            from_middle_padding = 50
            logo_image = Image.open(icon_path).convert("RGBA")
            logo_alpha_channel = logo_image.split()[3]
            logoColoured = ImageOps.colorize(logo_alpha_channel, black=accent_hex, white=accent_hex)
            logoColoured = logoColoured.resize((int((logoColoured.size[0]/5)),int((logoColoured.size[1]/5))), Image.LANCZOS)
            
            logo_y_location = int(screen_y_middle-logoColoured.size[1]/2-from_middle_padding)
            logo_x_location = int(screen_x_middle-logoColoured.size[0]/2)

            image.paste(logoColoured,(logo_x_location,logo_y_location),logoColoured)
            
    font_size = int(57.6)
    font = ImageFont.truetype(font_path, font_size)

    textBbox = font.getbbox(display_text)

    textWidth = int(textBbox[2] - textBbox[0])
    textHeight = int(textBbox[3]-textBbox[1])
    y_location = int(screen_y_middle-textHeight/2-textBbox[1]+from_middle_padding)
    x_location = int(screen_x_middle - textWidth/2)

    draw.text((x_location,y_location), display_text, font=font, fill=f"#{accent_hex}")

    
    return (image)

def generatePilImageDefaultScreen(base_hex, screen_width, screen_height):
    base_rgb = hex_to_rgb(base_hex)
    image = Image.new("RGBA", (screen_width, screen_height), base_rgb)
    return (image)

def replace_in_file(file_path, search_string, replace_string):
    # Read the content of the file in binary mode
    with open(file_path, 'rb') as file:
        file_contents = file.read()
    
    # Replace the occurrences of the search_string with replace_string in binary data
    search_bytes = search_string.encode()
    replace_bytes = replace_string.encode()
    new_contents = file_contents.replace(search_bytes, replace_bytes)
    
    # Write the new content back to the file in binary mode
    with open(file_path, 'wb') as file:
        file.write(new_contents)


def get_es_system_name(folder_name:str, muOS_system_name:str, config:Config):
    # Special case for Neo Geo Pocket
    if check_for_special_case(folder_name, config.special_cases) != None:
        muOS_system_name = check_for_special_case(folder_name, config.special_cases)
    if muOS_system_name in config.system_map.keys():
        return config.system_map[muOS_system_name]
    else:
        return "_default.png"

def check_for_special_case(folder_name, special_cases):
    """
    Checks if a string matches any special case pattern and returns the associated output.
    
    Args:
        folder_name (str): The input string to check.
        special_cases (dict): A dictionary where keys are regex patterns and values are output strings.
    
    Returns:
        str or None: The associated output string if a match is found; otherwise, None.
    """
    for pattern in special_cases.keys():
        if re.search(pattern, folder_name, re.IGNORECASE):  # Case insensitive search
            return special_cases[pattern]
    return None


def generateLogoImage(folder_name:str,
                      muOS_system_name:str,
                      image_width:int,
                      image_height:int,
                      logger,
                      logos_dir,
                      max_icon_height,
                      max_icon_width,
                      font_path,
                      shadow_strength):
    image = Image.new("RGBA", (image_width, image_height), (0, 0, 0, 0))
    ## draw the logo in the middle of the screen
    logger.info(f"Generating logo for {folder_name}")
    if muOS_system_name != "default":
        logo_image = Image.open(os.path.join(logos_dir, f"{muOS_system_name}.png")).convert("RGBA")
        logo_image_multiplier = min(max_icon_height/logo_image.height, max_icon_width/logo_image.width)
        logo_image = logo_image.resize((int(logo_image.width*logo_image_multiplier), int(logo_image.height*logo_image_multiplier)), Image.LANCZOS)
    else:
        # use config font_path to draw a text logo
        font_size_w = 150*(image_width/1440)
        font_size_h = 150*(image_height/810)
        font_size = min(font_size_w, font_size_h)

        font = ImageFont.truetype(font_path, font_size)

        folder_name_bbox = font.getbbox(folder_name)
        folder_name_width = folder_name_bbox[2]-folder_name_bbox[0]
        folder_name_height = folder_name_bbox[3]-folder_name_bbox[1]

        text_to_draw = []
        max_chars = floor(len(folder_name)*((max_icon_width)/(folder_name_width)))
        if len(folder_name) > max_chars:
            words_in_folder_name = folder_name.split(" ")
            set_of_words = []
            index=0
            while True:
                if index >= len(words_in_folder_name):
                    break
                set_of_words.append(words_in_folder_name[index])
                sub_index = index+1
                while True:
                    if sub_index >= len(words_in_folder_name):
                        break
                    if len(set_of_words[index]+" "+words_in_folder_name[sub_index]) > max_chars:
                        break
                    set_of_words[index] += " "+words_in_folder_name[sub_index]
                    words_in_folder_name.remove(words_in_folder_name[sub_index])
                index += 1
            for word in set_of_words:
                if len(word) > max_chars:
                    for i in range(0, len(word), max_chars):
                        if i+max_chars > len(word):
                            text_to_draw.append(word[i:])
                            break
                        else:
                            text_to_draw.append(word[i:i+max_chars])
                else:
                    text_to_draw.append(word)
        else:
            text_to_draw = [folder_name]
        text_widths = []
        ascent, descent = font.getmetrics()
        text_height = ascent + descent
        for text in text_to_draw:
            text_widths.append(font.getbbox(text)[2]-font.getbbox(text)[0])
        space_between_text = int(-30*(image_width/1440))
        total_text_height = text_height*len(text_to_draw)+ (len(text_to_draw)-1)*space_between_text

        logo_image = Image.new("RGBA", (max(text_widths), total_text_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(logo_image)

        for n in range(len(text_to_draw)):
            if n == 0:
                text_y = 0
            else:
                text_y = text_y + text_height + space_between_text
            text_x = (max(text_widths)-text_widths[n])/2
            draw.text((text_x,text_y), text_to_draw[n], font=font, fill=(255,255,255,255))
        
    logo_image_middle_x = int((image_width - logo_image.width) / 2)
    logo_image_middle_y = int((image_height - logo_image.height) / 2)

    # Prepare shadow
    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))  # Transparent canvas
    alpha_channel = logo_image.split()[3]  # Extract the alpha channel of the logo
    shadow_logo = ImageOps.colorize(alpha_channel, black="black", white="black")  # Create a black shadow
    shadow_logo = shadow_logo.convert("RGBA")  # Ensure RGBA mode
    shadow.paste(shadow_logo, (logo_image_middle_x, logo_image_middle_y), alpha_channel)  # Use alpha_channel as mask for transparency
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=20))
    for n in range(shadow_strength):
        image.alpha_composite(shadow, (0,0))

    # Composite logo
    image.alpha_composite(logo_image, (logo_image_middle_x, logo_image_middle_y))

    return image


def get_folders(roms_dir):
    """
    Get all folders in the ROMs directory, retaining the ordering of the `ls` command.

    :param roms_dir: Path to the ROMs directory.
    :return: List of folders.
    """
    folders = []
    try:
        # Use the `ls` command to list the directory contents in order
        output = subprocess.check_output(['ls', '-1', roms_dir], text=True).splitlines()
        for folder in output:
            folder_path = os.path.join(roms_dir, folder)
            if os.path.isdir(folder_path) and not folder.startswith(('.', '_')):
                folders.append(folder)
    except subprocess.CalledProcessError as e:
        print(f"Error while listing directory: {e}")
    return folders

def get_folder_core_associations(folders, core_info_dir):
    """
    Get folder core associations from the core info directory.

    :param roms_dir: Path to the ROMs directory.
    :param core_info_dir: Path to the core info directory.
    :return: Dictionary of folder core associations.
    """
    folder_core_associations = {}
    for folder in folders:
        folder = folder.lower()
        core_info_file = os.path.join(core_info_dir, folder, "core.cfg")
        if os.path.isfile(core_info_file):
            with open(core_info_file, "r") as f:
                lines = f.readlines()
                # Check if the file has at least two lines
                if len(lines) >= 2:
                    core_info = lines[1].strip()  # Use strip() to remove any trailing newlines or spaces
                else:
                    core_info = "default"  # Handle the case where there are less than 2 lines
                folder_core_associations[folder] = core_info
        else:
            folder_core_associations[folder] = "default"
    return folder_core_associations

def verify_json_mapping(json_file_path, valid_muos_system_names_path, panels_dir, logger):
    """
    Verifies that the JSON file has a mapping for each system image panel.

    :param json_file_path: Path to the JSON file.
    :param valid_muos_system_names_path: Path to the file containing valid MUOS system names.
    :param panels_dir: Path to the system image panels directory.
    :return: True if the JSON file has a mapping for each system image panel, False otherwise.
    """
    with open(json_file_path, "r") as f:
        json_data = json.load(f)

    # Get valid MUOS system names
    with open(valid_muos_system_names_path, "r") as f:
        valid_muos_system_names = f.read().splitlines()

    # Get system image panels
    panels = os.listdir(panels_dir)

    # Check if the JSON file has a mapping for each system image panel
    for valid_muos_system_name in valid_muos_system_names:
        if valid_muos_system_name not in json_data.keys():
            logger.info(f"[ERROR] No mapping found for system name: {valid_muos_system_name}")
            return False
        else:
            logger.info(f"[OK] JSON file has a mapping for system name: {valid_muos_system_name}")
    for json_muos_system_name in json_data.keys():
        if json_muos_system_name not in valid_muos_system_names:
            logger.error(f"[ERROR] Invalid system name '{json_muos_system_name}' in JSON file")
            return False
        else:
            logger.info(f"[OK] JSON file has a valid system name: {json_muos_system_name}")
    for es_system_names in json_data.values():
        if es_system_names not in panels:
            logger.error(f"[ERROR] No panel found for system name: {es_system_names}")
            return False
        else:
            logger.info(f"[OK] JSON file has a panel for system name: {es_system_names}")

    logger.info(f"[OK] JSON file has a mapping for each system image panel.")
    return True

def validate_directory(path, description, logger):
    """
    Validates whether the provided path is a valid directory.

    :param path: Path to validate.
    :param description: Description of the directory (for error messages).
    :return: True if valid, False otherwise.
    """
    if os.path.isdir(path):
        logger.info(f"[OK] {description}: '{path}' is a valid directory.")
        return True
    else:
        logger.error(f"[ERROR] {description}: '{path}' is not a valid directory.")
        return False

def validate_file(path, description, logger):
    """
    Validates whether the provided path is a valid file.

    :param path: Path to validate.
    :param description: Description of the file (for error messages).
    :return: True if valid, False otherwise.
    """
    if os.path.isfile(path):
        logger.info(f"[OK] {description}: '{path}' is a valid file.")
        return True
    else:
        logger.error(f"[ERROR] {description}: '{path}' is not a valid file.")
        return False
    
def check_lv_font_conv(lv_font_conv_path):
    """
    Checks if the lv_font_conv tool is available.
    
    :param lv_font_conv_path: Path to the lv_font_conv binary or "lv_font_conv" if it's in PATH.
    :return: True if lv_font_conv is found and executable, False otherwise.
    """
    try:
        # Check if the command is callable
        result = subprocess.run([lv_font_conv_path, "--help"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # If the tool is callable and returns help or no error
        return result.returncode == 0
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        return False

def main():
    # Define and parse arguments
    parser = argparse.ArgumentParser(
        description="Validate directories and configure optional settings."
    )

    # Mode argument
    parser.add_argument(
        "--mode",
        choices=["box_art", "theme", "both"],
        required=True,
        help="Choose what to generate: 'box_art', 'theme', or 'both'."
    )

    # Required arguments
    parser.add_argument("--screen_height", type=int, required=True, help="Screen height in pixels")
    parser.add_argument("--screen_width", type=int, required=True, help="Screen width in pixels")
    parser.add_argument("--panels_dir", required=True, help="Path to the system image panels directory")
    parser.add_argument("--working_dir", required=True, help="Path to the folder where your the script will use to store temporary files and folders")

    parser.add_argument(
        "--roms_dir",
        help="Path to the ROMs directory (required if mode includes 'box_art')"
    )
    parser.add_argument(
        "--box_art_dir",
        help="Path to the box art directory (required if mode includes 'box_art')"
    )
    parser.add_argument(
        "--logos_dir",
        help="Path to the system image logos directory (required if mode includes 'box_art')"
    )
    parser.add_argument(
        "--core_info_dir",
        help="Path to the folder where folder core associations are stored (required if mode includes 'box_art')"
    )
    parser.add_argument(
        "--system_map_path",
        help="Path to the file where muOS -> ES system name mapping is stored (required if mode includes 'box_art')"
    )
    parser.add_argument(
        "--valid_muos_system_names_path",
        help="Path to the file containing valid muOS system names (required if mode includes 'box_art')"
    )
    parser.add_argument(
        "--font_path",
        help="Path to the font file (required if mode includes 'box_art')"
    )

    # Conditionally required argument
    parser.add_argument(
        "--theme_shell_dir",
        help="Path to the theme shell directory (required if mode includes 'theme')."
    )

    parser.add_argument(
        "--theme_output_dir",
        help="Path to the output directory for themes (required if mode includes 'theme')."
    )

    parser.add_argument(
        "--theme_name",
        help="Path to the output directory for themes (required if mode includes 'theme')."
    )

    parser.add_argument(
        "--template_scheme_path",
        help="Path of the template scheme file for themes (required if mode includes 'theme')."
    )

    parser.add_argument(
        "--lv_font_conv_path",
        help="Path of where lv_font_conv program is (required if mode includes 'theme')."
    )

    parser.add_argument(
        "--font_ranges_path",
        help="Path to a file containing valid font ascii ranges (required if mode includes 'theme')."
    )

    parser.add_argument(
        "--font_cache_path",
        help="Path to where font valid ranges cache is (required if mode includes 'theme')."
    )

    # Optional arguments with defaults
    parser.add_argument(
        "--background_hex", default="#000000",
        help="Background colour in hex format (default: #000000)"
    )
    parser.add_argument(
        "--gap_between_panels", type=int, default=7,
        help="Gap between panels in pixels (default: 7)"
    )
    parser.add_argument(
        "--icon_height_percent", type=float, default=0.5,
        help="Max icon height as a percentage of screen height (default is 50%%: 0.5 )"
    )
    parser.add_argument(
        "--icon_width_percent", type=float, default=0.7,
        help="Max icon width as a percentage of screen width (default is 70%%: 0.7)"
    )
    parser.add_argument(
        "--deselected_brightness", type=float, default=0.4,
        help="How close to full brightness are the deselected folders (default is 40%%: 0.4)"
    )
    parser.add_argument(
        "--shadow_strength", type=int, default=1,
        help="How strong do you want the drop shadow to be? (default is 1: int[0-5])"
    )
    parser.add_argument(
        "--gradient_intensity", type=int, default=235,
        help="The intensity of the gradient overlaid (default is 235: 0-255)"
    )

    args = parser.parse_args()

    if args.mode in ["theme", "both"] and not args.theme_output_dir:
        parser.error("--theme_output_dir is required when mode is 'theme' or 'both'.")
    if args.mode in ["theme", "both"] and not args.theme_shell_dir:
        parser.error("--theme_shell_dir is required when mode is 'theme' or 'both'.")
    if args.mode in ["theme", "both"] and not args.theme_name:
        parser.error("--theme_name is required when mode is 'theme' or 'both'.")
    if args.mode in ["theme", "both"] and not args.template_scheme_path:
        parser.error("--template_scheme_path is required when mode is 'theme' or 'both'.")
    if args.mode in ["theme", "both"] and not args.lv_font_conv_path:
        parser.error("--lv_font_conv_path is required when mode is 'theme' or 'both'.")
    if args.mode in ["theme", "both"] and not args.font_ranges_path:
        parser.error("--font_ranges_path is required when mode is 'theme' or 'both'.")
    if args.mode in ["theme", "both"] and not args.font_cache_path:
        parser.error("--font_cache_path is required when mode is 'theme' or 'both'.")

    # Validate conditional argument
    if args.mode in ["box_art", "both"] and not args.theme_output_dir:
        parser.error("--roms_dir is required when mode is 'box_art' or 'both'.")
    if args.mode in ["box_art", "both"] and not args.box_art_dir:
        parser.error("--box_art_dir is required when mode is 'box_art' or 'both'.")
    if args.mode in ["box_art", "both"] and not args.logos_dir:
        parser.error("--logos_dir is required when mode is 'box_art' or 'both'.")
    if args.mode in ["box_art", "both"] and not args.core_info_dir:
        parser.error("--core_info_dir is required when mode is 'box_art' or 'both'.")
    if args.mode in ["box_art", "both"] and not args.system_map_path:
        parser.error("--system_map_path is required when mode is 'box_art' or 'both'.")
    if args.mode in ["box_art", "both"] and not args.valid_muos_system_names_path:
        parser.error("--valid_muos_system_names_path is required when mode is 'box_art' or 'both'.")
    if args.mode in ["box_art", "both"] and not args.font_path:
        parser.error("--font_path is required when mode is 'box_art' or 'both'.")
    

    logger = setup_logger(args.working_dir)

    logger.info("=" * 50)  # Divider line
    logger.info("Checking if given directories are valid")
    logger.info("=" * 50)

    # Validate directories
    required_validations = [
        validate_directory(args.panels_dir, "System Image Panels Directory", logger),
        validate_directory(args.working_dir, "Log File Output Directory", logger)
    ]

    box_art_validations = [
        validate_directory(args.roms_dir, "ROMs Directory", logger),
        validate_directory(args.box_art_dir, "Box Art Directory", logger),
        validate_directory(args.logos_dir, "System Image Logos Directory", logger),
        validate_directory(args.core_info_dir, "Folder Core Association Directory", logger),
        validate_file(args.system_map_path, "System Map File", logger),
        validate_file(args.valid_muos_system_names_path, "Valid muOS System Names File", logger),
        validate_file(args.font_path, "Font File", logger),
    ]

    theme_validations = [
        validate_directory(args.theme_output_dir, "Themes Directory", logger),
        validate_directory(args.theme_shell_dir, "Theme Shell Directory", logger),
        validate_file(args.template_scheme_path, "Template Scheme File", logger),
        validate_file(args.font_ranges_path, "Font Ranges File", logger),
        validate_file(args.font_cache_path, "Font Cache File", logger)
    ]

    if not all(required_validations):
        logger.error("One or more required directories are invalid. Please check the paths and try again.")
        sys.exit(1)
    
    if not all(box_art_validations) and args.mode in ["box_art", "both"]:
        logger.error("One or more rquired directories for box_art are invalid. Please check the paths and try again.")
        sys.exit(1)
    
    if not all(theme_validations) and args.mode in ["theme", "both"]:
        logger.error("One or more rquired directories for theme generation are invalid. Please check the paths and try again.")
        sys.exit(1)
    if not check_lv_font_conv(args.lv_font_conv_path):
        logger.error("lv_font_conv is not installed or the path is incorrect.")
        sys.exit(1)

    logger.info("All directories are valid. Proceeding with the next steps...")
    config = Config(args, logger)
    config.log_config()

    if args.mode in ["box_art", "both"]:
        logger.info("Generating folder box art...")
        for folder in config.folders:
            generateFolderImage(folder, config).save(os.path.join(config.box_art_dir, f"{folder}.png"))
            logger.info(f"Successfully generated image for folder: {folder}")

    if args.mode in ["theme", "both"]:
        temp_theme_folder = os.path.join(args.working_dir, ".temp_theme_folder")
        if os.path.exists(temp_theme_folder):
            shutil.rmtree(temp_theme_folder)
        shutil.copytree(args.theme_shell_dir, temp_theme_folder)
        
        fillTempThemeFolder(temp_theme_folder, args.template_scheme_path, args.lv_font_conv_path, args.font_ranges_path, args.font_cache_path, config)
        
        theme_output_dir = args.theme_output_dir
        os.makedirs(theme_output_dir, exist_ok=True)

        if os.path.exists(os.path.join(theme_output_dir, f"{args.theme_name}.zip")):
            os.remove(os.path.join(theme_output_dir, f"{args.theme_name}.zip"))

        shutil.make_archive(os.path.join(theme_output_dir, args.theme_name), 'zip', temp_theme_folder)
        shutil.rmtree(temp_theme_folder)
    
if __name__ == "__main__":
    main()
