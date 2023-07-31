import pronto
from urllib.error import HTTPError
import yaml
from scripts.create_db import read_from_db, save_to_db


def load_file(file_type: str):
    """
    Load ontology obo files from GitHub
    Arguments:
        file_type : entity type of ontology, values are checked in entity yaml file for
                    the url of content
    Returns:
        ontology object, boolean value (if ontology has some new changes)
    """
    with open("./entity_meta.yaml") as f:  # changed
        em = yaml.safe_load(f)
    try:
        ontology = pronto.Ontology(em[file_type]["link"])
    except HTTPError:
        print(f"File {file_type} does not exist")
        return None, False
    em_version = em[file_type]["version"]
    ontology_version = ontology.metadata.data_version if ontology.metadata.data_version is not None else \
        ontology.metadata.format_version
    if em_version != ontology_version:
        print(f"New version found {file_type}")
        return ontology, True
    else:
        print(f"Returning current version {file_type}")
        return ontology, True  # todo: update this to false


def create_node_mappings():
    def return_prop_str(string):
        prop_lst = string.split(';')
        prop_str = ""
        for prop in prop_lst:
            # if "_id" in prop:
            #     new_prop = prop[-2:]
            # else:
            #     new_prop = prop
            prop_str += f'; :{prop} {{{prop}}}^^xsd:string '
        return prop_str

    node_df = read_from_db("node_table_names")
    new_mapping = []
    for index, row in node_df.iterrows():
        if row['mapping'] == 'not_mapped':
            prop_str = return_prop_str(row['properties'])
            entity_type = row['type']
            temp = ["\n", f"mappingId   MAPID-{entity_type}", "\n",
                    f"target    :kgdb/{entity_type}/{{{entity_type}_id}} a :{entity_type} {prop_str} .", "\n",
                    f"source    SELECT * FROM {row['table_name']}", "\n"
                    ]
            new_mapping.extend(temp)

    node_df['mapping'] = 'mapped'  ############# uncomment
    save_to_db(node_df, "node_table_names")
    return new_mapping


def create_rel_mappings():
    rel_df = read_from_db("rel_table_names")
    new_mapping = []
    for index, row in rel_df.iterrows():
        if row['mapping'] == 'not_mapped':
            source, target, rel, table_name = row["source_type"], row["target_type"], row["relation_name"], row[
                "table_name"]
            source_col = f"{source}_id"
            target_col = f"{target}_id"
            temp = ["\n", f"mappingId	MAPID-{source}_id_{rel}_relation", "\n",
                    f"target		:kgdb/{source}/{{{source_col}}} :{rel} :kgdb/{target}/{{{target_col}}} . ", "\n",
                    f"source		SELECT * FROM {table_name}", "\n"
                    ]
            new_mapping.extend(temp)

    rel_df['mapping'] = 'mapped'
    save_to_db(rel_df, "rel_table_names")
    return new_mapping


def update_mapping(mapping_file_name="../semantics/BioMedOnto.obda"):
    with open(mapping_file_name, 'r+') as file:
        new_mapping = create_node_mappings()
        rel_mapping = create_rel_mappings()
        new_mapping.extend(rel_mapping)

        new_mapping.append("]]")
        lines = file.readlines()[:-1]
        lines.extend(new_mapping)
        file.seek(0)
        file.truncate()
        file.writelines(lines)



if __name__ == "__main__":
    update_mapping()

# check if there is an updated content
# run get_ontology function if there is an update and save the data in db
