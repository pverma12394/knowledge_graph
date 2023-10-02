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

def connect_to_sql():
  '''
  connecting to mysql server
  '''
  load_dotenv('.env')
  user = os.environ.get("mysql_user")
  pw=os.environ.get("mysql_pwd")
  db=os.environ.get("mysql_db")
  host= "localhost"
  conn = mysql.connect(host=host, user=user, passwd=pw, database=db)
  c = conn.cursor()
  return conn, c 

def fetch_disease_nodes(c):
  '''
  Fetch data from the disease_nodes table and return it as a DataFrame.

  Args:
      c(connection): connection to mysql server

  Return:
      df(dataFrame): Returning all the columns of the table as dataframe    
  '''
  c.execute("select * from disease__nodes;")
  data = c.fetchall()
  column_names = [desc[0] for desc in c.description]
  df = pd.DataFrame(data, columns= column_names)
  return df

def post_request(term, p):
    '''
    Perform a POST request to the BioPortal API to search for terms and retrieve synonym information.

    Args:
        term (str): The search term.
        p (int): The page number for pagination.

    Returns:
        dict: A dictionary containing the API response in JSON format.

    Note:
        This function constructs a POST request to the BioPortal API using the provided search term and page number.
        It includes synonyms and requires an exact match in the search results.
        The API key should be set as an environment variable named 'api_key' for authentication.
    '''
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

def synonym(resp_dict,i,syns):
    '''
    Extract and organize synonyms for a disease term from the JSON response obtained from a BioPortal API request.

    Args:
        resp_dict (dict): The JSON response dictionary obtained from the API request.
        i (int): The disease term associated with the response.
        syns(dict): Disease and their associated synonyms will be stored as key-value pair.

    Returns:
        dict: A dictionary where the key is the disease term 'i' and the value is a list of synonyms (strings).

    Note:
        This function iterates through the 'collection' key in the provided JSON response dictionary
        and extracts synonyms for the disease term specified by 'i'.
        It skips synonyms that contain a colon (':') in their text.
    '''
    for x in resp_dict['collection']:
      str_to_skip = ':'
      if 'synonym' in x:
        s = x.get('synonym', [])
        if not any([str_to_skip.lower() in word.lower() for word in s]):
          syns[i]=s 
    return(syns)

def process_disease_term(disease_term):
    '''
    Process a disease term to retrieve and organize its synonyms from the BioPortal API.

    Args:
        disease_term (str): The disease term to search for in the API.

    Returns:
        dict: A dictionary where keys are the disease terms and values are lists of synonyms (strings) for the disease term.

    Note:
        This function initiates a search for the specified disease term using the BioPortal API and retrieves
        synonyms for the term from multiple pages of API results if available. It handles pagination automatically.
        It uses the 'post_request' function to query the API and the 'synonym' function to extract synonyms.
    '''
    syns = {}
    p = 1
    resp_dict = post_request(disease_term, p)
    for x in resp_dict:
        if 'pageCount' in x:
            page = resp_dict.get("pageCount")
            next = resp_dict.get("nextPage")
            if page > 1 and next is not None:
                for p in range(2, page + 1):
                    resp_dict = post_request(disease_term, p)
                    syns = synonym(resp_dict, disease_term,syns)
            else:
                syns = synonym(resp_dict, disease_term,syns)
    return syns

def parallel_process_disease(disease_list):
   '''
   Perform parallel processing to retrieve and organize synonyms for a list of disease terms.

    Args:
        disease_list (list): A list of disease terms to search for in the API.

    Returns:
        combined_syns (dict):  The results from multiple parallel executions are combined into a single dictionary.

    Note:
        This function parallelizes the execution of the 'process_disease_term' function for each disease term in the list.
        It uses the 'joblib' library to efficiently distribute the work across multiple CPU cores (n_jobs=-1).
   '''
   syns_list = joblib.Parallel(n_jobs=-1)(joblib.delayed(process_disease_term)(disease) for disease in disease_list)
   combined_syns = {}
   for result in syns_list:
     combined_syns.update(result)
   return combined_syns

def remove_non_standard(data):
 '''
 Remove non-standard characters from a string.

    Args:
        data (str): The input string containing potentially non-standard characters.

    Returns:
        cleaned_data (str): The cleaned string with non-standard characters removed.

    Note:
        This function takes an input string and uses a regular expression pattern to remove characters
        that are not letters (both uppercase and lowercase), digits, spaces, or hyphens from the string.
        The cleaned string is then returned
 '''
 pattern = re.compile("[^a-zA-Z0-9\s-]+")
 cleaned_data = re.sub(pattern, "", data)
 return cleaned_data

