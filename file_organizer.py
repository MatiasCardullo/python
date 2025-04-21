# file_organizer.py

import os
import shutil
from datetime import datetime

CATEGORIES = {
    'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'],
    'Documents': ['.pdf', '.docx', '.doc', '.txt', '.odt'],
    'Spreadsheets': ['.xls', '.xlsx', '.csv'],
    'Videos': ['.mp4', '.mkv', '.avi', '.mov'],
    'Audio': ['.mp3', '.wav', '.aac', '.flac'],
    'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
    'Scripts': ['.py', '.js', '.sh', '.bat', '.java', '.cpp'],
    'Others': []
}

def generate_unique_filename(filepath):
    directory, filename = os.path.split(filepath)
    name, ext = os.path.splitext(filename)
    counter = 1

    new_filepath = filepath
    while os.path.exists(new_filepath):
        new_filename = f"{name} ({counter}){ext}"
        new_filepath = os.path.join(directory, new_filename)
        counter += 1

    return new_filepath

def files_are_identical(file1, file2):
    if os.path.getsize(file1) != os.path.getsize(file2):
        return False
    with open(file1, "rb") as f1, open(file2, "rb") as f2:
        return f1.read() == f2.read()

def get_category(extension):
    for category, extensions in CATEGORIES.items():
        if extension.lower() in extensions:
            return category
    return 'Others'


def organize_by_type(target_folder: str, dry_run=False):
    if not os.path.isdir(target_folder):
        raise FileNotFoundError(f"The folder '{target_folder}' does not exist.")

    for filename in os.listdir(target_folder):
        file_path = os.path.join(target_folder, filename)

        if os.path.isfile(file_path):
            _, ext = os.path.splitext(filename)
            category = get_category(ext)
            category_folder = os.path.join(target_folder, category)

            dest_path = os.path.join(category_folder, filename)
            if dry_run:
                print(f"[Dry-run] Would move: {file_path} → {dest_path}")
            else:
                os.makedirs(category_folder, exist_ok=True)
                shutil.move(file_path, dest_path)

    print(f"✔️ Finished organizing by type {'(dry-run mode)' if dry_run else ''}.")


def organize_by_date(target_folder: str, dry_run=False):
    if not os.path.isdir(target_folder):
        raise FileNotFoundError(f"The folder '{target_folder}' does not exist.")

    for filename in os.listdir(target_folder):
        file_path = os.path.join(target_folder, filename)

        if os.path.isfile(file_path):
            mod_time = os.path.getmtime(file_path)
            date = datetime.fromtimestamp(mod_time)
            folder_name = date.strftime("%Y-%m")
            dest_folder = os.path.join(target_folder, folder_name)
            dest_path = os.path.join(dest_folder, filename)

            if dry_run:
                print(f"[Dry-run] Would move: {file_path} → {dest_path}")
            else:
                os.makedirs(dest_folder, exist_ok=True)
                shutil.move(file_path, dest_path)

    print(f"📅 Finished organizing by date {'(dry-run mode)' if dry_run else ''}.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Organize files in a folder.")
    parser.add_argument("folder", help="Target folder to organize")
    parser.add_argument(
        "--by", choices=["type", "date"], default="type", help="Organize by file type or date"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview actions without moving files"
    )

    args = parser.parse_args()

    if args.by == "type":
        organize_by_type(args.folder, dry_run=args.dry_run)
    elif args.by == "date":
        organize_by_date(args.folder, dry_run=args.dry_run)
