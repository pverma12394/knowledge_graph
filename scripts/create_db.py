import os
import pandas as pd
import mysql.connector
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()
engine = create_engine("mysql+pymysql://{user}:{pw}@localhost/{db}"
                       .format(user=os.environ.get("mysql_user"),
                               pw=os.environ.get("mysql_pwd"), db=os.environ.get("mysql_db")))


def save_to_db(df, table_name):
    # print(f"Saved df to {table_name}")  # uncomment next line
    df.to_sql(table_name, con=engine, if_exists='replace', chunksize=1000,
              index=False)  # if_exists = 'add' for updation


def read_from_db(table_name):
    df = pd.read_sql(table_name, engine)
    return df


def get_tables_list():
    mydb = mysql.connector.connect(
        host=os.environ.get("mysql_host"),
        user=os.environ.get("mysql_user"),
        password=os.environ.get("mysql_pwd"),
        database=os.environ.get("mysql_db"),
        # auth_plugin='mysql_native_password'
    )

    mycursor = mydb.cursor()

    mycursor.execute("Show tables;")

    myresult = mycursor.fetchall()
    lst = [tup[0] for tup in myresult]
    # print(lst)
    return lst


def add_table_name(row):
    df1 = pd.DataFrame({'table_name': [row[0]], 'source_type': [row[1]], 'target_type': [row[2]],
                        'relation_name': [row[3]], 'mapping': [row[4]]})
    if 'rel_table_names' in get_tables_list():
        df = read_from_db("rel_table_names")
        if row[0] not in list(df['table_name']):
            df = pd.concat([df, df1], ignore_index=True)
            save_to_db(df, "rel_table_names")
    else:
        save_to_db(df1, "rel_table_names")


def add_node_table_name(row):
    """
        The columns of the table are, table_name(str),type(str),properties(str), mapping(str)
    """
    df1 = pd.DataFrame({'table_name': [row[0]], 'type': [row[1]], 'properties': [row[2]], 'mapping': [row[3]]})

    if 'node_table_names' in get_tables_list():
        df = read_from_db("node_table_names")
        if row[0] not in list(df['table_name']):
            df = pd.concat([df, df1], ignore_index=True)
            save_to_db(df, "node_table_names")
        else:
            ind = df.index[df['table_name'] == row[0]].tolist()[0]
            df = df.drop(ind)
            df = pd.concat([df, df1], ignore_index=True)
            save_to_db(df, "node_table_names")
    else:
        save_to_db(df1, "node_table_names")


if __name__ == '__main__':
    print("Hello")
    lst = get_tables_list()

    for table in lst:
        df = read_from_db(table)
        print(df.head(3))
        print('\n')
