#!/bin/sh
# Build a signed copy for printing: AISR_P05_G06_Report_signed.pdf.
# Put each member's signature as docs/report/signatures/<firstname>.png (e.g. mihika.png).
# Signatures and the signed copy are git-ignored, so they never go to GitHub.
cd "$(dirname "$0")/../.."
OUT=AISR_P05_G06_Report_signed SIGN_DIR="$PWD/docs/report/signatures" sh docs/report/make_report.sh "$@"
