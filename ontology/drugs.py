import sys
sys.path.append("/Users/pawan/Documents/Elucidata/Knowledge_Graphs/biomedical_ontology/biomedical_ontologies_kg/")
import pandas as pd
import tqdm
import requests
from dotenv import load_dotenv
import json
from scripts.create_db import save_to_db,read_from_db,add_node_table_name,add_table_name

load_dotenv()
def drug_node():
    with open("ontologies/pubchem_onto_upper.json") as f:
        data = json.load(f)

    dct = {
        "drug_id" :[],
        "name" :[],
        "synonyms" :[]
    }

    for drug in data:
        dct['drug_id'].append(drug['id'])
        dct['name'].append(drug['name'])
        syn = ';'.join(drug['synonym'])
        dct['synonyms'].append(syn)

    drug__nodes = pd.DataFrame(dct)
    chebi_id = pd.read_csv('ontologies/drug_chebi_ids.tsv',sep='\t',names=['drug_id','chebi_id'])
    chembl_id = pd.read_csv('ontologies/drug_chembl_ids.tsv',sep='\t',names=['drug_id','chembl_id'])
    drug__nodes = pd.merge(drug__nodes,chebi_id,on='drug_id',how='left')
    drug__nodes = pd.merge(drug__nodes,chembl_id,on='drug_id',how='left')
    drug__nodes= drug__nodes.fillna('0')

    polly_drugs = pd.read_csv("ontologies/drugs_on_polly.csv")
    polly_drugs = list(polly_drugs['curated_drugs'])

    def filter_rows(row):
        if row['name'].lower() in polly_drugs:
            return 1
        else:
            syns = list(map(lambda x: x.lower(),row['synonyms'].split(';')))
            inter = set(polly_drugs).intersection(set(syns))
            if len(inter) == 0:
                return 0
            else:
                return 1

    drug__nodes['matched'] = drug__nodes.apply(filter_rows,axis=1)
    drug__nodes.to_csv("ontologies/drug__nodes.csv",index=False)
    df = pd.read_csv("ontologies/drug__nodes.csv")
    final_df = df[df['matched']==1]
    final_df.drop(columns=['matched'],inplace=True)

    save_to_db(final_df,"drug__nodes")
    add_node_table_name(["drug__nodes",'drug',';'.join(final_df.columns),'not_mapped'])

def up_drug_gene():
    final_df = pd.read_csv('ontologies/drug_upregulates_gene.csv')
    final_df['relation'] = 'drug_upregulates'

    genes = read_from_db("gene__nodes")
    final_df['gene_target'] = final_df['gene_target'].str.upper()
    final_df = pd.merge(final_df, genes[['gene_id','gene_symbol']], left_on='gene_target', right_on='gene_symbol')[['gene_id','drug_id']]
    
    print(final_df.head())
    add_table_name(["drug__upregulates__gene",'drug','gene','drug_upregulates','not_mapped'])
    save_to_db(final_df, "drug__upregulates__gene")

def down_drug_gene():
    final_df = pd.read_csv('ontologies/drug_downregulates_gene.csv')
    final_df['relation'] = 'drug_downregulates'

    genes = read_from_db("gene__nodes")
    final_df['gene_target'] = final_df['gene_target'].str.upper()
    final_df = pd.merge(final_df, genes[['gene_id','gene_symbol']], left_on='gene_target', right_on='gene_symbol')[['gene_id','drug_id']]
    
    print(final_df.head())
    add_table_name(["drug__downregulates__gene",'drug','gene','drug_downregulates','not_mapped'])
    save_to_db(final_df, "drug__downregulates__gene")
    
