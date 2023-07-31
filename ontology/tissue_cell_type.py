import pronto
import pandas as pd
from scripts.create_db import read_from_db, save_to_db, add_table_name, add_node_table_name
from scripts.load import load_file

"""
Plan
1. Load obo data from ontology page
2. Refactor and update the code to save data in mysql
3. Add code to check if the obo data are updated 
4. Update obda mapping data depending on the file update
"""



# region tissue and cell type ontology

def get_type_terms(bto, name):
    return [i for i in bto.terms() if name in list(i.subsets)[0]]


def fetch_node_properties(ontology_term, id_column_name):
    def joined_description(_terms):
        return ";".join([i.description for i in _terms.synonyms])

    bto_df = pd.DataFrame([(i.id, i.name, i.definition, joined_description(i)) for i in ontology_term],
                          columns=[f"{id_column_name}_id", 'name', 'definition', 'synonyms'])
    # print(bto_df.shape)
    # save bto_df to sql data
    if id_column_name == 'cell_type':
        bto_df['type'] = 'cell-type'
    else:
        bto_df['type'] = 'tissue'
    add_node_table_name([f"{id_column_name}__nodes",id_column_name,';'.join(bto_df.columns),'not_mapped'])
    save_to_db(bto_df, f"{id_column_name}__nodes")
    


def fetch_relationship(ontology_term, id_column_name):
    def get_subterms(terms):
        return [i.id for i in terms.subclasses(with_self=False, distance=1)]

    sub_df = pd.DataFrame([(i.id, get_subterms(i)) for i in ontology_term],
                          columns=[f"{id_column_name}_target", f"{id_column_name}_source"]).explode(f"{id_column_name}_source").dropna(subset=[f"{id_column_name}_source"])

    # Have only the nodes which are present in the node table
    node_df = read_from_db(f"{id_column_name}__nodes")[[f"{id_column_name}_id"]]
    node_df.columns = [f'{id_column_name}_source']
    sub_df = pd.merge(node_df,sub_df,on=f'{id_column_name}_source',how='inner')

    sub_df['relation'] = f'is_a_{id_column_name}'
    add_table_name([f"{id_column_name}__is_a__relation",id_column_name,id_column_name,f'is_a_{id_column_name}','not_mapped'])
    save_to_db(sub_df, f"{id_column_name}__is_a__relation")


def relationship_bto(ontology,ontology_term, id_column_name):
    bto_part = []
    bto_rel = []
    bto_id = []
    bto_target_type = []

    for terms in ontology_term:
        term_rel = [j.id for j in terms.relationships]
        for rel in term_rel:
            try:
                ts = terms.relationships.get(ontology.get_relationship(rel))
                # print(ts)
                if ts is not None and len(ts) > 0:
                    bto_part.append([i.id for i in ts])
                    bto_id.append(str(terms.id))
                    bto_rel.append(rel)
                    bto_target_type.append(list(list(ts)[0].subsets)[0])
            except KeyError:
                print("Error")
                print(terms.id)

    rel_df = pd.DataFrame(zip(bto_id, bto_rel, bto_part,bto_target_type), columns=[id_column_name, 'relation', 'target','target_type'])
    rel_df = rel_df.explode('target')
    rel_df = rel_df.dropna(subset=['target'])

    rel_target_type = {}
    for rel in rel_df["relation"].unique():
        rel_target_type[rel] = set()

    for i in range(len(rel_df)):
        rel_target_type[rel_df.iloc[i]['relation']].add(rel_df.iloc[i]['target_type'])

    # print(rel_target_type)

    for rel in rel_df['relation'].unique():
        for keys in rel_target_type[rel]:
            df = rel_df[(rel_df['relation'] == rel) & (rel_df['target_type'] == keys)]
            target_type = df['target_type'].unique()[0]
            df = df.drop('target_type',axis=1)
            df.columns = [f"{id_column_name}_source",'relation',f"{target_type}_target"]
            
            # Have only the nodes that are present in node table
            node_df = read_from_db(f'{target_type}__nodes')[[f'{target_type}_id']]
            node_df.columns = [f'{target_type}_target']
            df = pd.merge(node_df,df,on=f'{target_type}_target',how='inner')

            if len(list(rel_target_type[rel])) > 1:
                df['relation'] = f"{rel}_{keys}"
                table_name = f"{id_column_name}__{rel}_{keys}__relation".replace(" ",'_')
                save_to_db(df,table_name)
                add_table_name([table_name,id_column_name,target_type,f"{rel}_{keys}",'not_mapped'])
                # update_relation([f"{rel}_{keys}"],id_column_name,target_type,table_name)
            else:
                table_name = f"{id_column_name}__{rel}__relation"
                save_to_db(df,table_name)
                add_table_name([table_name,id_column_name,target_type,df['relation'].iloc[0],'not_mapped'])
                # update_relation([rel],id_column_name,target_type,table_name)

def main_load_tissue_cell_type(bto):
    ontology, new = bto
    if new:
        for name_type in ["tissue", "cell_type"]:
            bto_ontology_term = get_type_terms(ontology, name_type)
            fetch_node_properties(bto_ontology_term, name_type)
        for name_type in ['tissue',"cell_type"]:
            bto_ontology_term = get_type_terms(ontology, name_type)
            fetch_relationship(bto_ontology_term, name_type)
            relationship_bto(ontology,bto_ontology_term, name_type)



if __name__ == "__main__":
    # Read obo file
    bto = pronto.Ontology("ontologies/tissue.obo")
    main_load_tissue_cell_type((bto,True))
