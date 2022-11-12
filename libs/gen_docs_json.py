import json
import re
from loguru import logger

from helper import project_dir, CleanDoc


def gen_text(doc: str, rule_block: bool = False) -> str:
    if key := re.search('^#+\s*%{(.*?)}', doc):
        if rule_block:
            doc = doc.replace(key.group(), f'**{mapped_translations[key.groups()[0]]}**')
        else:
            doc = doc.replace(key.group(), f'{mapped_translations[key.groups()[0]]}')
    elif key := re.search('\*\*%{(.*?)}\*\*', doc):
        doc = doc.replace(key.group(), f'**{mapped_translations[key.groups()[0]]}**')
    elif key := re.search('^%{(.*?)}', doc):
        mkey = key.groups()[0]
        doc = doc.replace(key.group(), f'{mapped_translations[mkey]}')
    elif key := re.search('%{(.*?)}', doc):
        mkey = key.groups()[0]
        doc = doc.replace(key.group(), f'**{mapped_translations[mkey]}**')
    else:
        return doc
    return gen_text(doc)


# logger.debug("Get Translations from gametools")
# translations = requests.get("https://api.gametools.network/bf2042/translations/").json()['localizedTexts']

with open(project_dir / "data" / "translations.json") as file:
    translations = json.load(file)['localizedTexts']

mapped_translations = dict()

logger.debug("Generate Mapping")
for item in translations:
    mapped_translations[item['sid']] = item['localizedText']


logger.info("Generate Docs")
clean_names = []

for raw_doc in sorted((project_dir / "data" / "raw_docs").glob("*.md")):
    bad_blocks = ['controls_if_else', 'missingActionBlockType_v1', 'missingValueBlockType_v1']
    with open(raw_doc) as file:
        data = [
            key
            for key in re.sub('```.*```', '', file.read().strip(), flags=re.DOTALL).strip().split("\n") if key != ''
        ]
        if not len(data):
            continue

    if raw_doc.stem == "ruleBlock":
        clean = [gen_text(data[0])]
        for index, line in enumerate(data[1:]):
            if index == 0:
                clean.append(gen_text(line, rule_block=True).split('\n')[0])
            else:
                clean.append(gen_text(line, rule_block=True))
    else:
        clean = [gen_text(line) for line in data]

    i = False
    o = False
    if 'Inputs' in clean:
        i = clean.index('Inputs')
    if 'Output' in clean:
        o = clean.index('Output')

    clean_doc: CleanDoc = dict()
    if raw_doc.stem == "subroutineInstanceBlock":
        clean_doc['block'] = "subroutineInstanceBlock"
    else:
        clean_doc['block'] = clean[0]

    clean_doc['summary'] = "\n".join(clean[1:(i if i else o if o else None)])
    if i:
        clean_doc['inputs'] = clean[i+1:(o if o else None)]
    if o:
        clean_doc['output'] = clean[o+1:]

    k = f"ID_ARRIVAL_BLOCK_{raw_doc.stem.upper()}"
    clean_name = mapped_translations.get(k, False)
    if clean_name == "VehicleTypes":
        clean_name = "VehicleTypesItem"
    elif not clean_name:
        if raw_doc.stem == "controls_if_if":
            clean_name = "Control_If"
        else:
            clean_name = clean_doc['block'].replace(' ', '').replace('#', '')

    if clean_name in ["RULE", "MOD"]:
        clean_name = clean_name.capitalize()

    doc_json_folder_path = project_dir / "docs_json"
    doc_json_folder_path.mkdir(exist_ok=True)
    doc_json_file_path = doc_json_folder_path / f'{clean_name}.json'
    doc_json_file_path.touch(exist_ok=True)

    with open(doc_json_file_path, 'r+') as file:
        try:
            doc_json: CleanDoc = json.loads(file.read())
        except json.JSONDecodeError:
            doc_json = dict()
        doc_json.update(clean_doc)
        if not doc_json.get('extra', False):
            doc_json['extra'] = ''
        file.seek(0)
        json.dump(doc_json, file, indent=4)
        file.truncate()

    clean_names.append(clean_name)
    logger.debug(f"{raw_doc.stem} -> {clean_name}")

with open(project_dir / "data" / "clean_names", 'w') as file:
    json.dump(clean_names, file)
logger.info("Gen docs complete")
