"""
Argument parsers for the JSON‑driven scraper pipeline.

Import the objects you need, e.g.:
    from util.argparsers import main_iterative_parser as parser
"""
from argparse import ArgumentParser, ArgumentError, ArgumentDefaultsHelpFormatter
import os

# ---------- helper validators ----------

def _dir(path: str) -> str:
    """Return absolute path for a directory (creates if missing)."""
    return os.path.abspath(path)


def _file(path: str) -> str:
    if os.path.isfile(path):
        return os.path.abspath(path)
    raise ArgumentError(None, f"File not found: {path}")

# ---------------------------------------------------------------------------
# MAIN‑ITERATIVE  (scraper)
# ---------------------------------------------------------------------------

main_iterative_parser = ArgumentParser(
    description="iterative web scraper (JSON config driven)",
    formatter_class=ArgumentDefaultsHelpFormatter,
)

main_iterative_parser.add_argument(
    "--config", required=True, type=_file,
    help="JSON file containing site configurations (site_configs.json)",
)
main_iterative_parser.add_argument(
    "--site", required=True, type=str,
    help="Key inside the JSON identifying which site to scrape",
)
main_iterative_parser.add_argument(
    "--search_terms", required=True, type=_file,
    help="CSV file of search terms",
)

# optional knobs
main_iterative_parser.add_argument("-d", "--outdir", type=_dir, default="./data", help="output directory")
main_iterative_parser.add_argument("-p", "--pools", type=int, default=0, help="multiprocessing pools (0=off)")
main_iterative_parser.add_argument("-i", "--iterations", type=int, default=2, help="scraper tree depth")
main_iterative_parser.add_argument("-s", "--size_cutoff", type=int, default=1000, help="HTML size cutoff")
main_iterative_parser.add_argument("-r", "--retry_cutoff", type=int, default=10, help="retry attempts per link")
main_iterative_parser.add_argument("-c", "--webcache", action="store_true", help="use Google WebCache fallback")

# ---------------------------------------------------------------------------
# EXTRACTOR  (html ➜ raw text)
# ---------------------------------------------------------------------------

extractor_parser = ArgumentParser(description="text extractor", formatter_class=ArgumentDefaultsHelpFormatter)
extractor_parser.add_argument("datadir", type=_dir, help="directory containing main_iterative output")
extractor_parser.add_argument("-p", "--pools", type=int, default=0, help="multiprocessing pools (0=off)")

# ---------------------------------------------------------------------------
# REFINER  (raw text ➜ refined chunks)
# ---------------------------------------------------------------------------

refiner_parser = ArgumentParser(description="text refiner", formatter_class=ArgumentDefaultsHelpFormatter)
refiner_parser.add_argument("datadir", type=_dir, help="directory containing extractor output")
refiner_parser.add_argument("search_terms", type=_file, help="CSV of search terms")
refiner_parser.add_argument("-p", "--pools", type=int, default=0, help="multiprocessing pools (0=off)")
refiner_parser.add_argument("-s", "--plusminus", type=int, default=5, help="± sentences window")

# ---------------------------------------------------------------------------
# Remaining utility parsers
# ---------------------------------------------------------------------------

to_coding_txts_parser = ArgumentParser(description="create coding texts from refined output", formatter_class=ArgumentDefaultsHelpFormatter)
to_coding_txts_parser.add_argument("datadir", type=_dir, help="directory containing refiner output")
to_coding_txts_parser.add_argument("-p", "--pools", type=int, default=0, help="multiprocessing pools (0=off)")

fill_parser = ArgumentParser(description="fill in failed scrapes", formatter_class=ArgumentDefaultsHelpFormatter)
fill_parser.add_argument("datadir", type=_dir, help="directory containing all outputs")

find_empties_parser = ArgumentParser(description="find failed scrapes", formatter_class=ArgumentDefaultsHelpFormatter)
find_empties_parser.add_argument("datadir", type=_dir, help="directory containing all outputs")
find_empties_parser.add_argument("outfile", type=str, help="file to write list of empty scrapes to")