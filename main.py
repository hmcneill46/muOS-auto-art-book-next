import argparse
import os
import sys
import json
import logging
from math import ceil
from PIL import Image, ImageDraw, ImageEnhance, ImageOps, ImageFilter

# Create a custom logging configuration
log_format = "%(asctime)s - %(levelname)s - %(message)s"
log_file = 'AutoArtBookNextLog.log'

# Configure the root logger
logging.basicConfig(
    level=logging.DEBUG,
    format=log_format,
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)  # Send logs to the console
    ]
)

# Get the logger instance
logger = logging.getLogger(__name__)


class Config(object):
    def __init__(self, args):
        self.roms_dir = args.roms_dir
        self.box_art_dir = args.box_art_dir
        self.slides_dir = args.slides_dir
        self.logos_dir = args.logos_dir
        self.core_info_dir = args.core_info_dir
        self.system_map_path = args.system_map_path
        with open(self.system_map_path, "r") as file:
            self.system_map = json.load(file)
        self.valid_muos_system_names_path = args.valid_muos_system_names_path
        self.screen_height = args.screen_height
        self.screen_width = args.screen_width
        self.background_hex = args.background_hex
        self.gap_between_slides = args.gap_between_slides
        self.icon_height_percent = args.icon_height_percent
        self.icon_width_percent = args.icon_width_percent
        self.max_icon_height = (args.screen_height * args.icon_height_percent)
        self.max_icon_width = (args.screen_width * args.icon_width_percent) 
        self.deselected_brightness = args.deselected_brightness
        self.shadow_strength = args.shadow_strength
        self.folders = get_folders(self.roms_dir)
        self.folder_console_associations = get_folder_core_associations(self.folders, self.core_info_dir)
        self.example_slide_image = Image.open(os.path.join(self.slides_dir, f"_default.png")).convert("RGBA")
        self.slide_height = self.example_slide_image.height
        self.slide_width = self.example_slide_image.width

        first_row = list(self.example_slide_image.getdata())[0:self.example_slide_image.width]
        alpha_threshold = 200
        self.real_slide_width = sum(1 for pixel in first_row if pixel[3] > alpha_threshold)
    def log_config(self):
        # Log directories
        logger.info("=" * 50)  # Divider line
        logger.info("Directories:")
        logger.info("=" * 50)
        logger.info(f"ROMs Directory: {self.roms_dir}")
        logger.info(f"Box Art Directory: {self.box_art_dir}")
        logger.info(f"System Image Slides Directory: {self.slides_dir}")
        logger.info(f"System Image Logos Directory: {self.logos_dir}")
        logger.info(f"Folder Core Association Directory: {self.core_info_dir}")

        logger.info("=" * 50)  # Divider line
        logger.info("Device Settings:")
        logger.info("=" * 50)

        logger.info(f"Screen Width: {self.screen_width}")
        logger.info(f"Screen Height: {self.screen_height}")

        # Log results
        logger.info("=" * 50)  # Divider line
        logger.info("Optional settings:")
        logger.info("=" * 50)
        logger.info(f"  Background color: {self.background_hex}")
        logger.info(f"  Gap between slides: {self.gap_between_slides}px")
        logger.info(f"  Icon height max percent of screen height: {self.icon_height_percent*100}%")
        logger.info(f"  Icon width max percent of screen width: {self.icon_width_percent*100}%")
        logger.info(f"  Calculated max icon height: {self.max_icon_height}px")
        logger.info(f"  Calculated max icon width: {self.max_icon_width}px")
    def log_associations(self):
        for folder in self.folder_console_associations.keys():
            logger.info(f"  {folder}: {self.folder_console_associations[folder]}")