def get_drug_gene_interaction():
    """Get all synonyms of a compound using the RDF rest api
    Args:
        compound_id : compound id
    Returns:
        Tuple: (GeneIDs,PubmedIDs)
    """

    drugs_df = read_from_db("drug__nodes")
    compound_id = list(drugs_df['drug_id'])
    c = ['1117','24524','10461508']
    gene_ids = []
    #pmids = []
    for id in tqdm.tqdm(compound_id): 
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{str(id)}/xrefs/GeneID,PubMedID/JSON"
        response = requests.get(url)
        #print(response.status_code)
        if response.status_code >= 202:
            continue
            #return ('None','None')

        response_json = response.json()
        if 'GeneID' in response_json['InformationList']['Information'][0].keys():
            gids = response_json['InformationList']['Information'][0]['GeneID']
            if len(gids) > 0:
                gene_ids.append(gids)
            else:
                gene_ids.append(['None'])

        #if 'PubMedID' in response_json['InformationList']['Information'][0].keys():
        #    pids = response_json['InformationList']['Information'][0]['PubMedID']
        #    if len(pids) > 0:
        #        pmids.append(pids)
        #    else:
        #        pmids.append(['None'])

    interactions_df = pd.DataFrame(list(zip(compound_id, gene_ids)), columns=['drug_id','gene_id'])
    interactions_df = interactions_df.explode('gene_id')
    interactions_df = interactions_df.dropna(subset='gene_id')
    interactions_df = interactions_df.drop_duplicates()

    # Map entrez IDs to HGNC IDs
    hgnc_gene = read_from_db("gene__nodes")
    gene = hgnc_gene[['gene_id', 'entrez_id']]
    gene.columns = ['hgnc_id','entrez_id']
    interactions_df = pd.merge(interactions_df, gene, left_on='gene_id', right_on='entrez_id', how='inner')
    interactions_df =interactions_df[['drug_id', 'hgnc_id']]
    
    interactions_df.columns = ['drug_source', 'gene_target']
    interactions_df['relation'] = 'interacts_with'
    add_table_name(["drug__interacts_with__relation",'drug','gene','interacts_with','not_mapped'])
    save_to_db(interactions_df,"drug__interacts_with__relation")
    
def get_3d_similar_drugs():
    """Get all synonyms of a compound using the PUG rest api
    Args:
        compound_id : compound id
    Returns:
        List: [CompoundIDs]
    """

    drugs_df = read_from_db("drug__nodes")
    compound_id = list(drugs_df['drug_id'])
    c = ['2244','5282452','10461508']
    analog_ids = []
    for id in tqdm.tqdm(compound_id): 
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/fastsimilarity_3d/cid/{str(id)}/cids/JSON"
        response = requests.get(url)
        #print(response.status_code)
        if response.status_code >= 202:
            continue
            #return ('None','None')

        response_json = response.json()
        if 'CID' in response_json['IdentifierList'].keys():
            cids = response_json['IdentifierList']['CID']
            if int(id) in cids:
                cids.remove(int(id))
            analog_ids.append(cids)
        else:
            analog_ids.append(None)

    interactions_df = pd.DataFrame(list(zip(compound_id, analog_ids)), columns=['drug_id','similar_drug_id'])
    interactions_df = interactions_df.dropna(subset=['similar_drug_id'])
    interactions_df = interactions_df.explode('similar_drug_id')
    interactions_df.columns = ['drug_source', 'drug_target']
    interactions_df = pd.merge(interactions_df, drugs_df[['drug_id']], left_on='drug_target', right_on='drug_id', how='inner')
    interactions_df = interactions_df.drop_duplicates()
    interactions_df.drop('drug_id', axis=1, inplace=True)

    interactions_df['relation'] = 'has_similar_structure'
    add_table_name(["drug__has_similar_structure__relation",'drug','drug','has_similar_structure','not_mapped'])
    save_to_db(interactions_df,"drug__has_similar_structure__relation")
    
def main_drug():
    #drug_node()
    #down_drug_gene()
    #up_drug_gene()
    #get_drug_gene_interaction()
    get_3d_similar_drugs()

if __name__ == '__main__':
    main_drug()



