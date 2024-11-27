import argparse
import os
import subprocess
import sys
import json
import logging
import re
import shutil
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
        self.max_icon_height = (args.screen_height * args.icon_height_percent)
        self.max_icon_width = (args.screen_width * args.icon_width_percent) 
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
        self.logger.info(f"  Background color: {self.background_hex}")
        self.logger.info(f"  Gap between panels: {self.gap_between_panels}px")
        self.logger.info(f"  Icon height max percent of screen height: {self.icon_height_percent*100}%")
        self.logger.info(f"  Icon width max percent of screen width: {self.icon_width_percent*100}%")
        self.logger.info(f"  Calculated max icon height: {self.max_icon_height}px")
        self.logger.info(f"  Calculated max icon width: {self.max_icon_width}px")
    def log_associations(self):
        for folder in self.folder_console_associations.keys():
            self.logger.info(f"  {folder}: {self.folder_console_associations[folder]}")
    def get_gradient_overlay_image(self, width, height, start_color, end_color, gradient_height_percent):
        if self.gradient_overlay_image is None:
            self.gradient_overlay_image = generateGradientImage(width, height, start_color, end_color, gradient_height_percent, self)
        return self.gradient_overlay_image
    def update_folders(self, folders):
        self.folders = folders
        self.folder_console_associations = get_folder_core_associations(self.folders, self.core_info_dir)

def generateGradientImage(width, height, start_color, end_color, gradient_height_percent,config:Config):
    """
    Generate a smooth vertical gradient image using PIL.
    
    Parameters:
        width (int): The width of the image.
        height (int): The height of the image.
        start_color (tuple): RGBA tuple for the color at the top of the gradient.
        end_color (tuple): RGBA tuple for the color at the bottom of the gradient.
        gradient_height_percent (float): The percentage of the image height that the gradient covers (0.0 to 1.0).
    
    Returns:
        Image: A PIL Image object containing the gradient.
    """
    config.logger.info(f"Generating Gradient Image")
    # Create a new image with an RGBA mode
    gradient = Image.new("RGBA", (width, height))
    gradient_height = int(height * gradient_height_percent)

    # Calculate the color difference for the gradient
    delta_r = end_color[0] - start_color[0]
    delta_g = end_color[1] - start_color[1]
    delta_b = end_color[2] - start_color[2]
    delta_a = end_color[3] - start_color[3]

    for y in range(height):
        if y < gradient_height:
            # Calculate the interpolation factor
            t = y / gradient_height
            # Interpolate the color
            r = int(start_color[0] + t * delta_r)
            g = int(start_color[1] + t * delta_g)
            b = int(start_color[2] + t * delta_b)
            a = int(start_color[3] + t * delta_a)
        else:
            # Use the end color for the rest of the image
            r, g, b, a = end_color

        # Draw a horizontal line with the calculated color
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
        logo_image = generateLogoImage(folder_name, special_muOS_system_name, rendered_image_width, rendered_image_height, rendered_image_multiplier, config)
    else:
        logo_image = generateLogoImage(folder_name, muOS_system_name, rendered_image_width, rendered_image_height, rendered_image_multiplier, config)
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

def fillTempThemeFolder(theme_folder_dir, config:Config):
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
            current_theme_image.resize(preview_size, Image.LANCZOS)
            current_theme_image.save(os.path.join(theme_folder_dir, "preview.png"))
        config.logger.info(f"Successfully generated theme image for system: {item}")

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


def generateLogoImage(folder_name:str, muOS_system_name:str, rendered_image_width:int, rendered_image_height:int, rendered_image_multiplier:float, config:Config):
    image = Image.new("RGBA", (rendered_image_width, rendered_image_height), (0, 0, 0, 0))
    ## draw the logo in the middle of the screen
    config.logger.info(f"Generating logo for {folder_name}")
    if muOS_system_name != "default":
        logo_image = Image.open(os.path.join(config.logos_dir, f"{muOS_system_name}.png")).convert("RGBA")
        logo_image_multiplier = min(config.max_icon_height/logo_image.height, config.max_icon_width/logo_image.width)*rendered_image_multiplier
        logo_image = logo_image.resize((int(logo_image.width*logo_image_multiplier), int(logo_image.height*logo_image_multiplier)), Image.LANCZOS)
    else:
        # use config config.font_path to draw a text logo
        font_size_w = 150*(rendered_image_width/1440)
        font_size_h = 150*(rendered_image_height/810)
        font_size = min(font_size_w, font_size_h)

        font = ImageFont.truetype(config.font_path, font_size)

        folder_name_bbox = font.getbbox(folder_name)
        folder_name_width = folder_name_bbox[2]-folder_name_bbox[0]
        folder_name_height = folder_name_bbox[3]-folder_name_bbox[1]

        text_to_draw = []
        max_chars = floor(len(folder_name)*((config.max_icon_width*rendered_image_multiplier)/(folder_name_width)))
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
        space_between_text = int(-30*(rendered_image_width/1440))
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
        
    logo_image_middle_x = int((rendered_image_width - logo_image.width) / 2)
    logo_image_middle_y = int((rendered_image_height - logo_image.height) / 2)

    # Prepare shadow
    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))  # Transparent canvas
    alpha_channel = logo_image.split()[3]  # Extract the alpha channel of the logo
    shadow_logo = ImageOps.colorize(alpha_channel, black="black", white="black")  # Create a black shadow
    shadow_logo = shadow_logo.convert("RGBA")  # Ensure RGBA mode
    shadow.paste(shadow_logo, (logo_image_middle_x, logo_image_middle_y), alpha_channel)  # Use alpha_channel as mask for transparency
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=20))
    for n in range(config.shadow_strength):
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

    # Optional arguments with defaults
    parser.add_argument(
        "--background_hex", default="#000000",
        help="Background color in hex format (default: #000000)"
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
        validate_directory(args.theme_shell_dir, "Theme Shell Directory", logger)
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
        
        fillTempThemeFolder(temp_theme_folder, config)
        
        theme_output_dir = args.theme_output_dir
        os.makedirs(theme_output_dir, exist_ok=True)

        shutil.make_archive(os.path.join(theme_output_dir, args.theme_name), 'zip', temp_theme_folder)
        shutil.rmtree(temp_theme_folder)
    
if __name__ == "__main__":
    main()