def generateFolderImage(folder_name:str, config:Config):
    """
    Generate a folder image for the given folder name. In the style of Art Book Next.
    :param folder_name: Name of the folder.
    :param config: Configuration object.
    :return: Image object.
    """
    height_multiplier = config.slide_height/config.screen_height
    width_multiplier = config.slide_width/config.screen_width
    rendered_image_multiplier = max(height_multiplier, width_multiplier)
    rendered_image_width, rendered_image_height = int(config.screen_width*rendered_image_multiplier), int(config.screen_height*rendered_image_multiplier)
    image = Image.new("RGBA", (rendered_image_width, rendered_image_height), config.background_hex)
    draw = ImageDraw.Draw(image)


    change_in_x = int(config.real_slide_width+(config.gap_between_slides*(rendered_image_multiplier)))

    slides_per_screen = ceil(rendered_image_width/change_in_x)+1

    muOS_system_name = config.folder_console_associations[folder_name.lower()]

    # draw the correct slide image in the middle of the screen
    if os.path.exists(os.path.join(config.slides_dir, f"{folder_name}.png")):
        slide_image = Image.open(os.path.join(config.slides_dir, f"{folder_name}.png"))
    else:
        if muOS_system_name in config.system_map.keys():
            es_system_image_name = config.system_map[muOS_system_name]
        else:
            es_system_image_name = "_default.png"
    
        slide_image = Image.open(os.path.join(config.slides_dir, f"{es_system_image_name}"))
    image_middle_x = int((rendered_image_width - slide_image.width) / 2)
    image.alpha_composite(slide_image, (image_middle_x, 0))
    slides_left = slides_per_screen-1
    slides_to_the_left = ceil(slides_left/2)
    slides_to_the_right = ceil(slides_left/2)
    index=1
    while index <= slides_to_the_left:
        # draw the correct slide image in the middle of the screen
        current_folder_index = config.folders.index(folder_name)
        new_folder_index = (current_folder_index+index)%len(config.folders)
        current_folder_name = config.folders[new_folder_index]
        current_muOS_system_name = config.folder_console_associations[current_folder_name.lower()]
        if muOS_system_name in config.system_map.keys():
            current_es_system_image_name = config.system_map[current_muOS_system_name]
        else:
            current_es_system_image_name = "_default.png"
        current_slide_image = Image.open(os.path.join(config.slides_dir, f"{current_es_system_image_name}"))
        enhancer = ImageEnhance.Brightness(current_slide_image)
        # to reduce brightness by 50%, use factor 0.5
        current_slide_image = enhancer.enhance(config.deselected_brightness)
        image.alpha_composite(current_slide_image, (image_middle_x+index*change_in_x, 0))
        index += 1
    index=1
    while index <= slides_to_the_right:
        # draw the correct slide image in the middle of the screen
        current_folder_index = config.folders.index(folder_name)
        new_folder_index = (current_folder_index-index)%len(config.folders)
        current_folder_name = config.folders[new_folder_index]
        current_muOS_system_name = config.folder_console_associations[current_folder_name.lower()]
        if muOS_system_name in config.system_map.keys():
            current_es_system_image_name = config.system_map[current_muOS_system_name]
        else:
            current_es_system_image_name = "_default.png"
        current_slide_image = Image.open(os.path.join(config.slides_dir, f"{current_es_system_image_name}"))

        enhancer = ImageEnhance.Brightness(current_slide_image)
        # to reduce brightness by 50%, use factor 0.5
        current_slide_image = enhancer.enhance(config.deselected_brightness)
        image.alpha_composite(current_slide_image, (image_middle_x-index*change_in_x, 0))
        index += 1

    ## draw the logo in the middle of the screen
    logo_image = Image.open(os.path.join(config.logos_dir, f"{muOS_system_name}.png")).convert("RGBA")
    logo_image_multiplier = min(config.max_icon_height/logo_image.height, config.max_icon_width/logo_image.width)*rendered_image_multiplier
    logo_image = logo_image.resize((int(logo_image.width*logo_image_multiplier), int(logo_image.height*logo_image_multiplier)), Image.LANCZOS)

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

    return(image.resize((config.screen_width, config.screen_height), Image.LANCZOS))

def get_folders(roms_dir):
    """
    Get all folders in the ROMs directory.

    :param roms_dir: Path to the ROMs directory.
    :return: List of folders.
    """
    folders = []
    for folder in os.listdir(roms_dir):
        if os.path.isdir(os.path.join(roms_dir, folder)):
            if (not str.startswith(folder, ".")) and (not str.startswith(folder, "_"))  :
                folders.append(folder)
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

