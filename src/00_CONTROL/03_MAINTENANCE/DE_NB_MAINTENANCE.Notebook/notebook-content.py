# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "jupyter",
# META     "jupyter_kernel_name": "python3.11"
# META   },
# META   "dependencies": {
# META     "environment": {
# META       "environmentId": "5b536ce4-9e39-8d79-4ac0-8d134aef92e1",
# META       "workspaceId": "00000000-0000-0000-0000-000000000000"
# META     }
# META   }
# META }

# MARKDOWN ********************

# # Maintenance
# This workbook deals with maintenance tasks, such as compacting and reducing parquet files, on the tables of the existing data lakes in the solution.

# MARKDOWN ********************

# ## Parameters

# PARAMETERS CELL ********************

bronze_workspace_id = ""
bronze_lakehouse_id = ""
silver_workspace_id = ""
silver_lakehouse_id = ""
gold_workspace_id = ""
gold_lakehouse_id = ""

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# ## Dependencies

# CELL ********************

%pip install semantic-link-labs ms-fabric-cli --q

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

import sempy_labs as labs
import struct
import sqlalchemy
import pyodbc
import polars as pl

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# ## Variables

# CELL ********************

SQL_COPT_SS_ACCESS_TOKEN = 1256
BRONZE_QUERY = "SELECT [entity] FROM [md].[enrich_control] WHERE [active_for_load_bronze] = 1"
SILVER_QUERY = "SELECT [entity] FROM [md].[enrich_control] WHERE [active_for_load_silver] = 1"
GOLD_QUERY = "SELECT [entity_name] FROM [md].[curated_control] WHERE [active_for_load_gold]= 1"
RETENTION_PERIOD = 168

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# ## Functions

# CELL ********************

def read_sql_table(server: str, database: str, query: str) -> list:
    """
    Runs a query against a database.

    Parameters
    ----------
    server : str
        Endpoint to the server.
    database : str
        The SQL Database name and ID.
    query : str
        Select statement.
    """
    conn_string = f"Driver={{ODBC Driver 18 for SQL Server}};Server={server};Database={{{database}}}"
    token = notebookutils.credentials.getToken('https://analysis.windows.net/powerbi/api').encode("UTF-16-LE")
    token_struct = struct.pack(f'<I{len(token)}s', len(token), token)

    engine = sqlalchemy.create_engine("mssql+pyodbc://", creator=lambda: pyodbc.connect(conn_string, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct}))
    with engine.connect() as alchemy_connection:
        df = pl.read_database(query, alchemy_connection) # runs the query against the server/database
        return pl.Series(df.select(pl.nth(0))).to_list() # converts entities column to a list

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# MARKDOWN ********************

# ## Execution

# CELL ********************

# Uses user identity to work with Fabric CLI
token = notebookutils.credentials.getToken('pbi')
os.environ['FAB_TOKEN'] = token
os.environ['FAB_TOKEN_ONELAKE'] = token

# Gets the workspace name where the notebook is located. By definition, it is same of the metadata database
workspace = notebookutils.runtime.context["currentWorkspaceName"]

# Lists SQL Database connection properties
connection_info = !fab -c "get {workspace}.Workspace/DE_SQL_METADATA.SQLDatabase -q properties.connectionInfo"

# Splits SQL Database connection string
properties = connection_info[0].split(';')
metadata_server = properties[0].split('=')[1]
metadata_database = properties[1].split('=')[1]

# 🥉 BRONZE

print(f"*INFO*: 🟤 Starting bronze maintenance...")

# Gets entities
bronze_entities = read_sql_table(metadata_server, metadata_database, BRONZE_QUERY)
# OPTIMIZE (https://docs.delta.io/latest/optimizations-oss.html)
labs.lakehouse.optimize_lakehouse_tables(bronze_entities, bronze_lakehouse_id, bronze_workspace_id)
# VACUUM (https://docs.delta.io/latest/delta-utility.html#remove-files-no-longer-referenced-by-a-delta-table)
labs.lakehouse.vacuum_lakehouse_tables(bronze_entities, bronze_lakehouse_id, bronze_workspace_id, RETENTION_PERIOD)

# 🥈 SILVER

print(f"*INFO*: ⚪ Starting silver maintenance...")

# Gets entities
silver_entities = read_sql_table(metadata_server, metadata_database, SILVER_QUERY)
labs.lakehouse.optimize_lakehouse_tables(silver_entities, silver_lakehouse_id, silver_workspace_id)
labs.lakehouse.vacuum_lakehouse_tables(silver_entities, silver_lakehouse_id, silver_workspace_id, RETENTION_PERIOD)

# 🥇 GOLD

print(f"*INFO*: 🟡 Starting gold maintenance...")

# Gets entities
gold_entities = read_sql_table(metadata_server, metadata_database, GOLD_QUERY)
labs.lakehouse.optimize_lakehouse_tables(gold_entities, gold_lakehouse_id, gold_workspace_id)
labs.lakehouse.vacuum_lakehouse_tables(gold_entities, gold_lakehouse_id, gold_workspace_id, RETENTION_PERIOD)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }
