import os
from multiprocessing import Process, Manager, Pool, freeze_support
import json
import pprint
from util.argparsers import to_coding_txts_parser as parser

def make_passage_txts(json_path, output_dir_specific):
    print(f'working on {json_path}: making txts for coding')
    with open(json_path, 'rb') as f:
        passages_json = json.load(f)

    for page in passages_json['pages']:
        output_file = f"{output_dir_specific}/{page['page_id']}.txt"
        text_lines = [f'{passages_json["platform"]}\n', f'{passages_json["area"]}\n']
        text_lines.append(f"Page ID: {page['page_id']}\n")
        text_lines.append(f"Source: {page['source']}\n")
        for passage in page['passages']:
            if passage['terms']:
                text_lines.append(pprint.pformat(passage['terms'])+'\n')
                text_lines.extend(passage['text'])
                text_lines.append('\n')
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.writelines(text_lines)

def main(datadir, pools):
    if pools:
        pool = Pool(pools)

    try:
        os.mkdir(f"{datadir}/coding_txts/")
    except FileExistsError as e:
        pass
    try:
        os.mkdir(f"{datadir}/logs/coding_txts/")
    except FileExistsError as e:
        pass

    for area in ['copyright', 'hatespeech', 'misinformation']:
        try: 
            output_dir = f"{datadir}/coding_txts/{area}"
            os.mkdir(f"{output_dir}")
        except FileExistsError as e:
            pass

        for platform in os.listdir(f"{datadir}/passages/{area}"):
            json_path = f"{datadir}/passages/{area}/{platform}"
            try: 
                output_dir_specific = f"{datadir}/coding_txts/{area}/{platform.split('.')[0]}/"
                os.mkdir(f"{output_dir_specific}")
            except FileExistsError as e:
                pass           
            if pools:
                pool.apply_async(make_passage_txts, args=(json_path, output_dir_specific), error_callback=pcb)
            else:
                make_passage_txts(json_path, output_dir_specific)

    if pools:
        pool.close()
        pool.join()

def pcb(res):
    print(f'One of the jobs errored: {res}')

if __name__ == '__main__':
    args = parser.parse_args()

    main(**vars(args))
