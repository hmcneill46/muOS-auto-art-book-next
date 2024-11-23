import argparse
import os
import sys

class Config(object):
    def __init__(self, args):
        self.roms_dir = args.roms_dir
        self.box_art_dir = args.box_art_dir
        self.slides_dir = args.slides_dir
        self.logos_dir = args.logos_dir
        self.core_info_dir = args.core_info_dir
        self.screen_height = args.screen_height
        self.screen_width = args.screen_width
        self.background_hex = args.background_hex
        self.gap_between_slides = args.gap_between_slides
        self.icon_height_percent = args.icon_height_percent
        self.icon_width_percent = args.icon_width_percent
        self.max_icon_height = (args.screen_height * args.icon_height_percent) / 100
        self.max_icon_width = (args.screen_width * args.icon_width_percent) / 100
        self.folder_console_associations = get_folder_core_associations(self.roms_dir, self.core_info_dir)
    def print_config(self):
        # Print directories
        print("\nDirectories:")
        print(f"ROMs Directory: {self.roms_dir}")
        print(f"Box Art Directory: {self.box_art_dir}")
        print(f"System Image Slides Directory: {self.slides_dir}")
        print(f"System Image Logos Directory: {self.logos_dir}")
        print(f"Folder Core Association Directory: {self.core_info_dir}")

        print(f"\nScreen Width: {self.screen_width}")
        print(f"Screen Height: {self.screen_height}")

        # Print results
        print("\nOptional settings:")
        print(f"  Background color: {self.background_hex}")
        print(f"  Gap between slides: {self.gap_between_slides}px")
        print(f"  Icon height max percent of screen height: {self.icon_height_percent}%")
        print(f"  Icon width max percent of screen width: {self.icon_width_percent}%")
        print(f"  Calculated max icon height: {self.max_icon_height}px")
        print(f"  Calculated max icon width: {self.max_icon_width}px")
    def print_associations(self):
        for folder in self.folder_console_associations.keys():
            print(f"  {folder}: {self.folder_console_associations[folder]}")

def generateFolderImage(folder_name:str, config:Config):
    print(f"Generating image for folder: {folder_name}")
    # Get core info
    core_info = get_core_info(folder_name, config.core_info_dir)
    if core_info is None:
        print(f"[ERROR] Could not find core info for folder: {folder_name}")
        return

    # Get ROMs
    roms = get_roms(folder_name, config.roms_dir)
    if not roms:
        print(f"[ERROR] Could not find any ROMs for folder: {folder_name}")
        return

    # Get box art
    box_art = get_box_art(roms, config.box_art_dir)
    if not box_art:
        print(f"[ERROR] Could not find any box art for folder: {folder_name}")
        return

    # Get system image
    system_image = get_system_image(core_info, config.slides_dir)
    if system_image is None:
        print(f"[ERROR] Could not find system image for folder: {folder_name}")
        return

    # Get system logo
    system_logo = get_system_logo(core_info, config.logos_dir)
    if system_logo is None:
        print(f"[ERROR] Could not find system logo for folder: {folder_name}")
        return

    # Generate folder image
    folder_image = generate_folder_image(
        folder_name, roms, box_art, system_image, system_logo, config
    )

    # Save folder image
    folder_image.save(f"{folder_name}.png")
    print(f"Successfully generated image for folder: {folder_name}")

def get_folder_core_associations(roms_dir, core_info_dir):
    """
    Get folder core associations from the core info directory.

    :param roms_dir: Path to the ROMs directory.
    :param core_info_dir: Path to the core info directory.
    :return: Dictionary of folder core associations.
    """
    folder_core_associations = {}
    for folder in os.listdir(roms_dir):
        if (not str.startswith(folder, ".")) and (not str.startswith(folder, "_"))  :
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

def validate_directory(path, description):
    """
    Validates whether the provided path is a valid directory.

    :param path: Path to validate.
    :param description: Description of the directory (for error messages).
    :return: True if valid, False otherwise.
    """
    if os.path.isdir(path):
        print(f"[OK] {description}: '{path}' is a valid directory.")
        return True
    else:
        print(f"[ERROR] {description}: '{path}' is not a valid directory.")
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
        "--icon_height_percent", type=float, default=50.0,
        help="Max icon height as a percentage of screen height (default: 50%)"
    )
    parser.add_argument(
        "--icon_width_percent", type=float, default=50.0,
        help="Max icon width as a percentage of screen width (default: 50%)"
    )

    args = parser.parse_args()

    # Validate directories
    roms_valid = validate_directory(args.roms_dir, "ROMs Directory")
    box_art_valid = validate_directory(args.box_art_dir, "Box Art Directory")
    slides_valid = validate_directory(args.slides_dir, "System Image Slides Directory")
    logos_valid = validate_directory(args.logos_dir, "System Image Logos Directory")
    core_info_valid = validate_directory(args.core_info_dir, "Folder Core Association Directory")

    # Validation summary
    if roms_valid and box_art_valid and slides_valid and logos_valid and core_info_valid:
        print("\nAll directories are valid. Proceeding with the next steps...")
    else:
        print(
            "\nOne or more directories are invalid. Please check the paths and try again."
        )
        sys.exit(1)  # Exit with an error code if any directory is invalid

    # Print configuration
    config = Config(args)
    config.print_config()

    
    print(f"\nFolder Console Associations:")
    config.print_associations()
    

if __name__ == "__main__":
    main()
