# This code is for getting disease gene associations by using Harmonizome api
import sys
sys.path.append("/Users/pawan/Documents/Elucidata/Knowledge_Graphs/biomedical_ontology/biomedical_ontologies_kg/")
from dotenv import load_dotenv
import math
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from multiprocessing import Process, Manager
from scripts.harmonizomeapi import Harmonizome, Entity
from scripts.create_db import save_to_db,add_table_name, read_from_db

load_dotenv()
def return_json(addr):
    base_url = "https://maayanlab.cloud/Harmonizome"

    url = base_url + addr
    try:
        response = requests.get(url)
    except:
        # todo: what kind of error exception?
        print("Error")
        print(addr)
        return " "

    if response.status_code == 200:
        try:
            data = json.loads(response.text)
            return data
        except:
            return " "

    else:
        print("Error")
        print(addr)


def convert_name_to_url(name):
    url_name1 = name.replace(',', '%').replace(" ", '+')
    url_name2 = name.replace(',', '%2C').replace(" ", '+')

    url1 = "https://maayanlab.cloud/Harmonizome/gene_set/" + url_name1 + "/CTD+Gene-Disease+Associations"
    url2 = "https://maayanlab.cloud/Harmonizome/gene_set/" + url_name2 + "/CTD+Gene-Disease+Associations"

    # html2 = requests.get(url2)

    # if html2.status_code == 200:
    #     return url2
    # else:
    #     return url1

    return (url1,url2)


def find_mesh_id(url_tup):
    try:
        html1 = requests.get(url_tup[0])
        if html1.status_code == 200:
            html_text = html1.text
            soup = BeautifulSoup(html_text, 'html.parser')

            for link in soup.find_all('a'):
                link_url = link.get('href')
                if "ctdbase.org" in link_url:
                    mesh_id = link_url.split('=')[-1]
                    return mesh_id
    except:
        return " "

    try:
        html2 = requests.get(url_tup[0])
        if html2.status_code == 200:
            html_text = html2.text
            soup = BeautifulSoup(html_text, 'html.parser')

            for link in soup.find_all('a'):
                link_url = link.get('href')
                if "ctdbase.org" in link_url:
                    mesh_id = link_url.split('=')[-1]
                    return mesh_id
    except:
        return " "

    return " "



def disease_gene_associations(genesets, num, return_dict):
    dis_gene_dict = {
        'disease_id': [],
        'Associated_Gene_Symbols': []}

    for geneset in genesets:
        disease_name = geneset['name'].split('/')[0]

        url_tup = convert_name_to_url(disease_name)
        mesh_id = find_mesh_id(url_tup)

        gene_info = return_json(geneset['href'])
        if mesh_id != " " and gene_info != " ":
            dis_gene_dict['disease_id'].append(mesh_id)

            genes = [gene['gene']['symbol'] for gene in gene_info['associations']]
            dis_gene_dict['Associated_Gene_Symbols'].append(genes)

    return_dict[num] = dis_gene_dict


def retrive_dis_gene_associations(dataset):
    num_processes = 20

    return_dict = Manager().dict()
    jobs = []

    for i in range(num_processes):
        lb = i * math.ceil(len(dataset) / num_processes)
        up = min((i + 1) * math.ceil(len(dataset) / num_processes), len(dataset))

        p = Process(target=disease_gene_associations, args=(dataset[lb:up], i, return_dict))
        jobs.append(p)
        p.start()

    for process in jobs:
        print()
        process.join()

    return pd.concat([pd.DataFrame(return_dict[i]) for i in range(len(return_dict))])


def main_disease_gene():
    dataset_lst = Harmonizome.get(Entity.DATASET)
    # CTD dataset index is 24
    dataset = return_json(dataset_lst['entities'][24]['href'])['geneSets']

    dis_gene = retrive_dis_gene_associations(dataset)      # remove the list slice

    # The disease in disease gene associations must be present in disease ontotlogy
    mesh_dis = read_from_db("disease__nodes")
    dis = mesh_dis[['disease_id']]

    # # The gene in disease gene associations must be present in gene ontology and with HGNC symbols
    hgnc_gene = read_from_db("gene__nodes")
    gene = hgnc_gene[['gene_id', 'gene_symbol']] 
    
    final_df = pd.merge(dis_gene, dis, on='disease_id', how='inner')
    
    final_df = final_df.explode('Associated_Gene_Symbols')
    final_df = final_df.dropna(subset=['Associated_Gene_Symbols'])
    final_df = pd.merge(dis_gene, gene, left_on='Associated_Gene_Symbols', right_on='gene_symbol', how='inner')
    final_df = final_df[['disease_id', 'gene_id']]
    final_df.columns = ['disease_source', 'gene_target']
    final_df['relation'] = 'associated_with'
    add_table_name(["disease__associated_with__relation",'disease','gene','associated_with','not_mapped'])
    save_to_db(final_df, "disease__associated_with__relation")


# main
if __name__ == '__main__':
    main_disease_gene()


