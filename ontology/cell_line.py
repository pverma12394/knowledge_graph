import pronto
from dotenv import load_dotenv
import os
import sys
import pandas as pd
#sys.path.append("/home/ubuntu/environment/biomedical_ontologies_kg")
from scripts.create_db import read_from_db, save_to_db, add_table_name,add_node_table_name
#from scripts.load import load_file
from get_all_terms import *


load_dotenv()
def get_polly_cl(indexes):
    term_repos= {}; #{term:{repos}}
    field = 'cell_line'
    polly_env = 'prod'
    for i,oa in enumerate(list(indexes.values())):
        if i%4==0:
            allz= get_all_cell_lines_polly(field, oa, polly_env)
        
        for w in {d.strip() for d in allz}:
            term_repos[w]= term_repos.get(w,set()) | {oa.replace("_files","")}
    term_repos.pop("",None)
    return term_repos.keys()

def cell_line_node(clo_v3):
    """
    Creating nodes table for cell line from cellosaurus ontology
    """
    gender_terms = ['Male', 'Female', 'Mixed_sex', 'Sex_ambiguous', 'Sex_unspecified']

    df = pd.DataFrame([(i.id, i.name, list(i.subsets.intersection(gender_terms)),
                        list(i.subsets.difference(gender_terms)), i.synonyms,'cell-line') for i in clo_v3.terms()],
                      columns=['cell_line_id', 'name', 'gender', 'category', 'synonyms','type'])
    df['synonyms'] = df["synonyms"].apply(lambda x: ';'.join([str(str(i).split("'")[1]) for i in x]))
    df['gender'] = df['gender'].apply(lambda x: x[0] if len(x) > 0 else " ")
    df['category'] = df["category"].apply(lambda x: x[0] if len(x) > 0 else " ")
    df = df[df['name'].isin(polly_cell_lines)]
    add_node_table_name(['cell_line__nodes','cell_line',';'.join(df.columns),'not_mapped'])
    save_to_db(df, "cell_line__nodes")


def cell_line_rel(clo_v3):
    """
    Creating relation file for cell line from cellosaurus ontology
    """
    rels_clo = [r.id for r in clo_v3.relationships()]

    clo_tar = []
    clo_rel = []
    clo_id = []

    for terms in clo_v3.terms():
        for rel in rels_clo:
            if rel in str(list(terms.relationships)):
                ts = terms.relationships[clo_v3.get_relationship(rel)]
                clo_id.append(str(terms.id))
                clo_rel.append(rel)
                clo_tar.append(str(list(ts)[0].id))

    rel_df = pd.DataFrame(list(zip(clo_id, clo_rel, clo_tar)), columns=['cell_line_source', 'relation', 'cell_line_target'])
    rel_df = rel_df.explode('cell_line_target')
    rel_df = rel_df.dropna(subset=['cell_line_target'])

    # Have nodes only if they are present in node table
    node_df = read_from_db("cell_line__nodes")[["cell_line_id"]]
    node_df.columns = ['cell_line_target']
    rel_df = pd.merge(node_df,rel_df,on='cell_line_target',how='inner')
    # print(len(node_df))
    # node_df = set(node_df["cell_line_id"])
    # tar = set(rel_df['cell_line_target'])
    # print("nodes:",len(node_df))
    # print("target:",len(tar))
    # # print(tar.difference(node_df))
    # print(len(tar.difference(node_df)))
    # print("\n\n")


    # save to db
    for rel in rels_clo:
        # print(rel)
        df = rel_df[rel_df['relation'] == rel]
        add_table_name([f"cell_line__{rel}__relation","cell_line","cell_line",rel,'not_mapped'])
        # update_relation([rel],"cell_line","cell_line",f"cell_line__{rel}__relation")
        save_to_db(df, f"cell_line__{rel}__relation")

def disease_cell_line(clo_2):
    """
    Creating cell line and disease table
    """
    # clo_dis = []
    # clo_id = []
    clo_all = []
    for term in clo_2.terms():
        for xref in term.xrefs:
            if xref.id.startswith("MESH"):
                clo_all.append((term.id, xref.id, term.name))
                # clo_id.append(term.id)
                # clo_dis.append(xref.id)
                # clo_id.append(ter)

    # dis = pd.DataFrame(zip(clo_id, clo_dis), columns=['cell_line_source', 'disease_target'])
    dis = pd.DataFrame(clo_all, columns=['cell_line_source', 'disease_target', "cell_line_name"])
    dis = dis[dis['cell_line_name'].isin(polly_cell_lines)]
    # print(dis.shape)
    dis['relation'] = 'obtained_from_sample_with_disease'
    add_table_name(['cell_line__obtained_from_sample_with_disease__relation','cell_line','disease','obtained_from_sample_with_disease','not_mapped'])
    save_to_db(dis, "cell_line__obtained_from_sample_with_disease__relation")


def main_cellosaurus(clo_v3):
    ontology, new = clo_v3
    if new:
        cell_line_node(ontology)
        cell_line_rel(ontology)


def main_cell_line(clo_2):
    ontology, new = clo_2
    if new:
        disease_cell_line(ontology)


if __name__ == "__main__":
    refresh_token = os.environ.get('PROD_REFRESH_TOKEN')
    library_client= OmixAtlas(refresh_token,polly_env='prod')
    repo_id_index= get_all_oas(library_client)
    polly_cell_lines = get_polly_cl(repo_id_index)
    print(polly_cell_lines)
    main_cell_line((pronto.Ontology("ontologies/cell_line.obo"),True))
    main_cellosaurus((pronto.Ontology("ontologies/cell_line_cellosaurus.obo"),True))