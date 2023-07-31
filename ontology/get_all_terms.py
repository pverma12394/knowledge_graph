import requests
from requests import Session
import pandas as pd
import ast,json
import os
    
class PollySession(Session):
    def __init__(self, REFRESH_TOKEN):
        Session.__init__(self)
        self.headers = {
            "Content-Type": "application/vnd.api+json",
            "Cookie" : f"refreshToken={REFRESH_TOKEN}",
            "User-Agent" : "polly-python/"
        }

class OmixAtlas: 
    polly_api_url= {"dev":"dev","test":"test","prod":""}
    
    def __init__(self, token: str, polly_env) -> None:
        self.session = PollySession(token)
        self.base_url = "https://v2.api.{}polly.elucidata.io/v1/omixatlases".format(self.polly_api_url[polly_env])

    def get_all_omixatlas(self): 
        url = self.base_url
        #params = {"summarize": "true"}
        response = self.session.get(url) #,params=params)
        return response.json()

    def omixatlas_summary(self, key: str):
        url = f"{self.base_url}/{key}"
        #params = {"summarize": "true"}
        response = self.session.get(url) #,params=params)
        #error_handler(response)
        return response.json()

def get_all_oas(library_client):
    ao = library_client.get_all_omixatlas()
    #print("all oa response:",ao)
    if "data" not in ao or not ao["data"]:
        print("Failed to fetch all OAs.. Kindly specify OA name-id map explicitly in repo_id_index_variable")
        print(ao,end="\n\n")
    #print(json.dumps(ao,indent=2),"\n\n")
    repo_ids= [int(ind["attributes"]["repo_id"]) for ind in ao["data"] if "files" in ind["attributes"]["v2_indexes"]]
    repo_indexes= [ind["attributes"]["v2_indexes"]["files"] for ind in ao["data"] if "files" in ind["attributes"]["v2_indexes"]]
    repo_id_index= {k:v for k,v in zip(repo_ids,repo_indexes)}
    return(repo_id_index) 

def post_polly_request(index, polly_env, es_query, elastic_api_ver="v2"): 
    cookie = os.environ.get('PROD_COOKIE')
    
    polly_api_url= {"dev":"dev","test":"test","prod":""}
    elastic_api_url= {"v1":"","v2":"v2/"}
    
    ELASTIC_URL = "https://api.datalake.discover.{}polly.elucidata.io/elastic/{}".format(polly_api_url[polly_env],\
                                                                                          elastic_api_url[elastic_api_ver])  
    endpoint='_search'
    method = 'POST'
    kwargs = {
        'url': ELASTIC_URL+index+"/"+endpoint,
        'method': method,
        'headers': {
            'Content-Type': 'application/vnd.api+json',
            'Accept': 'application/vnd.api+json',
            'Cookie': cookie
        },
        'data': json.dumps(es_query)}
    resp = requests.request(**kwargs)
    #print("resp text--", resp, resp.text)
    #if int(resp.status_code)!=200:
    #    print(resp.text)
    
    resp_dict = {
        "status": None,
        "errors": None,
        "primary_data": None,
        "included_data": None,
        "links": None,
        "meta": None
    }
    resp_dict['status'] = resp.status_code
    if resp.status_code!=200:
        print("Failed to make post request:-\n",resp.status_code,"\n",resp.text)
        #return(False)
    if resp.text:
        resp_dict['primary_data'] = json.loads(resp.text)
        
    return resp_dict['primary_data']

def get_all_terms_polly(field, index, polly_env, elastic_api_ver="v2"):
    if not field.startswith("curated_"):
        field= "curated_" + field
    try:
        all_terms_query = {"size":0,"query":{"bool":{"must":[{"exists":{"field":"dataset_id"}}]}},"aggs":{field:{"terms":{"field":field+".keyword","size":10000}}}}
        resp_dict = post_polly_request(index, polly_env, all_terms_query,elastic_api_ver)
        if not resp_dict:
            return False
        all_terms = set([bk["key"] for bk in resp_dict["aggregations"][field]["buckets"]])
        #print("all terms=",len(all_terms))
        return all_terms
    except Exception as e:
        print("Exception in get_all_terms:-",e)
        print("resp=",resp_dict)
        raise e

def get_all_cell_lines_polly(field, index, polly_env, elastic_api_ver="v2"):
    if not field.startswith("curated_"):
        field= "curated_" + field
    
    all_terms = set(); sort_last_hit_val= None
    all_terms_query = {"size":10000,"_source":[field],"query":{"bool":{"must":[{"exists":{"field":"dataset_id"}}]}},"sort":[{"dataset_id.keyword":"asc"}]}
    try:
        while True:
            if sort_last_hit_val:
                all_terms_query["search_after"]= sort_last_hit_val
            resp_dict = post_polly_request(index, polly_env, all_terms_query,elastic_api_ver)
            if len(resp_dict['hits']['hits'])==0:
                break
            sort_last_hit_val= resp_dict['hits']['hits'][-1]["sort"]
            z= { val for hit in resp_dict['hits']['hits'] for val in hit["_source"].get(field,[]) } #if val not in {'nan','none'}
            #print(f"got {len(z)} cell_lines")
            all_terms|= z 
    except Exception as e:
        print(f"Exception in get_all_cell_lines_polly:-\n{e}\nEs_resp:-\n{resp_dict}")
        return False
    #print("all terms=",len(all_terms))
    return all_terms

# if __name__ == "__main__":
#     refresh_token = os.environ.get('PROD_REFRESH_TOKEN')
#
#     library_client= OmixAtlas(refresh_token,polly_env='prod')
#     repo_id_index= get_all_oas(library_client)
#     #repo_id_index= {1644896537390: 'tcga_files', 1659681281379: 'multiple_oa_files', 1643359804137: 'geo_files', 1659419095067: 'demo_oa_2_files', 1653564741851: 'test_boolean_type_support_files'}
#     print("All repos:-\n",repo_id_index,end="\n\n")

