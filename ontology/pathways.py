import pandas as pd
from scripts.create_db import save_to_db,read_from_db, add_node_table_name,add_table_name

def pathway_nodes():

    pathways = pd.read_csv("ontologies/pathway_nodes.csv")

    def find_ontology(row):
        temp = row.split('_')[0]
        if temp == 'GOMF':
            return 'Molecular Function'
        elif temp == 'GOCC':
            return 'Cellular Component'
        elif temp == 'GOBP':
            return 'Biological Process'
        elif temp == 'HP':
            return 'Human Phenotype'
        
    pathways['ontology'] = pathways['pathway'].apply(find_ontology)
    pathways['name'] = pathways['pathway'].apply(lambda x: ' '.join(x.split('_')[1:]).capitalize())
    pathways.drop(columns=['Unnamed: 0','pathway'],inplace=True)

    pathways = pathways.rename(columns={"pathway_sys_name":"synonyms"})

    # pathways.to_csv("ontologies/present_pathways.csv",index=False)

    save_to_db(pathways,"pathway__nodes")
    add_node_table_name(["pathway__nodes",'pathway',';'.join(pathways.columns),'not_mapped'])

def pathway_dis_rel():

    dis_pathway = pd.read_csv("ontologies/pathway_disease_mapping.csv")
    dis_pathway.drop(columns=['Unnamed: 0'],inplace=True)

    save_to_db(dis_pathway,"pathway__enriched_in__relation")
    add_table_name(["pathway__enriched_in__relation",'pathway','disease','enriched_in','not_mapped'])

def main_pathway():
    pathway_nodes()
    pathway_dis_rel()

if __name__ == '__main__':
    main_pathway()