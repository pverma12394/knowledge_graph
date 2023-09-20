#script for enriching disease terms with synonyms
import os
import requests
import json
import re
import pandas as pd
import mysql.connector as mysql
import joblib
import numpy as np
from dotenv import load_dotenv

#loading SQL table
load_dotenv('.env')

user = os.environ.get("mysql_user")
pw=os.environ.get("mysql_pwd")
db=os.environ.get("mysql_db")
host= "localhost"

conn = mysql.connect(host=host, user=user, passwd=pw, database=db)

#executing the mysql query to filter out the rows
c = conn.cursor()
c.execute("select * from disease__nodes;")
data = c.fetchall()
column_names = [desc[0] for desc in c.description]
#converting the table obtained to a dataframe
df = pd.DataFrame(data, columns= column_names)
#print (df)

#sending the api request
def post_request(term, p):

    api_endpoint = "http://data.bioontology.org"
    endpoint='search'
    method = 'POST'

    API_KEY = os.environ.get("api_key")
    
    kwargs = {
        'url': api_endpoint+"/"+endpoint+"/?q="+term + "&include=synonym" + "&require_exact_match=true" + "&page="+ str(p),
        'method': method,
        'headers': {
            'Authorization': 'apikey token='+API_KEY
        }
    }

    resp = requests.request(**kwargs)

    if int(resp.status_code)!=200:
        print(resp.text)

    if resp.text:
        resp_dict = json.loads(resp.text)

    return resp_dict

#extracting only the synonyms from the json file that was obtained as a api request result
def synonym(resp_dict,i):
    for x in resp_dict['collection']:
      str_to_skip = ':'
      identifier = ''
      if 'synonym' in x:
        s = x.get('synonym', [])
        if not any([str_to_skip.lower() in word.lower() for word in s]):
          syns[i]=s 
    return(syns)



def process_disease_term(disease_term):
    syns = {}
    p = 1
    resp_dict = post_request(disease_term, p)
    
    # Looping through each page of the API result
    for x in resp_dict:
        if 'pageCount' in x:
            page = resp_dict.get("pageCount")
            next = resp_dict.get("nextPage")
            
            if page > 1 and next is not None:
                for p in range(2, page + 1):
                    resp_dict = post_request(disease_term, p)
                    syns = synonym(resp_dict, disease_term)
            else:
                syns = synonym(resp_dict, disease_term)
    
    return syns

def parallel_process_disease(disease_list):
# Use joblib to parallelize the execution of process_disease
   syns_list = joblib.Parallel(n_jobs=-1)(joblib.delayed(process_disease_term)(disease) for disease in disease_list)
# Combine the results from multiple parallel executions
   combined_syns = {}
   for result in syns_list:
     combined_syns.update(result)
   return combined_syns

#accessing each disease term for api request
disease = df['name']
syns = {}
result= parallel_process_disease(disease)
df['Synonym_new']= df['name'].map(result)

#clean the synonym list obtained
def remove_non_standard(data):
 pattern = re.compile("[^a-zA-Z0-9\s-]+")
 cleaned_data = re.sub(pattern, "", data)
 return cleaned_data

def clean_list(lst):
  if isinstance(lst, list):
   cleaned_items = [remove_non_standard(item) for item in lst]
   cleaned_items = [item for item in cleaned_items if item.strip() != ""]
   return cleaned_items
  else:
   return lst
df['Synonym_new'] = df['Synonym_new'].apply(clean_list)

# Define a function to join the elements of an array into a string separated by semicolons

# Function to join synonyms in each row
def join_synonyms(row):
    if not isinstance(row, list):
        return row

    joined_items = []

    for item in row:
        if isinstance(item, list):
            joined_items.append(';'.join(item))
        elif isinstance(item, str):
            joined_items.append(str(item))

    return ';'.join(joined_items)

# Apply the function to the 'synonyms' column and create a new column 'synonyms_str'
df['Synonym_new'] = df['Synonym_new'].apply(join_synonyms)

#df.to_csv("/home/nayanika/Documents/el/codechange.csv", sep='\t')

# Replace NaN values in column2 with an empty string
df['Synonym_new'] = df['Synonym_new'].replace(np.nan, '')

# Function to split and merge terms and synonyms to the old column "synonyms"
def merge_columns(row):
    synonyms1 = set(row['synonyms'].split(';')) if row['synonyms'] else set()
    synonyms2 = set(row['Synonym_new'].split(';')) if row['Synonym_new'] else set()
    
    terms1 = [term.strip() for term in row['synonyms'].split(',') if 'term' in term]
    terms2 = [term.strip() for term in row['Synonym_new'].split(',') if 'term' in term]
    
    merged_synonyms = ';'.join(synonyms1.union(synonyms2))
    merged_terms = ','.join(terms1 + terms2)
    
    if merged_synonyms:
        return f'{merged_synonyms},{merged_terms}'
    else:
        return merged_terms

# Apply the function to each row
df['synonyms'] = df.apply(merge_columns, axis=1)
df['synonyms'] = df['synonyms'].str.rstrip(',')
df.drop(columns=['Synonym_new'], inplace=True)

#print (df)

def update_column_in_sql_table(table_name, updated_column, unique_column, df):

# Define the SQL UPDATE query
 update_query = f"UPDATE {table_name} SET {updated_column} = %s WHERE {unique_column} = %s;"

# Execute the UPDATE query for each row in the DataFrame
 for index, row in df.iterrows():
   row[updated_column] = str(row[updated_column]) # Ensure data type compatibility
   c.execute(update_query, (row[updated_column], row[unique_column]))

# Commit the changes to the MySQL database
 conn.commit()

table_name= "disease__nodes"
updated_column= "synonyms"
unique_column= "name"
#Call the function to update the 'synonyms' column
update_column_in_sql_table(table_name, updated_column, unique_column, df)

print("Data updated in the MySQL table.")
