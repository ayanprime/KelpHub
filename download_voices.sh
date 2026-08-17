#!/bin/bash
# old piper voice downloader, NOT USED ANYMORE since I switched to coqui
# keeping it around in case I ever want to go back to piper (faster but
# more robotic sounding)

set -e
mkdir -p voices
cd voices

BASE_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en"

download_voice () {
    lang_code=$1
    speaker=$2
    quality=$3
    name="${lang_code}-${speaker}-${quality}"

    if [ -f "${name}.onnx" ]; then
        echo "already have ${name}, skipping"
        return
    fi

    echo "downloading ${name}..."
    if curl -f -L -o "${name}.onnx" "${BASE_URL}/${lang_code}/${speaker}/${quality}/${name}.onnx?download=true" \
        && curl -f -L -o "${name}.onnx.json" "${BASE_URL}/${lang_code}/${speaker}/${quality}/${name}.onnx.json?download=true"; then
        echo "  done"
    else
        echo "  FAILED, deleting any partial file"
        rm -f "${name}.onnx" "${name}.onnx.json"
    fi
}

# my old voice picks from the piper version
download_voice en_US hfc_female medium   # kelp
download_voice en_US amy medium          # quill
download_voice en_US ryan high           # axiom
download_voice en_US joe medium          # cipher
download_voice en_US john medium         # vault
download_voice en_US norman medium       # orion
download_voice en_US kristin medium      # vita

echo ""
echo "done, check above for any FAILED lines"
