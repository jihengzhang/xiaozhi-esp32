#!/usr/bin/env bash

# Detect whether the script is executed (not sourced)
__ESP_INIT_EXECUTED=0
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  __ESP_INIT_EXECUTED=1
  set -euo pipefail
fi

# ESP init helper
# Args:
#   -set-idf  : append ESP-IDF aliases to ~/.bashrc
#   -en_tty   : enable Linux serial access for /dev/ttyACM0
# Env:
#   IDF_EXPORT_PATH : path to ESP-IDF export.sh (default below)
#   BASHRC_PATH     : path to bashrc (default ~/.bashrc)

IDF_EXPORT_PATH="${IDF_EXPORT_PATH:-$HOME/esp/v5.5.2/esp-idf/export.sh}"
BASHRC_PATH="${BASHRC_PATH:-$HOME/.bashrc}"

BLOCK_START="# >>> xiaozhi-esp32 set-idf aliases >>>"
BLOCK_END="# <<< xiaozhi-esp32 set-idf aliases <<<"

usage() {
  cat <<EOF
Usage: $(basename "$0") [-set-idf | -en_tty]

  -set-idf  Append ESP-IDF aliases to ~/.bashrc:
            set-idf, set_idf -> source ~/esp/v5.5.2/esp-idf/export.sh

  -en_tty   Add user to 'dialout' and verify access to /dev/ttyACM0:
            sudo usermod -a -G dialout "$USER"
            newgrp dialout
            id -nG | grep -w dialout && ls -l /dev/ttyACM0
EOF
}

ensure_bashrc() {
  if [[ ! -f "$BASHRC_PATH" ]]; then
    touch "$BASHRC_PATH"
  fi
}

remove_existing_block() {
  if grep -qF "$BLOCK_START" "$BASHRC_PATH" 2>/dev/null; then
    awk -v start="$BLOCK_START" -v end="$BLOCK_END" '
      $0==start {inblock=1; next}
      $0==end {inblock=0; next}
      !inblock {print}
    ' "$BASHRC_PATH" > "${BASHRC_PATH}.tmp" && mv "${BASHRC_PATH}.tmp" "$BASHRC_PATH"
  fi
}

append_block() {
  {
    cat <<'EOF'

# >>> xiaozhi-esp32 set-idf aliases >>>
# Added by xiaozhi-esp32 helper on $(date)
alias set-idf='. ~/esp/v5.5.2/esp-idf/export.sh'
alias set_idf='. ~/esp/v5.5.2/esp-idf/export.sh'

# <<< xiaozhi-esp32 set-idf aliases <<<
EOF
  } >> "$BASHRC_PATH"
}

set_idf_action() {
  if [[ ! -f "$IDF_EXPORT_PATH" ]]; then
    echo "Error: ESP-IDF export script not found at: $IDF_EXPORT_PATH" >&2
    echo "Hint: Install ESP-IDF or set IDF_EXPORT_PATH to the correct export.sh" >&2
    return 1
  fi
  ensure_bashrc
  ts=$(date +%Y%m%d-%H%M%S)
  cp "$BASHRC_PATH" "${BASHRC_PATH}.bak.$ts" 2>/dev/null || true
  remove_existing_block
  append_block
  echo "Aliases added to $BASHRC_PATH"
  echo "- set-idf  -> . ~/esp/v5.5.2/esp-idf/export.sh"
  echo "- set_idf  -> . ~/esp/v5.5.2/esp-idf/export.sh"
  echo "Reload your shell: source \"$BASHRC_PATH\"" 
  echo "Then run: set-idf (or set_idf)"
}

en_tty_action() {
  if [[ "$(uname -s)" != "Linux" ]]; then
    echo "-en_tty is only applicable on Linux." >&2
    return 1
  fi
  echo "Adding $USER to 'dialout' group..."
  sudo usermod -a -G dialout "$USER"
  echo "Starting newgrp dialout session to verify access..."
  newgrp dialout <<'EOS'
echo "Checking group membership and device access:"
id -nG | grep -w dialout && ls -l /dev/ttyACM0
EOS
  echo "Note: Other terminals may need restart to pick up the new group membership."
}

main() {
  if [[ $# -lt 1 ]]; then
    usage
    return 0
  fi
  case "${1}" in
    -set-idf)
      set_idf_action
      ;;
    -en_tty)
      en_tty_action
      ;;
    -h|--help)
      usage
      ;;
    *)
      echo "Unknown option: ${1}" >&2
      usage
      return 2
      ;;
  esac
}



if (( __ESP_INIT_EXECUTED )); then
  main "$@"
fi
