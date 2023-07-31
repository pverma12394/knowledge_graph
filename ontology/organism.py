import sys
sys.path.append("/Users/pawan/Documents/Elucidata/Knowledge_Graphs/biomedical_ontology/biomedical_ontologies_kg/")
from dotenv import load_dotenv
import json
import requests
import pandas as pd
import tqdm
from scripts.create_db import save_to_db, add_node_table_name

load_dotenv()

def post_request(term): 
    
    api_endpoint = "http://data.bioontology.org"
    endpoint='search'
    method = 'POST'

    API_KEY = "d602cd7d-35df-4310-a35a-8c271c1a2f47"

    kwargs = {
        'url': api_endpoint+"/"+endpoint+"/?q="+term+"&ontologies=NCBITAXON&require_exact_match=true",
        'method': method,
        'headers': {
            'Authorization': 'apikey token='+API_KEY
        }
    }

    resp = requests.request(**kwargs)

    if int(resp.status_code)!=200:
        print(resp.text)
    
    if resp.text:
        resp_dict = json.loads(resp.text)
        
    return resp_dict

def get_synonyms(resp_dict, term):
    
    syns = []
    identifier = ''
    str_to_skip = ':'

    for x in resp_dict['collection']:
        if x['prefLabel'].lower() == term.lower():
            identifier = f"NCBITAXON:"+str(x['@id'].split('/')[-1])

            if 'synonym' in x: 
                s = x.get('synonym', [])
                if not any([str_to_skip.lower() in word.lower() for word in s]):
                    syns = ';'.join(s)
                else:
                    syns = ''
        else:
            continue
    
    return identifier, syns

def organsims():

    organsim_names_df = pd.read_csv('ontologies/organisms.csv', sep = ',')
    terms = organsim_names_df['terms']
    organsim_terms = []
    synonyms = []
    ids = []
    type_entity = []

    for term in tqdm.tqdm(terms):

        resp_dict = post_request(term)
        id, s = get_synonyms(resp_dict, term)
        if id:
            organsim_terms.append(term)
            ids.append(id)
            if not s:
                synonyms.append(''.join(s))
            else:
                synonyms.append(s)
            type_entity.append('organism')
        else:
            continue


    organsim_df = pd.DataFrame(list(zip(ids, organsim_terms, synonyms, type_entity)), columns=['organism_id', 'name', 'synonyms', 'type'])
    organsim_df.to_csv('ontologies/organism_syn.csv')

    add_node_table_name(['organism__nodes','organism',';'.join(organsim_df.columns),'not_mapped'])
    save_to_db(organsim_df, "organism__nodes")

if __name__ == "__main__":

    organsims()

    