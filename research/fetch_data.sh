#!/usr/bin/env bash
# Re-download the public inputs used by research/tests into research/data and verify them against the
# SHA-256 values observed on 2026-11-07. A mismatch means the publisher changed a file; re-run the tests and
# compare results rather than trusting the committed outputs.
set -euo pipefail
cd "$(dirname "$0")/data"
UA="Mozilla/5.0 (research)"
get() { curl -sSL -m 120 -A "$UA" -o "$2" "$1"; }

E=https://www.esma.europa.eu/sites/default/files
get "$E/2026-10/ESMA65-955014868-17690_MIDAS_Reporting_Instructions.pdf" ESMA65-955014868-17690_MIDAS_Reporting_Instructions.pdf
get "$E/2026-10/ESMA65-955014868-17734_MIDAS_Feedback_File_Sample.csv" ESMA65-955014868-17734_MIDAS_Feedback_File_Sample.csv
get "$E/2026-10/ESMA65-955014868-17735_MIDAS_CryptoAssetRecordKeeping.json" ESMA65-955014868-17735_MIDAS_CryptoAssetRecordKeeping.json
get "$E/2026-10/ESMA65-955014868-17736_MIDAS_CryptoAssetOrderBook.json" ESMA65-955014868-17736_MIDAS_CryptoAssetOrderBook.json
get "$E/2025-11/ESMA65-955014868-15160_MiCA_Order_Book_and_Records_Keeping_Message_Specifications.zip" msgspec.zip
get "$E/2024-12/CASPS.csv" CASPS.csv
get "https://www.iso20022.org/sites/default/files/ISO10383_MIC/ISO10383_MIC.csv" ISO10383_MIC.csv

mkdir -p msgspec && unzip -o -q msgspec.zip -d msgspec
pdftotext -layout ESMA65-955014868-17690_MIDAS_Reporting_Instructions.pdf midas_instructions.txt

# CASPS.csv and ISO10383_MIC.csv are living registers and are expected to drift.
sha256sum -c --quiet <<'EOF' || echo "WARNING: some ESMA MIDAS artifacts changed since 2026-11-07"
7c6c9c01f392cb14872ac97e0b70bdb92a2dd130869fb38d39f47a03571d64b3  ESMA65-955014868-17690_MIDAS_Reporting_Instructions.pdf
ec36fbeb97f028657e80ff08c6f000228f29005357b9dd312f787d5509c7a484  ESMA65-955014868-17734_MIDAS_Feedback_File_Sample.csv
1aa1b9710e906612e24165d4637af6e7b5a26e4413d68d93682aa3fe1f30883d  ESMA65-955014868-17735_MIDAS_CryptoAssetRecordKeeping.json
2fa54f661a3f2776a4f59f49255fb6c1e9ddd452c88dc93beb367bf10052d924  ESMA65-955014868-17736_MIDAS_CryptoAssetOrderBook.json
3dbad33bf8bada6c5a5f9a240ab103112614e71e4f40c882310cdead8f1e7aa4  msgspec.zip
EOF
