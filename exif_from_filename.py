import logging
import os
from pathlib import Path
from datetime import datetime
from PIL import Image
import piexif
import fire
from tqdm import tqdm

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.WARNING)

def parse_date_iOS_filename(filename: Path):
    _LOGGER.debug(f"Trying iOS filename parser")
    # Extract date and time from filename on iPhone (old)
    # Check that file ends with .jpg or .jpeg
    if filename.suffix.lower() not in ['.jpg', '.jpeg']:
        return None
    date_str = filename.stem
    try:
        # Parse the date string
        date_obj = datetime.strptime(date_str, '%Y-%m-%d %H.%M.%S')
        return date_obj.strftime("%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None



FILENAME_PARSERS = [
    parse_date_iOS_filename,
]

def parse_date_from_filename(filename: Path):
    for parser in FILENAME_PARSERS:
        date = parser(filename)
        if date:
            return date
    return None


def update_exif_date(image_path: Path):
    try:
        # Open the image
        img = Image.open(image_path)

        # Check if EXIF data exists
        if 'exif' in img.info:
            exif_dict = piexif.load(img.info['exif'])
        else:
            exif_dict = {'0th': {}, '1st': {}, 'Exif': {}, 'GPS': {}, 'Interop': {}}

        # Check if DateTimeOriginal tag is already set
        if piexif.ExifIFD.DateTimeOriginal not in exif_dict['Exif']:
            # Parse date from filename
            date_taken = parse_date_from_filename(image_path)

            if date_taken:
                # Set the DateTimeOriginal tag
                exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = date_taken.encode('utf-8')

                # Save the updated EXIF data
                exif_bytes = piexif.dump(exif_dict)
                img.save(image_path, exif=exif_bytes)
                _LOGGER.info(f"Updated EXIF date for {image_path}")
            else:
                _LOGGER.debug(f"Could not parse date from filename: {image_path}")
        else:
            _LOGGER.debug(f"EXIF date already set for {image_path}")

    except Exception as e:
        _LOGGER.warning(f"Error processing {image_path}: {str(e)}")


def process_directory(directory: str, verbosity: int = logging.INFO):
    """
    Process all images in the given directory and update their EXIF date based on filename, if missing
    """
    _LOGGER.setLevel(verbosity)

    for dir_path, dir_names, file_names in tqdm(Path(directory).walk()):
        _LOGGER.info(f"Processing directory: {dir_path}")
        for filename in file_names:
            _LOGGER.info(f"Processing file: {filename}")
            image_path = dir_path / filename
            update_exif_date(image_path)


# Usage
if __name__ == "__main__":
    fire.Fire(process_directory)