This repo contains code for creating a Knowledge Graph(KG) from different data sources.

### Setup
* Install the packages from requirements.txt  
	 `pip install -r requirements.txt`
* Install and setup MySQL for your operating system  
	- For mac, install mysql on cli : `brew install mysql`  
	- Create a database named `kgdb` using the following commands
		- `> mysql`
		- `> CREATE DATABASE kgdb;`
		- `> CREATE USER 'neo4j'@'localhost' IDENTIFIED WITH mysql_native_password BY 'my-strong-password-here';`
		- `> GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX, DROP, ALTER, CREATE TEMPORARY TABLES, LOCK TABLES ON kgdb.* TO 'neo4j'@'localhost';`
		- `> GRANT FILE ON *.* TO 'neo4j'@'localhost';`
		- `exit`
		- To import the data tables in the empty db  
			- `mysql -u neo4j -p kgdb < semantics/data/kgdb.sql`
			- Enter password on prompt
			- Test if the tables are successfully imported, `mysql -u neo4j`
				- `USE kgdb`
				- `SHOW TABLES;`
* (Optional) Also install a mysql connector (based on your operating system). 
* Then install ontop cli based on your operation system. Follow the steps in [this](https://ontop-vkg.org/guide/cli.html#setup-ontop-cli) tutorial to properly install and setup ontop cli.
	* Check if ontop has been properly installed by using the below command
		
			ontop --version
		
* Install ontop-protege based on your operating system from [here](https://sourceforge.net/projects/ontop4obda/files/ontop-4.2.1/)
	* Open the owl file in protege (File > Open > select the file)
	* In Window > Tabs, select Ontop Mappings. This creates the Ontop Mappings tabs. Click on the tab.
	* In Connection parameters tab, enter the `username` and `password` for the database.
	* On mac, setup jdbc plugin on protege, from Protege -> Preferences -> JDBC Drivers -> Add.
	- Select the driver from folder, `semantics/jdbc/mysql-connector-java-8.0.29.jar`
	* In Class name, enter ***com.mysql.jdbc.Driver*** and select the location to the jdbc file and click Ok.
* Update the .env and semantics/BioMedOnto.properties files
- Test the Connection, making sure the credentials are correct.

### Directory structure
The main directory contains 4 sub-directories

* ontologies - Contains the data like ontology files, csv files etc.
* ontology - Contains the codes for extracting, processing and saving the data to the database.
* scripts - Contains the codes for creating owl and mappings files and other supportive functions.
* semantics - Contains the mapping, ontology and properties files and materialized graph (ttl file).

The directory also contains a main file which runs all the code.

### The Code base
For adding a new entity to the knowledge graph, a parsing script has to added to ontology folder. The script should 

* extract the data(node and relation) to a data frame and save it to the database (using save_to_db() function)
* Add the name of the node table to the database (using add_node_table_name() function)
* Add the name of relation table to the database (using add_table_name() function)
* Also add a function for running the script to the OntologyGroup.start() in main.py
* After the database has been updated, run the update_mappings() and update_owl() functions for generating a mappings file and ontology file.
* Then run the materialize command to materialize the knowledge graph. A name for the ttl file can be provided as a command line argument.

After the KG has been materialized, it can imported into neo4j. For importing the KG,

* The n10s plugin has to be installed before launching the database.
* After the database is opened, the following queries have to be executed for setting up the environment for importing the KG
		
		
		CALL n10s.graphconfig.init();
		CREATE CONSTRAINT n10s_unique_uri ON (r:Resource)
		ASSERT r.uri IS UNIQUE;
		call n10s.graphconfig.init( { handleMultival: "ARRAY", keepLangTag: false, handleRDFTypes: "LABELS" ,handleVocabUris: "SHORTEN" })
		
		
* Then the KG can be imported into neo4j be executing the following query

		CALL n10s.rdf.import.fetch("file://{file_path}","{file_format}")

#### Conventions to be followed

* The name of the node table has to be ***<entity_name>__nodes***. For example, ***drug__nodes***, ***cell_line__nodes*** etc.
* The name of the relation table has to be ***<entity_name>__<relation_name>__relation***. For example, ***tissue__sampled_from__relation*** etc.
* The name of a relation has to be unique even though the relation is between different entities.
* The node_table_names table has 4 columns
	* table_name - name of the table
	* type - type of entity. For example, tissue, drug, cell_line etc
	* properties - the values stored for each node. For example, tissue contains tissue_id, name,synonyms etc.
	* mapping - indicates whether a mapping has been created in the mappings file. Takes values mapped/not_mapped.
		
			add_node_table_name(['tissue__nodes','tissue','tissue_id;name;definition;synonyms;type','not_mapped'])
		
* The rel_table_name contains 5 columns.
	* table_name - name of the table
	* source_type - type of entity from which the edge starts
	* target_type - type of entity to which the edge points
	* relation_name - name of the relation
	* mapping - indicates whether a mapping has been created in the mappings file. Takes values mapped/not_mapped.
	
			add_table_name(["pathway__enriched_in__relation",'pathway','disease','enriched_in','not_mapped']) 
		is a relation from pathway node to disease node.