def verify_json_mapping(json_file_path, valid_muos_system_names_path, slides_dir):
    """
    Verifies that the JSON file has a mapping for each system image slide.

    :param json_file_path: Path to the JSON file.
    :param valid_muos_system_names_path: Path to the file containing valid MUOS system names.
    :param slides_dir: Path to the system image slides directory.
    :return: True if the JSON file has a mapping for each system image slide, False otherwise.
    """
    with open(json_file_path, "r") as f:
        json_data = json.load(f)

    # Get valid MUOS system names
    with open(valid_muos_system_names_path, "r") as f:
        valid_muos_system_names = f.read().splitlines()

    # Get system image slides
    slides = os.listdir(slides_dir)

    # Check if the JSON file has a mapping for each system image slide
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
        if es_system_names not in slides:
            logger.error(f"[ERROR] No slide found for system name: {es_system_names}")
            return False
        else:
            logger.info(f"[OK] JSON file has a slide for system name: {es_system_names}")

    logger.info(f"[OK] JSON file has a mapping for each system image slide.")
    return True

def validate_directory(path, description):
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

def validate_file(path, description):
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

    # Required arguments
    parser.add_argument("--roms_dir", required=True, help="Path to the ROMs directory")
    parser.add_argument("--box_art_dir", required=True, help="Path to the box art directory")
    parser.add_argument("--slides_dir", required=True, help="Path to the system image slides directory")
    parser.add_argument("--logos_dir", required=True, help="Path to the system image logos directory")
    parser.add_argument("--core_info_dir", required=True, help="Path to the folder where folder core associations are stored")
    parser.add_argument("--system_map_path", required=True, help="Path to the file where muOS -> ES system name mapping is stored")
    parser.add_argument("--valid_muos_system_names_path", required=True, help="Path to the file containing valid muOS system names")
    parser.add_argument("--screen_height", type=int, required=True, help="Screen height in pixels")
    parser.add_argument("--screen_width", type=int, required=True, help="Screen width in pixels")

    # Optional arguments with defaults
    parser.add_argument(
        "--background_hex", default="#000000",
        help="Background color in hex format (default: #000000)"
    )
    parser.add_argument(
        "--gap_between_slides", type=int, default=10,
        help="Gap between slides in pixels (default: 10)"
    )
    parser.add_argument(
        "--icon_height_percent", type=float, default=0.5,
        help="Max icon height as a percentage of screen height (default is 50%: 0.5 )"
    )
    parser.add_argument(
        "--icon_width_percent", type=float, default=0.5,
        help="Max icon width as a percentage of screen width (default is 70%: 0.7)"
    )
    parser.add_argument(
        "--deselected_brightness", type=float, default=0.5,
        help="How close to full brightness are the deselected folders (default is 20%: 0.2)"
    )
    parser.add_argument(
        "--shadow_strength", type=int, default=1,
        help="How strong do you want the drop shadow to be? (default is 1: int[0-5])"
    )

    args = parser.parse_args()

    logger.info("=" * 50)  # Divider line
    logger.info("Checking if given directories are valid")
    logger.info("=" * 50)

    # Validate directories
    roms_valid = validate_directory(args.roms_dir, "ROMs Directory")
    box_art_valid = validate_directory(args.box_art_dir, "Box Art Directory")
    slides_valid = validate_directory(args.slides_dir, "System Image Slides Directory")
    logos_valid = validate_directory(args.logos_dir, "System Image Logos Directory")
    core_info_valid = validate_directory(args.core_info_dir, "Folder Core Association Directory")
    system_map_valid = validate_file(args.system_map_path, "System Map File")
    valid_muos_system_names_valid = validate_file(args.valid_muos_system_names_path, "Valid muOS System Names File")

    # Validation summary
    if roms_valid and box_art_valid and slides_valid and logos_valid and core_info_valid and system_map_valid and valid_muos_system_names_valid:
        logger.info("All directories are valid. Proceeding with the next steps...")
    else:
        logger.info(
            "One or more directories are invalid. Please check the paths and try again."
        )
        sys.exit(1)  # Exit with an error code if any directory is invalid

    # Log configuration
    config = Config(args)
    config.log_config()

    logger.info("=" * 50)  # Divider line
    logger.info("Folder Console Associations:")
    logger.info("=" * 50)
    config.log_associations()

    logger.info("=" * 50)  # Divider line
    logger.info("Checking JSON mapping")
    logger.info("=" * 50)
    verify_json_mapping(config.system_map_path,config.valid_muos_system_names_path,config.slides_dir)

    for folder in config.folders:
        generateFolderImage(folder, config).save(os.path.join(config.box_art_dir, f"{folder}.png"))
        logger.info(f"Successfully generated image for folder: {folder}")
    

if __name__ == "__main__":
    main()
