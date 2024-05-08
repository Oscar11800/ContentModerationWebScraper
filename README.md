This repo contains code used to obtain data for our paper. 

The core program is the iterative scraper, a Selenium based tool for performant text data collection from the web. 
It supports filtered discovery of connected webpages in the webgraph, and is resistant to page-dynamicity and some anti-scraping methods. 
User provided seed links create access points to the web, and user provided search terms limit inclusion of irrelevant data. 
Users are able to configure scraper variables to adjust scrape quality, speed, etc. 

We have also written extractor and refiner scripts for extracting text from raw HTMLs and refining said text for purposes of coding, etc. 
These scripts are also customizable and can be run in sequence with the scraper using a provided bash script. 

Also included are supporting scripts for filling in missing data points both manually and automatically. This is typically needed due to rate-limiting on the web and 

# Iterative Scraper

## Input

The scraper requires as input: 
- A structured xlsx file of seed links to scrape. Search areas are organized sheet-wise, sites row-wise. 
- A csv file of search terms. Used to determine if discovered pages are relevant and should be included in the dataset.
- User specified options

To run the main iterative script, run

```
$ python main_iterative.py [links] [search_terms] [OPTIONS]
```

For more details about main_iterative.py positional arguments and options, run

```
$ python main_iterative.py --help
```

## Output

The `main_iterative.py` script outputs structured json files containing raw HTML data from scraped pages. 

In the specified data directory, the script creates a `all_htmls` folder. 

The json files are organized by site and search area as so:

`AREA_SITE_DATETIME.json`

For example:

`copyright_ebay_06_15_23_14_56.json`

The json files are structured by unique page as so:

```
{
site-id: id of the site (int)
site-name: name of the site (str)
site-url: url of the site (str)
pages: { 
        0: 
           url: url of the page/article (str)
           html: raw html from the url (str)
        1: ...
         ...
       }
}
```

For example:

```
{
site-id: 4
site-name: "twitter"
site-url: "https://www.twitter.com"
pages: { 
        0: 
           url: "https://help.twitter.com/en/rules-and-policies/crisis-misinformation"
           html: "<html lang\"en"\ dir=\"...></script></body></html>"
        1: 
           url: "https://help.twitter.com/en/rules-and-policies/medical-misinformation-policy"
           html: "<html lang\"en"\ dir=\"...></script></body></html>"
        2: 
           url: "https://help.twitter.com/en/rules-and-policies/france-false-information"
           html: "<html lang\"en"\ dir=\"...></script></body></html>"
       }
}
```

# Extractor

The extractor script pulls page text out of raw HTMLs into structured json files. 

## Input

The extractor requires as input: 
- A path to the data directory. It should contain an `all_htmls` folder containing scraper output.
- User specified options

To run the extractor script, run

```
$ python extractor.py [datadir] [OPTIONS]
```

For more details about extractor.py positional arguments and options, run

```
$ python extractor.py --help
```

## Output

The extractor.py script outputs folders of structured json files containing text extracted from raw scraped HTMLs. 

In the specified data directory, the script creates a `all_text` folder containing a folder for each search area. In each area folder, there are json files for each site

For example:

`copyright/ebay.json`

The json files are structured by unique page as so:

```
{
platform: platform, 
area: search term area, 
pages: [
        {
                page_id: page id,
                source: link from which page was scraped,
                text: list of text fragments extracted from page
        },
        ...
        ]
}
```

For example:

```
{
platform: 'instagram', 
area: 'copyright', 
pages: [
        {
                page_id: 10,
                source: 'www.instagram.com/copyright,
                text: [
                        'Instagram Copyright',
                        'Our policy\n',
                        ...
                ]
        },
        ...
        ]
}
```

# Refiner

The refiner reconstructs sentences from fragmented strings extracted from raw HTML. 

## Input

The refiner requires as input: 
- A path to the data directory. It should contain an `all_text` folder containing extractor output.
- A csv file of search terms. 
- User specified options

To run the extractor script, run:

```
$ python refiner.py [datadir] [search_terms] [OPTIONS]
```

For more details about refiner.py positional arguments and options, run:

```
$ python refiner.py --help
```

## Output

The refiner.py script outputs folders of structured json files containing refined sentences.  

In the specified data directory, the script creates a `passages` folder containing a folder for each search area. In each area folder, there are json files for each site. 

For example:

`copyright/ebay.json`

The json files are structured by unique page as so:

```
{
platform: platform, 
area: search term area, 
pages: [
        {
                page_id: page id,
                source: link from which page was scraped,
                passages: [
                        {
                        terms: list of found search terms, 
                        text: list of refined sentences
                        },
                        ...
                ]
        },
        ...
        ]
}
```

For example:

```
{
platform: 'instagram', 
area: 'copyright', 
pages: [
        {
                page_id: 10,
                source: 'www.instagram.com/copyright',
                passages: [
                        {
                        terms: ['copyright'], 
                        text: [
                                'This is our copyright policy for the instagram app.\n',
                                ...
                                ]
                        },
                        ...
                ]
        },
        ...
        ]
}
```

# Pipeline

We provide a bash script to run the scraper, extractor, and refiner in sequence. 

## Input

The pipeline script requires as input:
- path to xlsx file containing seed links
- path to csv file containing search terms
- user specified options

To run the pipeline script, run:

```
$ ./pipeline.sh -l [links] -t [search terms] [OPTIONS]
```

For more details about pipeline.sh positional arguments and options, run:

```
$ ./pipeline.sh -h
```

## Output

The pipeline script runs each of the three scripts in sequence, so the output is the exact same as if run manually. See above. 

# Fill

The fill script can be used for filling in missing data. 
Runs on pipeline output. 

Searches for individual missing pages (see find_empties) and then randomly scrapes them. Designed to overcome possible request throttling, etc. 

## Input

The fill script requires as input:
- path to directory containing all pipeline output

To run the fill script, run:

```
$ python util/fill.py [datadir]
```

For details about fill.py positional arguments and options, run:

```
$ python util/fill.py -h
```

# Output

No explicit output. Directly inserts data into json files in data directory. 
Can verify data filled using the find_empties script in the util folder. 

# Find Empties

The find_empties script allows json output of empties list used by fill script. 

Searches for bad data in refiner output and compiles a list. Running script in __main__ outputs this list to a json. 

Can also change the criteria for whether a datapoint is bad via the success() function. 

## Input

The find_empties script requires as input:
- path to directory containing all pipeline output
- filename to output json to

To run the find_empties script, run:

```
$ python util/find_empties.py [datadir] [outfile]
```

For details about fill.py positional arguments and options, run:

```
$ python util/find_empties.py -h
```

## Output

This script outputs a json file to the filename specified by the outfile argument. 

The json file may be loaded into a list. 

The json file is structured as so:

```
[
        (
                site, 
                area, 
                page_id, 
                source
        ), 
        ...
]
```

For example:

```
[
        (
                'instagram', 
                'copyright', 
                '10', 
                'www.instagram.com/copyright'
        ), 
        ...
]
```