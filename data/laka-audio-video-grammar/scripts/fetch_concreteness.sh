#!/usr/bin/env bash
# Fetch the full Brysbaert, Warriner & Kuperman (2014) concreteness norms.
#
# The compiler ships a three-band reduction covering ~2,500 frequent words,
# which is enough for the depiction gate to abstain safely. This gives you
# full-precision ratings for ~40,000 lemmas. The dataset is not vendored
# because its redistribution terms are not clear enough to commit into a repo;
# fetching it yourself keeps that decision where it belongs.
#
# Cite: Brysbaert, M., Warriner, A.B., & Kuperman, V. (2014). Concreteness
# ratings for 40 thousand generally known English word lemmas.
# Behavior Research Methods, 46, 904-911.
set -euo pipefail

DEST="${1:-grammar/lexicon/concreteness.txt}"
URL="https://raw.githubusercontent.com/ArtsEngine/concreteness/master/Concreteness_ratings_Brysbaert_et_al_BRM.txt"

mkdir -p "$(dirname "$DEST")"
curl -fsSL "$URL" -o "$DEST"
echo "wrote $DEST ($(wc -l < "$DEST") rows)"
echo "The compiler prefers this file automatically. Override with LAVC_CONCRETENESS_PATH."
