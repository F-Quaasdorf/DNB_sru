import requests
import unicodedata
from lxml import etree
from bs4 import BeautifulSoup as soup
import pandas as pd

# Builds the SRU-string and returns the fetched records
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
    first_request = True
    
    while True:
        params.update({'startRecord': i})
        req = requests.get(base_url, params=params)
        
        # Prints SRU-URL
        if first_request:
            print(req.url)
            first_request = False
        
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
    
    return records

# Parses the records and returns a dictionary of the fetched fields and elements (e.g. publication year)
def parse_record(record):
    ns = {"marc": "http://www.loc.gov/MARC21/slim"}
    xml = etree.fromstring(unicodedata.normalize("NFC", str(record)))
    
    # Returns the first element of a field
    def extract_text(xpath_query):
        elements = xml.xpath(xpath_query, namespaces=ns)
        return elements[0].text if elements else 'N.N.'
    
    # Returns multiple elements from a field as a list (e.g. places of publication)    
    def multi_extract_text(xpath_query):
        return [elem.text for elem in xml.xpath(xpath_query, namespaces=ns)] or ["N.N."]
    
    meta_dict = {
        "IDN": extract_text("marc:controlfield[@tag='001']"),
        "Titel": extract_text("marc:datafield[@tag='245']/marc:subfield[@code='a']"),
        "Verfasser": extract_text("marc:datafield[@tag='100']/marc:subfield[@code='a']"),
        "Ort": multi_extract_text("marc:datafield[@tag='264']/marc:subfield[@code='a']"),
        "Jahr": extract_text("marc:datafield[@tag='264']/marc:subfield[@code='c']"),
        "Sprache": extract_text("marc:datafield[@tag='041']/marc:subfield[@code='a']")
    }

    return meta_dict

def to_df(records):
    return pd.DataFrame(records)

# Put the query here, e.g. 'tit' for title, 'jhr' for publication year, 'isbn' for, well, the ISBN
# Concatenate different search terms with 'and'
records = dnb_sru("tit=kursachsen und das ende") 

# Parses the records
parsed_records = [parse_record(record) for record in records]
df = to_df(parsed_records)

pd.set_option('display.max_columns', None)
print(df)
