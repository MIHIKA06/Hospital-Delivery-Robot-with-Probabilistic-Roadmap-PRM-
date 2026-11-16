#!/bin/sh
# Build the report .docx and .pdf (two passes so the Index page numbers are right).
#   sh docs/report/make_report.sh "path/to/AISR_Sample_Project_Report.docx"
# Needs: python-docx, LibreOffice (soffice), poppler (pdfinfo, pdftotext).
set -e
cd "$(dirname "$0")/../.."
SAMPLE="${1:-../AISR_Sample_Project_Report (1).docx}"
R=docs/report
SOFFICE="${SOFFICE:-/Applications/LibreOffice.app/Contents/MacOS/soffice}"
OUT=AISR_P05_G06_Report

pdf() { (cd $R && "$SOFFICE" --headless --convert-to pdf $OUT.docx >/dev/null 2>&1); }

python3 $R/build_report.py "$SAMPLE" $R/$OUT.docx
pdf
python3 $R/paginate.py $R/$OUT.pdf $R/report_items.json $R/pages.json >/dev/null
python3 $R/build_report.py "$SAMPLE" $R/$OUT.docx $R/pages.json
pdf
python3 $R/paginate.py $R/$OUT.pdf $R/report_items.json $R/pages_check.json | head -1
cmp -s $R/pages.json $R/pages_check.json && echo "Index page numbers verified." \
  || echo "WARNING: page numbers moved; run this script again."
rm -f $R/pages_check.json
pdfinfo $R/$OUT.pdf | grep Pages
