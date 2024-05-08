'''
Argument parsers for iterative scraper, extractor, and refiner.

Import main_iterative_parser, extractor_parser, or refiner_parser to use. 

Example:
from argparsers import main_iterative_parser as parser
'''

from argparse import ArgumentParser, ArgumentError, ArgumentDefaultsHelpFormatter
import os

#
# =========================
# Path validation functions
# =========================
#

def __dir(dir_path):
    return os.path.abspath(dir_path)

def __file(file_path):
    if os.path.isfile(file_path): return os.path.abspath(file_path)
    
    raise ArgumentError(f'File not found: {file_path}')

#
# ====================================
# Argument parser for main_iterative.py
# ====================================
# 

main_iterative_parser = ArgumentParser(description='iterative web scraper', 
                                       formatter_class=ArgumentDefaultsHelpFormatter)

main_iterative_parser.add_argument('links', 
                                   type=__file, 
                                   help='xlsx file containing links for scraping')

main_iterative_parser.add_argument('search_terms', 
                                   type=__file,
                                   help='csv file containing search terms')

main_iterative_parser.add_argument('-d', '--outdir', 
                                   type=__dir, 
                                   help='output directory', 
                                   default='./data')

main_iterative_parser.add_argument('-p', '--pools', 
                                   type=int, 
                                   default=0, 
                                   help='number of multiprocessing pools (0 means no multiprocessing)')

main_iterative_parser.add_argument('-i', '--iterations', 
                                   type=int, 
                                   default=2, 
                                   help='iterations to scrape')

main_iterative_parser.add_argument('-s', '--sizecutoff', 
                                   type=int, 
                                   default=1000, 
                                   help='html size (number of characters) cutoff')

main_iterative_parser.add_argument('-r', '--retrycutoff', 
                                   type=int, 
                                   default=10, 
                                   help='retry number cutoff')
                                   
main_iterative_parser.add_argument('-c', '--webcache', 
                                   action='store_true', 
                                   help='use google webcaching when direct scraping fails past cutoff')

#
# ================================
# Argument parser for extractor.py
# ================================
# 

extractor_parser = ArgumentParser(description='text extractor', 
                                  formatter_class=ArgumentDefaultsHelpFormatter)

extractor_parser.add_argument('datadir', 
                              type=__dir, 
                              help='directory containing main_iterative output')

extractor_parser.add_argument('-p', '--pools', 
                              type=int, 
                              default=0, 
                              help='number of multiprocessing pools (0 means no multiprocessing)')


#
# ==============================
# Argument parser for refiner.py
# ==============================
# 

refiner_parser = ArgumentParser(description='text refiner', 
                                formatter_class=ArgumentDefaultsHelpFormatter)

refiner_parser.add_argument('datadir', 
                            type=__dir, 
                            help='directory containing extractor output')

refiner_parser.add_argument('search_terms', 
                            type=__file, 
                            help='csv file containing search terms')

refiner_parser.add_argument('-p', '--pools', 
                            type=int, 
                            default=0, 
                            help='number of multiprocessing pools (0 means no multiprocessing)')

refiner_parser.add_argument('-s', '--plusminus', 
                            type=int, 
                            default=5, 
                            help='sentences plus minus for refining', )

#
# =====================================
# Argument parser for to_coding_txts.py
# =====================================
# 

to_coding_txts_parser = ArgumentParser(description='create coding texts from refined output', 
                                       formatter_class=ArgumentDefaultsHelpFormatter)

to_coding_txts_parser.add_argument('datadir', 
                                   type=__dir, 
                                   help='directory containing refiner output')

to_coding_txts_parser.add_argument('-p', '--pools', 
                                   type=int, 
                                   default=0, 
                                   help='number of multiprocessing pools (0 means no multiprocessing)')

#
# ===========================
# Argument parser for fill.py
# ===========================
# 

fill_parser = ArgumentParser(description='fill in failed scrapes', 
                             formatter_class=ArgumentDefaultsHelpFormatter)

fill_parser.add_argument('datadir', 
                         type=__dir, 
                         help='directory containing all outputs')

#
# ==============================
# Argument parser for find_empties.py
# ==============================
# 

find_empties_parser = ArgumentParser(description='find failed scrapes', 
                                     formatter_class=ArgumentDefaultsHelpFormatter)

find_empties_parser.add_argument('datadir', 
                                 type=__dir, 
                                 help='directory containing all outputs')

find_empties_parser.add_argument('outfile', 
                                 type=str, 
                                 help='file to write list of empty scrapes to')