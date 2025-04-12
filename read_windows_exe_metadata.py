#!/usr/bin/env python3
"""
Show metadata for a Windows executable.

This script runs on any platform.

Copyright (C) 2025 by Andrew Ziem.  All rights reserved.
License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>.
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.
"""
import sys
import argparse

try:
    import pefile
except ImportError:
    print("Error: pefile module is required. Try running: 'pip install pefile'.")
    sys.exit(1)


def extract_string_table_metadata(pe, metadata, metadata_fields):
    # Extract string table info
    if hasattr(pe, 'FileInfo') and pe.FileInfo:
        for fileinfo in pe.FileInfo[0]:
            if fileinfo.Key.decode() == 'StringFileInfo':
                for st in fileinfo.StringTable:
                    for key, value in st.entries.items():
                        decoded_key = key.decode()
                        decoded_value = value.decode()

                        if decoded_key in metadata_fields:
                            metadata_key = metadata_fields[decoded_key]
                            metadata[metadata_key] = decoded_value
                        else:
                            print(f"Unknown key: {decoded_key}")


def extract_metadata(file_path):
    try:
        pe = pefile.PE(file_path)
    except pefile.PEFormatError:
        print("Error: Not a valid PE file.")
        return {}

    metadata_fields = {
        'FileDescription': 'File description',
        'FileVersion': 'File version',
        'ProductName': 'Product name',
        'ProductVersion': 'Product version',
        'LegalCopyright': 'Legal copyright',
        'LegalTrademarks': 'Legal trademarks',
        'Comments': 'Comments',
        'CompanyName': 'Company name'
    }

    # Initialize metadata with defaults
    metadata = {field: 'N/A' for field in metadata_fields.values()}
    metadata['Digitally signed'] = 'No'

    extract_string_table_metadata(pe, metadata, metadata_fields)

    # Check digital signature
    if pe.OPTIONAL_HEADER.DATA_DIRECTORY[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_SECURITY']].Size > 0:
        metadata['Digitally signed'] = 'Yes'

    # Print all metadata
    for field_name, value in metadata.items():
        print(f"{field_name}: {value}")

    return metadata


def main():
    parser = argparse.ArgumentParser(
        description='Check metadata of Windows executable')
    parser.add_argument('file_path', help='Path to the Windows executable')
    parser.add_argument('--require-signature', '-r', action='store_true',
                        help='Exit with code 1 if digital signature is missing')
    args = parser.parse_args()

    metadata = extract_metadata(args.file_path)

    if args.require_signature and metadata.get('Digitally signed', 'No') == 'No':
        sys.exit(1)


if __name__ == "__main__":
    main()
