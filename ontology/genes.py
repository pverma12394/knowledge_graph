# This code fetches properties of genes from Harmonizome api
import math
import json
import requests
import pandas as pd
from multiprocessing import Process, Manager
from scripts.create_db import save_to_db,read_from_db, add_node_table_name


def return_json(url):
    try:
        response = requests.get(url)
    except:
        print("Timed out")
        print(url)
        return {"symbol": "",
                "synonyms": [],
                "name": "",
                "description": "",
                "ncbiEntrezGeneId": -1,
                "ncbiEntrezGeneUrl": "",
                "proteins": [],
                "hgncRootFamilies": []}

    if response.status_code == 200:
        data = json.loads(response.text)
        return data

    else:
        return {"symbol": "",
                "synonyms": [],
                "name": "",
                "description": "",
                "ncbiEntrezGeneId": -1,
                "ncbiEntrezGeneUrl": "",
                "proteins": [],
                "hgncRootFamilies": []}


def gene_properties(gene_lst, num, return_dict):
    base_url = "https://maayanlab.cloud/Harmonizome/api/1.0/gene/"

    gene_prop_dict = {"gene_id": [],
                      "synonyms": [],
                      "name": [],
                      "definition": [],
                      "NcbiEntrezGeneId": [],
                      "NcbiEntrezGeneUrl": [],
                      "proteins": [],
                      "HgncRootFamilies": []}

    for gene in gene_lst:
        url = base_url + gene
        gene_props = return_json(url)
        gene_prop_dict['gene_id'].append(gene)

        synonyms = ""
        if gene_props['synonyms']:
            for i in range(len(gene_props['synonyms'])):
                synonyms += gene_props['synonyms'][i]
                if i != len(gene_props['synonyms']) - 1:
                    synonyms += ';'
        gene_prop_dict['synonyms'].append(synonyms)

        gene_prop_dict['name'].append(gene_props['name'])
        gene_prop_dict['definition'].append(gene_props['description'])
        gene_prop_dict['NcbiEntrezGeneId'].append(gene_props['ncbiEntrezGeneId'])
        gene_prop_dict['NcbiEntrezGeneUrl'].append(gene_props['ncbiEntrezGeneUrl'])

        proteins = ""
        if gene_props['proteins']:
            for i in range(len(gene_props['proteins'])):
                proteins += gene_props['proteins'][i]['symbol']
                if i != len(gene_props['proteins']) - 1:
                    proteins += ','
        gene_prop_dict['proteins'].append(proteins)

        root_family = ""
        if gene_props['hgncRootFamilies']:
            for i in range(len(gene_props['hgncRootFamilies'])):
                root_family += gene_props['hgncRootFamilies'][i]['name']
                if i != len(gene_props['hgncRootFamilies']) - 1:
                    root_family += ','
        gene_prop_dict['HgncRootFamilies'].append(root_family)

    return_dict[num] = gene_prop_dict


def retrive_gene_properties(gene_lst):
    num_processes = 20

    return_dict = Manager().dict()
    jobs = []

    for i in range(num_processes):
        lb = i * math.ceil(len(gene_lst) / num_processes)
        up = min((i + 1) * math.ceil(len(gene_lst) / num_processes), len(gene_lst))

        p = Process(target=gene_properties, args=(gene_lst[lb:up], i, return_dict))
        jobs.append(p)
        p.start()

    for process in jobs:
        process.join()

    df = pd.concat([pd.DataFrame(return_dict[i]) for i in range(len(return_dict))])

    return df


def main_genes():
    # present in disease gene associations
    df = read_from_db("disease__associated_with__relation")
    gene_lst = list(set(df['gene_target']))  

    gene_nodes = retrive_gene_properties(gene_lst)        # remove the list slice
    gene_nodes['type'] = 'gene'
    add_node_table_name(['gene__nodes','gene',';'.join(gene_nodes.columns),'not_mapped'])
    save_to_db(gene_nodes, "gene__nodes")

# main
if __name__ == '__main__':
    # find gene node properties for genes
    # present in disease gene associations
    df = read_from_db("disease__associated_with__relation")
    gene_lst = list(set(df['gene']))

    gene_nodes = retrive_gene_properties(gene_lst[:30])
    save_to_db(gene_nodes, "gene__nodes")
