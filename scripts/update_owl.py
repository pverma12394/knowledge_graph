from scripts.create_db import read_from_db


def create_object_properties():
    rel_df = read_from_db("rel_table_names")
    line_list = []
    line_list.append("\n\n### Object")
    for index, row in rel_df.iterrows():
        relation_name = row["relation_name"]
        source = row["source_type"]
        target = row["target_type"]
        x = f"""
###  http://www.semanticweb.org/pawan/ontologies/2022/6/untitled-ontology-20#{relation_name}
:{relation_name} rdf:type owl:ObjectProperty ;
                 rdfs:domain :{source} ;
                 rdfs:range :{target} ;
                 :id "{relation_name}"^^xsd:string ;
                 :shorthand "{relation_name}"^^xsd:string ;
                 rdfs:label "{relation_name.replace('_', ' ')}"^^xsd:string .
        """
        line_list.append(x)
    return line_list


def create_data_properties():
    df = read_from_db("node_table_names")
    props = ";".join(df["properties"].tolist())
    props = [i for i in props.split(";")]  # if "_id" not in i]
    line_list = []
    line_list.append("\n\n### Data")
    for prop in props:
        x = f"""
###  http://www.semanticweb.org/pawan/ontologies/2022/6/untitled-ontology-20#{prop}
:{prop} rdf:type owl:DatatypeProperty ;
        rdfs:range xsd:string .
        """
        line_list.append(x)
    return line_list


def create_class_properties():
    df = read_from_db("node_table_names")
    prop_list = df["type"].tolist()
    line_list = []
    line_list.append("\n\n### Class")
    for prop in prop_list:
        x = f"""
###  http://www.semanticweb.org/pawan/ontologies/2022/6/untitled-ontology-20#{prop}
:{prop} rdf:type owl:Class .
            """
        line_list.append(x)
    return line_list

def update_owl(file_name):
    cp = create_class_properties()
    dp = create_data_properties()
    op = create_object_properties()
    cp.extend(dp)
    cp.extend(op)
    start = """@prefix : <http://www.semanticweb.org/pawan/ontologies/2022/6/untitled-ontology-20#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix obda: <https://w3id.org/obda/vocabulary#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@base <http://www.semanticweb.org/pawan/ontologies/2022/6/BioMedOnto> .

<http://www.semanticweb.org/pawan/ontologies/2022/6/BioMedOnto> rdf:type owl:Ontology .
    """
    all_lines = "\n\n".join(cp)
    all_lines = start + "\n\n" + all_lines
    with open(file_name, "w+") as f:
        f.write(all_lines)



if __name__ == "__main__":
    cp = create_class_properties()
    dp = create_data_properties()
    op = create_object_properties()
    cp.extend(dp)
    cp.extend(op)
    start = """@prefix : <http://www.semanticweb.org/pawan/ontologies/2022/6/untitled-ontology-20#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xml: <http://www.w3.org/XML/1998/namespace> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix obda: <https://w3id.org/obda/vocabulary#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@base <http://www.semanticweb.org/pawan/ontologies/2022/6/BioMedOnto> .

<http://www.semanticweb.org/pawan/ontologies/2022/6/BioMedOnto> rdf:type owl:Ontology .
    """
    all_lines = "\n\n".join(cp)
    all_lines = start + "\n\n" + all_lines
    with open("semantics/BioMedOnto_1.owl", "w+") as f:
        f.write(all_lines)
