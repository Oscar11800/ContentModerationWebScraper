#!/bin/bash

usage="
$(basename $0)  -l -t [-o] [-p] [-i] [-s] [-r] [-m] [-c]

script to run full pipeline: main_iterative.py, extractor.py, refiner.py. 

arguments:
  -l
    path to excel file containing links
  -t  
    path to csv file containing search terms 

options:
  -h  
      show this help message and exit
  -o  
      output directory
      default=./data
  -p  
      number of pools for multiprocessing
      default=0 (no multiprocessing)
  -i  
      scraper iteration depth
      default=2
  -s
      scraper HTML size cutoff
      default=1000
  -r
      scraper retry cutoff
      default=10
  -m
      extractor sentences plus minus
      default=5
  -c
      use google webcaching when direct scrape fails past cutoff (toggle true)
"

#
#
# Parse arguments using getopts
#
#

links=''
search_terms=''
outdir='./data'
pools=0
iterations=2
size_cutoff=1000
retry_cutoff=10
plusminus=5
webcache=false

while getopts "hl:t:o:p:i:s:r:m:c" flag; do
    case $flag in
        h) printf "$usage"; exit;;
        l) links=$OPTARG;;
        t) search_terms=$OPTARG;;
        o) outdir=$OPTARG;;
        p) pools=$OPTARG;;
        i) iterations=$OPTARG;;
        s) size_cutoff=$OPTARG;;
        r) retry_cutoff=$OPTARG;;
        m) plusminus=$OPTARG;;
        c) webcache=true;;
    esac
done

#
#
# Validate arguments
#
#

if [ -z "$links" ]; then
  printf "error: missing required argument -- l " >&2
  exit 1
fi

if ! test -f $links; then
  printf "error: file '$links' does not exist " >&2
  exit 1
fi

if [ -z "$search_terms" ]; then
  printf "error: missing required argument -- t " >&2
  exit 1
fi

if ! test -f $search_terms; then
  printf "error: file '$search_terms' does not exist " >&2
  exit 1
fi

#
#
# Echo pipeline arguments
#
#

printf "
Links: $links
Search terms: $search_terms
Output directory: $outdir
Pools: $pools
Iterations: $iterations
HTML size cutoff: $size_cutoff
Retry cutoff: $retry_cutoff
Sentences plus minus: $plusminus
Use webcache: $webcache

Running pipeline..."


#
#
# Main Iterative
#
#

printf "

==========Main Iterative==========

"

if [ $webcache = true ]; then
    python3 main_iterative.py $links $search_terms -d $outdir -p $pools -i $iterations -s $size_cutoff -r $retry_cutoff -c
else
    python3 main_iterative.py $links $search_terms -d $outdir -p $pools -i $iterations -s $size_cutoff -r $retry_cutoff
fi

#
#
# Extractor
#
#

printf "

==========Extractor==========

"


python3 extractor.py $outdir -p $pools

#
#
# Refiner
#
#

printf "

==========Refiner==========

"


python3 refiner.py $outdir $search_terms -p $pools -s $plusminus

#
#
# Done
#
#

printf "

Pipeline done. 

"
