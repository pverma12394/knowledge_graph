from py2neo import Graph
import os

'''
# starter queries (after changing settings conf file and installing n10s)
CALL n10s.graphconfig.init();
CREATE CONSTRAINT n10s_unique_uri ON (r:Resource)
ASSERT r.uri IS UNIQUE;
call n10s.graphconfig.init( { handleMultival: "ARRAY", keepLangTag: false, handleRDFTypes: "LABELS" ,handleVocabUris: "SHORTEN" })
'''


def ontology_export(file_name: str, file_format: str="Turtle"):
    """
    Export rdf triplet file in neo4j graph
    Arguments:
        file_name: Name of file where triplets are stored after running ontology materialize
        file_format: format of the input rdf file
    """
    g = Graph(os.environ.get("host"), user=os.environ.get("neo4j_user"), password="harsha123", name="Graph DBMS")
    import_rdf_query = f'CALL n10s.rdf.import.fetch("file:///{file_name}","{file_format}")'
    result = g.run(import_rdf_query).data()
    print(result)


if __name__ == "__main__":
    ontology_file_name = "file:///Users/kanak/elucidata/projects/biomedical_ontologies_kg/semantics/BioMedOnto-materialized.ttl"
    ontology_export(ontology_file_name)