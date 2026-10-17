# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse_name": "",
# META       "default_lakehouse_workspace_id": ""
# META     },
# META     "environment": {
# META       "environmentId": "5b536ce4-9e39-8d79-4ac0-8d134aef92e1",
# META       "workspaceId": "00000000-0000-0000-0000-000000000000"
# META     }
# META   }
# META }

# MARKDOWN ********************

# **silver_orchestrator**
# ---
# Notebook in charge of controlling the execution, through the use of the notebook that stores the Entity class, of the entities of the metadata table **_enrich_control_**

# PARAMETERS CELL ********************

workspace_id = ""
lakehouse_id = ""
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

spark.conf.set("spark.sql.parquet.vorder.enabled","false")
spark.conf.set("spark.databricks.delta.optimizeWrite.enabled","false")
spark.conf.set("spark.databricks.delta.optimizeWrite.binSize","157m")
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

entities_arr = json.loads(entities)

if entities_arr:
    for row in entities_arr:
        
        entity_call=f"{{\
                        \"name\":\"{row['entity']}\",\
                        \"path\": \"DE_NB_ENTITY\",\
                        \"timeoutPerCellInSeconds\": 3600,\
                        \"args\": {{ \
                            \"useRootDefaultLakehouse\": true,\
                            \"layer_name\": \"silver\",\
                            \"control_workspace_id\": \"\",\
                            \"workspace_id\": \"{workspace_id}\",\
                            \"lakehouse_id\": \"{lakehouse_id}\",\
                            \"entity_name\": \"{row['entity']}\",\
                            \"primary_key\": \"{row['primary_key']}\",\
                            \"load_pattern\": {row['load_pattern_id_silver']}\
                        }}\
                    }}"
        
        if i == 0:
            DAG_entities = entity_call
        else:
            DAG_entities = DAG_entities + "," + entity_call
        
        i = 1
    
    DAG = DAG_start + DAG_entities + DAG_end
    
try:
    print(f"*INFO*: ▶️ Starting silver synchronization...")
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
