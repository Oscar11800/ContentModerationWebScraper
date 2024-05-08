import os
import json
import sys

def main():
    # directory to inject the manually extracted data
    data_directory = sys.argv[1] # './data/01_24_23_16_17'
    scrapes_directory =  None# 

    if len(sys.argv) > 2:
        specific_site = sys.argv[2]
    else:
        specific_site = ''

    area_keys = {'c': 'copyright', 'h': 'hatespeech', 'm': 'misinformation'}

    added_manual_scraped_pages = []
    for file in os.listdir(f"{scrapes_directory}"):
        if file.endswith('.txt') and specific_site in file:
            print(f'injecting {file}')
            with open(f"{scrapes_directory}/{file}", "r", encoding='utf-8') as f:
                text = f.readlines()
            
            area = area_keys[file.split('_')[0]]
            site = file.split('_')[1]
            page = int(file.split('_')[2].split('.')[0])

            with open(f"{data_directory}/all_text/{area}/{site}.json", 'r', encoding='utf-8') as f:
                all_text_json = json.load(f)

            # inject text from manual scrape into json!
            all_text_json['pages'][page]['text'] = text

            with open(f"{data_directory}/all_text/{area}/{site}.json", 'w') as f:
                json.dump(all_text_json, f)

            added_manual_scraped_pages.append(file + '\n')

    with open(f"{data_directory}/logs/manual_additions_note.txt", "w", encoding='utf-8') as f:
        f.writelines(['This directory has text from manual scrapings of text for the following pages:\n'])
        f.writelines(added_manual_scraped_pages)

if __name__ == '__main__':
    main()