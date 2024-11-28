import os
import argparse
import subprocess
import re
import json
import hashlib


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


def calculate_file_hash(file_path):
    """Calculate the SHA256 hash of a file."""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()


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
    parser = argparse.ArgumentParser(description="Automate font binary generation.")
    parser.add_argument("font_path", type=str, help="Path to the font file (e.g., FallingSkyBdObl.otf).")
    parser.add_argument("output_dir", type=str, help="Directory to save the output binaries.")
    parser.add_argument("size_range", type=str, help="Range of sizes as 'min-max' (e.g., '0-100').")
    parser.add_argument("--step_size", type=int, default=1, help="Step size for the loop (default is 1).")
    parser.add_argument("--ranges_file", default="ranges.txt", type=str, help="Path to the ranges.txt file.")
    parser.add_argument("--cache_file", type=str, default="font_ranges_cache.json", help="Path to the cache file.")
    parser.add_argument("--lv_font_conv_binary", type=str, default="lv_font_conv", help="Path to the font file (e.g., FallingSkyBdObl.otf).")
    args = parser.parse_args()

    # Parse the ranges file
    print("Parsing Unicode ranges file...")
    ranges = parse_ranges_file(args.ranges_file)

    # Extract the size range
    try:
        size_min, size_max = map(int, args.size_range.split('-'))
        if size_min > size_max:
            raise ValueError("Invalid size range: min size must be <= max size.")
    except ValueError:
        print("Invalid size_range format. Use 'min-max', e.g., '0-100'.")
        return

    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    # Check if lv_font_conv is available
    if not check_lv_font_conv(args.lv_font_conv_binary):
        print("lv_font_conv tool not found or not executable.")
        return

    # Check which ranges are supported
    supported_ranges = check_supported_ranges(args.font_path, ranges, args.cache_file, args.lv_font_conv_binary)
    if not supported_ranges:
        print("No supported ranges found for the font.")
        return
    print("Supported ranges:")
    for unicode_range, block_name in supported_ranges.items():
        print(f"{unicode_range} ({block_name})")

    # Generate font binaries
    size = size_min
    font_name = os.path.splitext(os.path.basename(args.font_path))[0]
    while size <= size_max:
        output_file = os.path.join(args.output_dir, f"{font_name}-{size}.bin")
        command = [
            args.lv_font_conv_binary,
            "--bpp", "4",
            "--size", f"{size}",
            "--font", args.font_path,
            "-r", ",".join(supported_ranges.keys()),
            "--format", "bin",
            "--no-compress",
            "--no-prefilter",
            "-o", output_file,
        ]
        print(f"Generating binary for size {size} -> {output_file}")
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error generating binary for size {size}: {e}")

        size += args.step_size


if __name__ == "__main__":
    main()
