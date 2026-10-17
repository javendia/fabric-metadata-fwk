# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "environment": {
# META       "environmentId": "5b536ce4-9e39-8d79-4ac0-8d134aef92e1",
# META       "workspaceId": "00000000-0000-0000-0000-000000000000"
# META     }
# META   }
# META }

# MARKDOWN ********************

# **gold_orchestrator**
# ---
# Notebook in charge of controlling the execution, through the use of the notebook that stores the Entity class, of the entities of the metadata table **_curated_control_**

# CELL ********************

# MAGIC %%configure
# MAGIC { 
# MAGIC     "defaultLakehouse": {
# MAGIC         "name":
# MAGIC         {
# MAGIC             "parameterName": "lakehouse_name",
# MAGIC             "defaultValue": ""
# MAGIC         },
# MAGIC         "id":
# MAGIC         {
# MAGIC             "parameterName": "lakehouse_id",
# MAGIC             "defaultValue": ""
# MAGIC         },
# MAGIC         "workspaceId":
# MAGIC         {
# MAGIC             "parameterName": "workspace_id",
# MAGIC             "defaultValue": ""
# MAGIC         }
# MAGIC     }
# MAGIC }

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# PARAMETERS CELL ********************

workspace_id = ""
lakehouse_id = ""
lakehouse_name = ""
entities = ""

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import json

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

spark.conf.set("spark.sql.parquet.vorder.enabled","true")
spark.conf.set("spark.databricks.delta.optimizeWrite.enabled","true")
spark.conf.set("spark.databricks.delta.optimizeWrite.binSize","1gb")
spark.conf.set("spark.microsoft.delta.snapshot.driverMode.enabled", True)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark",
# META   "frozen": false,
# META   "editable": true
# META }

# CELL ********************

i = 0
DAG_start="""{
    "activities": ["""

DAG_end="""],
    "timeoutInSeconds": 7200,
    "concurrency": 10
}"""

if entities:
    for row in json.loads(entities):
        
        entity_call=f"{{\
                        \"name\":\"{row['entity_name']}\",\
                        \"path\": \"DE_NB_ENTITY\",\
                        \"timeoutPerCellInSeconds\": 3600,\
                        \"args\": {{ \
                            \"useRootDefaultLakehouse\": true,\
                            \"layer_name\": \"gold\",\
                            \"control_workspace_id\": \"\",\
                            \"workspace_id\": \"{workspace_id}\",\
                            \"lakehouse_id\": \"{lakehouse_id}\",\
                            \"transformation_notebook\": \"{row['transformation_notebook']}\",\
                            \"sql_view\": \"{row['sql_view']}\",\
                            \"entity_name\": \"{row['entity_name']}\",\
                            \"primary_key\": \"{row['primary_key']}\",\
                            \"load_pattern\": {row['load_pattern_id_gold']}\
                        }}"
        if row['dependencies'] is None or row['dependencies'] == "":
            entity_call += '}'
        else:
            entity_call += f",\"dependencies\": [{row['dependencies']}]}}"

        if i == 0:
            DAG_entities = entity_call
        else:
            DAG_entities = DAG_entities + "," + entity_call
        i = 1
    
    DAG = DAG_start + DAG_entities + DAG_end
    print(DAG)

try:
    print(f"*INFO*: ▶️ Starting gold synchronization...")
    notebookutils.notebook.runMultiple(
        DAG, {"displayDAGViaGraphviz": True, "DAGLayout": "spectral"}
    )
except Exception as err:
    print(f"*ERROR*: ❌ Unable to complete the DAG execution, error message: {err=}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
