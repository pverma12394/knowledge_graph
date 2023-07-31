import sys
sys.path.append("/Users/pawan/Documents/Elucidata/Knowledge_Graphs/biomedical_ontology/biomedical_ontologies_kg/")
import pandas as pd
from dotenv import load_dotenv
from scripts.create_db import save_to_db,read_from_db,add_table_name

load_dotenv()
def main_gene_pathway():
    """
    gobp = pd.read_csv('gobp.csv')
    gocc = pd.read_csv('gocc.csv')
    gomf = pd.read_csv('gomf.csv')
    hpo = pd.read_csv('hpo.csv')

    final = pd.DataFrame()

    for types in [gobp, gocc, gomf, hpo]:    
        temp = types[["gs_exact_source","gene_symbol","gs_subcat"]]
        temp = temp.drop_duplicates().reset_index(drop=True)
        print(temp.head())
        final = pd.concat([final, temp])

    final.rename(columns={'gs_exact_source':'pathway_id'}).to_csv("pathway_gene_map.csv")
    """
    final_df = pd.read_csv('ontologies/pathway_gene_map.csv')
    final_df['relation'] = 'associated_with'
    genes = read_from_db("gene__nodes")
    pathway = read_from_db("pathway__nodes")
    final_df = pd.merge(final_df, genes[['gene_id','gene_symbol']], on='gene_symbol')[['gene_id','pathway_id','relation']]
    
    add_table_name(["gene__associated_with__relation",'gene','pathway','associated_with','not_mapped'])
    save_to_db(final_df, "gene__associated_with__relation")

# main
if __name__ == '__main__':
    main_gene_pathway()