def clean_list(lst):
  '''
    Clean a list of strings by removing non-standard characters and empty strings.

    Args:
        lst (list): A list of strings to be cleaned.

    Returns:
        lst (list): A cleaned list where non-standard characters and empty strings have been removed.

    Note:
        This function takes a list of strings as input and performs the following cleaning steps:
        1. It uses the 'remove_non_standard' function to remove non-standard characters from each string in the list.
        2. It removes any empty strings from the list.
        The cleaned list is then returned.
  '''
  if isinstance(lst, list):
   cleaned_items = [remove_non_standard(item) for item in lst]
   cleaned_items = [item for item in cleaned_items if item.strip() != ""]
   return cleaned_items
  else:
   return lst
  
def join_synonyms(row):
    '''
    Join the elements of a list into a string separated by semicolons.

    Args:
        row (list or str): The input row to be processed. If it's a list, its elements will be joined;
                       if it's a string, it will be returned as is.

    Returns:
           str: A string where the elements of the input list are joined together with semicolons.
           If the input is already a string, it is returned without modification.
    '''
    if not isinstance(row, list):
        return row
    joined_items = []
    for item in row:
        if isinstance(item, list):
            joined_items.append(';'.join(item))
        elif isinstance(item, str):
            joined_items.append(str(item))
    return ';'.join(joined_items)

def merge_columns(row):
    '''
    Merge terms and synonyms from two columns into the 'synonyms' column.

    Args:
        row (pandas.Series): A row from a DataFrame containing the two columns:
                            'synonyms' and 'Synonym_new'. The 'synonyms' column contains
                            existing synonyms along with the MeSH terms, while 'Synonym_new'
                            contains new synonyms obtained from BioPortal.

    Returns:
       merged_terms (str): A string containing merged synonyms and terms, with duplicate synonyms removed.

    Note:
        This function merges synonyms and terms from two columns, 'synonyms' and 'Synonym_new',
        into the 'synonyms' column. It handles the following steps:
        1. Separates the existing and new synonyms into sets, removing duplicates.
        2. Separates terms from both columns.
        3. Merges the sets of synonyms and joins the lists of terms.
        4. Combines the merged synonyms and terms into a single column.
    '''
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
    
def update_column_in_sql_table(table_name, updated_column, unique_column, df):
 '''
  Update the column in the SQL table.

    Args:
        table_name (str): The name of the SQL table to update.
        updated_column (str): The name of the column to update in the SQL table.
        unique_column (str): The name of the unique identifier column in the SQL table.
        df (pandas.DataFrame): The DataFrame containing the updated data to be written to the SQL table.

    Note:
        This function constructs and executes an SQL UPDATE query to update the values in the 'updated_column'
        of the specified 'table_name' using data from the DataFrame 'df'. The update is performed based on
        the unique values in the 'unique_column'.
        After updating, the changes are committed to the MySQL database.
 '''
 update_query = f"UPDATE {table_name} SET {updated_column} = %s WHERE {unique_column} = %s;"
 for index, row in df.iterrows():
   row[updated_column] = str(row[updated_column]) 
   c.execute(update_query, (row[updated_column], row[unique_column]))
 conn.commit()

def process_df(df):
   #accessing each disease term for api request
   disease = df['name']
   result= parallel_process_disease(disease)

   # mapping the list of new synonyms with their corresponding disease terms
   df['Synonym_new']= df['name'].map(result)

   df['Synonym_new'] = df['Synonym_new'].apply(clean_list)
   df['Synonym_new'] = df['Synonym_new'].apply(join_synonyms)

   # Replace NaN values in column2 with an empty string
   df['Synonym_new'] = df['Synonym_new'].replace(np.nan, '')

   df['synonyms'] = df.apply(merge_columns, axis=1)
   df['synonyms'] = df['synonyms'].str.rstrip(',')
   df.drop(columns=['Synonym_new'], inplace=True)

   #update the SQL table
   table_name= "disease__nodes"
   updated_column= "synonyms"
   unique_column= "name"
   update_column_in_sql_table(table_name, updated_column, unique_column, df)
   print("Data updated in the MySQL table.")
   
if __name__ == '__main__':
 conn, c= connect_to_sql()
 df=fetch_disease_nodes(c)
 process_df(df)
