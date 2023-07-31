# This code reads the disease ontology file and saves it to db
import pronto
import pandas as pd
from scripts.load import load_file
from scripts.create_db import add_table_name, read_from_db, save_to_db, add_node_table_name

def disease_nodes(mesh):
    def get_synonyms(synonyms):
        syn = list(synonyms)
        temp = [str(str(s).split("'")[1]) for s in syn]
        return ';'.join(temp)

    df = pd.DataFrame([(str(i.id), str(i.name), get_synonyms(i.synonyms),'disease') for i in mesh.terms()],
                      columns=['disease_id', 'name', 'synonyms','type'])
    add_node_table_name(['disease__nodes','disease',';'.join(df.columns),'not_mapped'])
    save_to_db(df, "disease__nodes")


def disease_subclass(mesh):
    def get_subclass(terms):
        mesh = terms.subclasses(with_self=False, distance=1)
        return [str(m.id) for m in mesh]

    sub_df = pd.DataFrame([(i.id, get_subclass(i)) for i in mesh.terms()],
                          columns=['disease_target', 'disease_source'])
    sub_df = sub_df.explode('disease_source')
    sub_df = sub_df.dropna(subset=['disease_source'])
    sub_df['relation'] = 'is_a'

    node_df = read_from_db("disease__nodes")[['disease_id']]
    node_df.columns = ['disease_source']
    sub_df = pd.merge(node_df,sub_df,on='disease_source',how='inner')

    add_table_name(["disease__is_a__relation",'disease','disease','is_a','not_mapped'])
    save_to_db(sub_df, "disease__is_a__relation")


def main_mesh_disease(mesh):
    ontology, new = mesh
    if new:
        disease_nodes(ontology)
        disease_subclass(ontology)

# main
if __name__ == '__main__':
    main_mesh_disease((pronto.Ontology("ontologies/disease.obo"),True))
