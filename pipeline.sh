#!/usr/bin/env bash
set -euo pipefail

usage="\n$(basename "$0") -c <site_configs.json> -s <site_key> -t <search_terms.csv> [options]\n\nOptions:\n  -o <dir>    Output directory (default ./data)\n  -p <n>      Pools for multiprocessing (default 0)\n  -i <depth>  Scraper tree depth (default 2)\n  -r <n>      Retry cutoff per link (default 10)\n  -m <n>      ± sentence window for extractor (default 5)\n  -s <bool>   Use Google web‑cache fallback (flag)\n  -h          Show this help\n"

# ---------- defaults ----------
config=""       # site_configs.json
site=""         # key inside JSON
search_terms="" # csv
outdir="./data"
pools=0
iterations=2
retry_cutoff=10
plusminus=5
size_cutoff=1000
webcache=false

# ---------- parse ----------
while getopts ":hc:s:t:o:p:i:r:m:w" flag; do
  case $flag in
    h) printf "%s" "$usage" && exit 0;;
    c) config=$OPTARG;;
    s) site=$OPTARG;;
    t) search_terms=$OPTARG;;
    o) outdir=$OPTARG;;
    p) pools=$OPTARG;;
    i) iterations=$OPTARG;;
    r) retry_cutoff=$OPTARG;;
    m) plusminus=$OPTARG;;
    w) webcache=true;;
    :) printf "missing value for -%s\n" "$OPTARG" >&2; exit 1;;
    *) printf "unknown option -%s\n" "$OPTARG" >&2; exit 1;;
  esac
done

# ---------- validation ----------
[[ -f $config       ]] || { echo "config file not found: $config" >&2; exit 1; }
[[ -n $site         ]] || { echo "--site (-s) required" >&2;          exit 1; }
[[ -f $search_terms ]] || { echo "search_terms csv not found" >&2;     exit 1; }

# ---------- echo ----------
cat <<EOF
Config file      : $config
Site key         : $site
Search terms CSV : $search_terms
Output directory : $outdir
Pools            : $pools
Depth            : $iterations
Retry cutoff     : $retry_cutoff
± sentences      : $plusminus
Use web‑cache    : $webcache
EOF

echo "\n========== Main Iterative =========="
main_args=(--config "$config" --site "$site" --search_terms "$search_terms" \
          -d "$outdir" -p "$pools" -i "$iterations" -s "$size_cutoff" -r "$retry_cutoff")
$webcache && main_args+=( -c )

python3 main_iterative.py "${main_args[@]}"

# newest run dir
run_dir=$(ls -td "$outdir"/*/ | head -n1 | sed 's:/*$::')
[[ -d $run_dir/all_htmls ]] || { echo "no run folder with all_htmls found" >&2; exit 1; }

echo -e "\nUsing run directory: $run_dir"

echo "\n========== Extractor =========="
python3 extractor.py "$run_dir" -p "$pools"

echo "\n========== Refiner =========="
python3 refiner.py "$run_dir" "$search_terms" -p "$pools" -s "$plusminus"

echo -e "\nPipeline done.\n"