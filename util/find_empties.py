'''
Script/function for finding empty scrapes. 

Argument parser throws error if necessary directory doesn't exist. 
'''

import os
import json
from argparsers import find_empties_parser as parser, ArgumentError

def success(page: dict) -> bool:
    '''
    Criterion for successful scrape. 
    Checks if there is at least one scraped passage and if search terms were
    found. 

    Args:
        page: dictionary containing structured scrape data

    Returns:
        bool: was the scrape a success?
    '''

    return (page['passages'] and 
            page['passages'][0]['terms'])

def find_empties(passages_path) -> list[tuple]:
    '''
    Find all empty scrapes in directory of refined scrape data. 
    Uses success() function to judge scrape

    Args:
        passages_path: path to refined data directory

    Returns:
        list: list of tuples, each containing information about a failed scrape
    '''

    old_dir = os.getcwd()
    os.chdir(passages_path)

    empties = []

    for area in os.listdir():
        if not os.path.isdir(area): continue

        for filename in os.listdir(area):
            if not filename.endswith('.json'): continue
            
            path = os.path.join(area, filename)
            with open(path, 'r') as f:
                pages = json.loads(f.read())['pages']
            
            for page in pages:
                if not success(page):
                    empties.append((filename.replace('.json', ''), 
                                    area, 
                                    page['page_id'], 
                                    page['source']))
    
    os.chdir(old_dir)

    print(f'Found {len(empties)} empties')
    return empties

if __name__ == "__main__":
    args = parser.parse_args()

    passages_path = os.path.join(args.datadir, 'passages')
    if not os.path.isdir(passages_path):
        raise ArgumentError('No passages directory')
    
    empties = find_empties(passages_path)

    with open(args.outfile, 'w+') as f:
        f.write(json.dumps(empties))

