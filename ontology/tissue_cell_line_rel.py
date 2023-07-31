# This code links tissue with cell line
import sys
from dotenv import load_dotenv
sys.path.append("/home/ubuntu/environment/biomedical_ontologies_kg")
import pronto
import pandas as pd
from scripts.load import load_file
from scripts.create_db import add_table_name, save_to_db,read_from_db

def get_tissue_cell_line(bto_ontology,cell_df):
	#Clean tissue column and Create a secondary tissue column	
	cell_df['secondary_tissue'] = cell_df['Tissue'].str.split(';').str[1]
	cell_df['secondary_tissue'] = cell_df['secondary_tissue'].str.strip(' ')
	
	#Tissue column only includes the primary tissue terms
	cell_df['Tissue'] = cell_df['Tissue'].str.split(';').str[0]

	#Clean tissue column
	cell_df['Tissue'].apply(lambda x: " " if '=' in str(x) else x)

	class_df = read_from_db("cell_line__nodes")

	#Subset using CLO
	cell_df = cell_df[cell_df['ACC'].isin(class_df['cell_line_id'])]
	cell_df = cell_df.dropna(subset=['Tissue'])
	cell_df['Tissue'] = cell_df['Tissue'].apply(lambda x: x.lower())

	bto_df = read_from_db("tissue__nodes")
	
	#Map tissue terms to BTO
	bto_clo = bto_df.merge(cell_df, how='inner', left_on='name', right_on='Tissue')
	bto_clo = bto_clo[['tissue_id', 'ACC']]
	bto_clo.columns = ['tissue_target', 'cell_line_source']
	bto_clo['relation'] = 'sampled_from'
	add_table_name(["tissue__sampled_from__relation",'cell_line','tissue','sampled_from','not_mapped'])
	save_to_db(bto_clo,"tissue__sampled_from__relation")


def main_tissue_cell_line_rel(bto):
	ontology, new = bto
	if new:
		cell_df = pd.read_csv('ontologies/tissue_cell_line.csv')  # Check and change the path

		get_tissue_cell_line(ontology, cell_df)

# main
if __name__ == '__main__':

	# Read the bto file
	# bto,new = load_file("tissue")

	# if new:
	# 	# Read tissue_cell_line.csv
	# 	cell_df = pd.read_csv('tissue_cell_line.csv')             # Check and change the path

	# 	get_tissue_cell_line(bto,cell_df)

	main_tissue_cell_line_rel((pronto.Ontology("ontologies/tissue.obo"),True))



	
