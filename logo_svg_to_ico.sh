#!/bin/sh

# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (c) 2026 Andrew Ziem.
# This work is licensed under the terms of the GNU GPL, version 3 or
# later.  See the COPYING file in the top-level directory.

set -e

INPUT_SVG="logo-square.svg"
OUTPUT_ICO="logo.ico"
ICON_SIZES=(16 32 48 64 128 256)

print_section() {
  echo ""
  echo "==== $1 ===="
  echo ""
}

print_section "Checking for tools..."
for tool in inkscape pngcrush icotool identify magick; do
  if ! command -v "${tool}" >/dev/null 2>&1; then
    echo >&2 "${tool} is not installed. Aborting."
    exit 1
  fi
done

print_section "Checking for input file..."
if [ ! -f "${INPUT_SVG}" ]; then
  echo "Input file ${INPUT_SVG} not found"
  exit 1
fi

print_section "Validating square resolution..."
dimensions=$(identify -format "%w %h" "${INPUT_SVG}")
WIDTH=$(echo "${dimensions}" | cut -d' ' -f1)
HEIGHT=$(echo "${dimensions}" | cut -d' ' -f2)
if [ -z "${WIDTH}" ] || [ -z "${HEIGHT}" ]; then
  echo "Could not determine SVG dimensions"
  exit 1
fi
if [ "${WIDTH}" -ne "${HEIGHT}" ]; then
  echo "Input SVG must be square, but is ${WIDTH}x${HEIGHT}"
  exit 1
fi

print_section "Checking for embedded bitmaps..."
if grep -qi "<image" "${INPUT_SVG}"; then
  echo "Detected embedded bitmap <image> tags in ${INPUT_SVG}. Please remove them."
  exit 1
fi

print_section "Generating icons..."
for size in "${ICON_SIZES[@]}"; do
  echo "  * icon_${size}.png"
  inkscape "${INPUT_SVG}" --export-type=png --export-filename=icon_${size}.png --export-width="${size}"
done
ls -la icon_*.png

print_section "Action required: Manually check the visual quality of the icons"
xdg-open icon_16.png
xdg-open icon_256.png

print_section "Action required: Generating preview against black and white"
echo "It should look good on either background"
magick \
  \( icon_256.png -background "#111111" -gravity center -extent 300x300 \) \
  \( icon_256.png -background "#f5f5f5" -gravity center -extent 300x300 \) \
  +append icon_256_preview.png
xdg-open icon_256_preview.png

print_section "FYI: Size before PNG optimization"
du -bcs icon_*.png

print_section "Optimizing PNG..."
for size in "${ICON_SIZES[@]}"; do
  if [ -f "icon_${size}.png" ]; then
    pngcrush -ow -rem allb -reduce -brute "icon_${size}.png"
  else
    echo "Warning: icon_${size}.png not found, skipping optimization"
  fi
done

print_section "FYI: Size after PNG optimization"
du -bcs icon_*.png

print_section "Generating ${OUTPUT_ICO}.."
icotool -c \
  --raw=icon_16.png \
  --raw=icon_32.png \
  --raw=icon_48.png \
  --raw=icon_64.png \
  --raw=icon_128.png \
  --raw=icon_256.png \
  -o "${OUTPUT_ICO}"

print_section "Action required: check for small file size"
ls -la "${OUTPUT_ICO}"

print_section "Action required: check for RGBA and sizes 16,32,48,64,128,256 squared"
file "${OUTPUT_ICO}"
identify "${OUTPUT_ICO}"

print_section "Action required: cleanup reminder"
echo "When you are done reviewing, manually run: rm icon_*.png"