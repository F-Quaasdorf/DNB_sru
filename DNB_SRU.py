import requests
import unicodedata
from lxml import etree
from bs4 import BeautifulSoup as soup
import pandas as pd

def dnb_sru(query):
    base_url = "https://services.dnb.de/sru/dnb"
    params = {
        'recordSchema': 'MARC21-xml',
        'operation': 'searchRetrieve',
        'version': '1.1',
        'maximumRecords': '100',
        'query': query
    }
    
    records = []
    i = 1
    while True:
        params.update({'startRecord': i})
        req = requests.get(base_url, params=params)
        
        if req.status_code != 200:
            print(f"Error: Failed to fetch records. Status code {req.status_code}")
            break

        xml = soup(req.content, features="xml")
        new_records = xml.find_all('record', {'type': 'Bibliographic'})
        
        if not new_records:
            break
        
        records.extend(new_records)
        if len(new_records) < 100:
            break
        
        i += 100
    print(req.url)
    return records

def parse_record(record):
    ns = {"marc": "http://www.loc.gov/MARC21/slim"}
    xml = etree.fromstring(unicodedata.normalize("NFC", str(record)))

    def extract_text(xpath_query):
        elements = xml.xpath(xpath_query, namespaces=ns)
        return elements[0].text if elements else 'N.N.'
        
    def multi_extract_text(xpath_query):
        return [elem.text for elem in xml.xpath(xpath_query, namespaces=ns)] or ["N.N."]

    idn = extract_text("marc:controlfield[@tag='001']")
    title = extract_text("marc:datafield[@tag='245']/marc:subfield[@code='a']")
    author = extract_text("marc:datafield[@tag='100']/marc:subfield[@code='a']")
    ort = multi_extract_text("marc:datafield[@tag='264']/marc:subfield[@code='a']")
    jahr = extract_text("marc:datafield[@tag='264']/marc:subfield[@code='c']")
    sprache = extract_text("marc:datafield[@tag='041']/marc:subfield[@code='a']")

    meta_dict = {
        "IDN": idn,
        "Titel": title,
        "Verfasser": author,
        "Ort": ort,
        "Jahr": jahr,
        "Sprache": sprache
    }

    return meta_dict

def to_df(records):
    return pd.DataFrame(records)


records = dnb_sru("tit=Kursachsen und das Ende")
parsed_records = [parse_record(record) for record in records]
df = to_df(parsed_records)

pd.set_option('display.max_columns', None)
print(df)
