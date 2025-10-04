#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  cat <<USAGE
Usage: $(basename "$0") <model-name> [target-dir]

Downloads a quantised GGUF model using curl or wget. The MODEL_BASE_URL
environment variable can be used to override the source repository
(defaults to llama.cpp's public Hugging Face mirror).
USAGE
  exit 1
fi

MODEL_NAME="$1"
TARGET_DIR="${2:-models}"
BASE_URL="${MODEL_BASE_URL:-https://huggingface.co/TheBloke/$MODEL_NAME/resolve/main}"
FILENAME="${MODEL_FILE:-$MODEL_NAME.gguf}"

mkdir -p "$TARGET_DIR"
OUTPUT_PATH="$TARGET_DIR/$FILENAME"

if command -v curl >/dev/null 2>&1; then
  DOWNLOADER=(curl -Lfo)
elif command -v wget >/dev/null 2>&1; then
  DOWNLOADER=(wget -O)
else
  echo "Neither curl nor wget is available. Install one to download models." >&2
  exit 2
fi

echo "Downloading $FILENAME from $BASE_URL"
"${DOWNLOADER[@]}" "$OUTPUT_PATH" "$BASE_URL/$FILENAME"

echo "Model saved to $OUTPUT_PATH"
