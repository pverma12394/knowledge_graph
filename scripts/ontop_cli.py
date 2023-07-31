import subprocess
import sys
import os


class OntopMaterializeException(Exception):
    pass


def verify_file(*args):
    """
    Verifying if all the arguments provided are valid file names or directory
    Arguments:
        args: File names provided as arguments in ontop materialze command
    """
    for fn in args:
        fn_exists = os.path.exists(fn)
        if not fn_exists:
            raise OntopMaterializeException(f"File {fn} does not exist")


def materialize(mapping, ontology, output, properties, output_format="turtle"):
    """
    Ontop cli materializing function
    Arguments:
        mapping : OBDA mapping file
        ontology: OWL ontology file
        output: Output turtle file where triplets would be materialized
        properties: Properties file containing mysql or db info
        output_format: Format of output materialized file
    """
    # try:
    #     verify_file(mapping, ontology,"/".join(output.split("/")[:-1]), properties)
    # except OntopMaterializeException:
    #     return
    if output_format not in ["turtle"]:
        print(f"Output format {output_format} not supported.")
        return

    if sys.platform == 'win32':
        cmd_output = subprocess.run([f"{os.environ.get('ontop_path')}/ontop.bat", "materialize",
                                    "-m", mapping,
                                    "-t", ontology,
                                    "-p", properties,
                                    "-f", output_format,
                                    "-o", output
                                    ])
    else:
        cmd_output = subprocess.run([f"{os.environ.get('ontop_path')}/ontop", "materialize",
                                    "-m", mapping,
                                    "-t", ontology,
                                    "-p", properties,
                                    "-f", output_format,
                                    "-o", output
                                    ])

    if cmd_output.returncode != 0:
        raise OntopMaterializeException("Error while running materialize command")
    print(cmd_output)


if __name__ == "__main__":
    file_path = "/Users/kanak/Downloads"
    try:
        materialize(mapping=f"{file_path}/university.obda",
                    ontology=f"{file_path}/university.ttl",
                    output="sample_output.ttl",
                    properties=f"{file_path}/university.properties"
                    )
    except OntopMaterializeException as e:
        print(f"Error in materializing {e}")
