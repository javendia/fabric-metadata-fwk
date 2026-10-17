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
# META     }
# META   }
# META }

# CELL ********************

from datetime import datetime
from uuid import UUID
from pyspark.sql.functions import *
import re
from pyspark.sql.window import Window
import glob
import sempy.fabric as fabric
import notebookutils

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# PARAMETERS CELL ********************

control_workspace_id = ""
workspace_id = ""
layer_name = ""
lakehouse_id = ""
file_mask = ""
entity_name = ""
transformation_notebook = ""
sql_view = ""
primary_key = ""
load_pattern = 1

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

class Entity:
    """
    Class representing an entity of a given layer.

    ...

    Attributes
    ----------
    workspace_id : UUID
        GUID of the workspace where the entity store is located.
    layer_name : str
        Layer name, silver or gold.
    lakehouse_in_id : UUID
        Data Lake's GUID where the entity has been ingested.
    lakehouse_out_id : UUID
        Data Lake's GUID where the entity has been written.
    source_path : str
        Relative path to the ingested entity files.
    entity_name : str
        Entity name.
    entity : DataFrame
        Represents the content of the entity.
    primary_key : str
        Primary key of the entity.
    load_pattern : str
        Load type.

    Methods
    -------
    _check_if_directory_or_table_exists()
        Checks if a directory exists.
    _move_processed_files()
        Moves the processed files to the Processed folder.
    _check_if_files_to_process()
        Checks if there are files to process.
    _clean_column_names()
        Removes special characters in the entity column names.
    _remove_duplicates()
        Deduplicates records by the defined primary key.
    _check_if_table_exists()
        Checks if the target entity exists.
    _trim_columns()
        Checks if the target entity exists.
    """

    def __init__(self, layer_name: str, control_workspace_id: UUID, workspace_id: UUID, lakehouse_id: UUID, file_mask: str, \
                    entity_name: str, transformation_notebook: str, sql_view: str, primary_key: str, load_pattern: int):
        self.layer_name = layer_name
        self.control_workspace_id = control_workspace_id
        self.workspace_id = workspace_id
        self.lakehouse_id = lakehouse_id
        self.entity_name = entity_name
        self.file_mask = file_mask
        self.default_path = "/lakehouse/default/Files/"
        self.parent_path = f"abfss://{self.workspace_id}@onelake.dfs.fabric.microsoft.com/{self.lakehouse_id}/Files/"
        
        # Define source path based on layer
        if self.layer_name == "bronze":
            self.source_path = self.parent_path + self.file_mask
        elif self.layer_name == "silver":
            self.source_path = f"{self.parent_path}01_BRONZE/{self.entity_name}"
        elif self.layer_name == "gold":
            self.transformation_notebook = transformation_notebook
            self.source_path = sql_view
        self.destination_path = f"abfss://{self.workspace_id}@onelake.dfs.fabric.microsoft.com/{self.lakehouse_id}/Tables/{self.entity_name}"

        # Initialize an empty entity
        self.entity = spark.createDataFrame([], StructType([]))
        self.primary_key = primary_key
        self.load_pattern = load_pattern
    
    def _check_if_directory_or_table_exists(self, path: str) -> bool:
        """
        Checks if a directory or table exists at the specified path.
        Returns True if exists, False otherwise.
        """
        return notebookutils.fs.exists(path)

    def _move_processed_files(self, files) -> None:
        """
        Moves processed files to the 'Processed' folder and deletes pending subfolders.
        
        Args
        ----
            files (list): List of file paths to move.
        """
        for file in files:
            # Move file from Pending to Processed
            notebookutils.fs.mv(file, file.replace("Pending", "Processed"), True, True)

        # Get unique pending subfolder paths
        pending_paths = list(dict.fromkeys(map(lambda path: path[:path.rfind('/')-5], files)))

        for path in pending_paths:
            # Delete the pending folder
            notebookutils.fs.rm(path, True) # Delete folder
    
    def _clean_column_names(self) -> None:
        """
        Removes special characters in the entity column names.
        """
        for column in self.entity.columns:
            # Replace accented characters
            column_aux = re.sub(r'[ú|ù|ü|û]','u',  
                            re.sub(r'[ó|ò|ö|ô]' ,'o', 
                            re.sub(r'[í|ì|ï|î]'  ,'i',  
                            re.sub(r'[é|è|ë|ê]','e', 
                            re.sub(r'[á|à|ä|â]','a',column)))))
            # Replace non-alphanumeric characters with '_'
            new_column = re.sub(r'[^a-zA-Z0-9]', '_', column_aux)
            self.entity = self.entity.withColumnRenamed(column, new_column)
    
    def _remove_duplicates(self) -> None:
        """
        Deduplicates records by the defined primary key.
        """
        if self.primary_key and self.primary_key != "N/A":
            pks = [column.strip() for column in self.primary_key.split(',')]
            window = Window().partitionBy(pks).orderBy(col("loaded_at").desc())
            self.entity = self.entity.withColumn("row_number", row_number().over(window)).filter(col("fila") == 1) 
            self.entity = self.entity.drop("row_number")

    def _trim_columns(self) -> None:
        """
        Removes leading and trailing spaces from columns of string type in the entity DataFrame.
        """
        for column in self.entity.columns:
            if self.entity.schema[column].dataType == StringType():
                self.entity = self.entity.withColumn(column, trim(col(column)))

    def _write(self) -> None:
        """
        Writes entity as delta table using its load pattern.
        """
        print(f"*INFO*: ▶️ Writing | {self.entity_name} | load_pattern | {self.load_pattern}")

        if self.load_pattern == 1 or not self._check_if_directory_or_table_exists(self.destination_path):
            self.entity.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(self.destination_path)
        elif self.load_pattern == 3:
            self.entity.write.format("delta").mode("append").save(self.destination_path)
    
    def persist(self) -> None:
        """
        Synchronizes pending files for the bronze layer: reads, cleans, deduplicates, and writes data.
        Executes pre-processing notebooks if they exist.
        """
        start = datetime.now()
        print(f"*INFO*: ▶️ Starting | bronze | {self.entity_name} | {start}")

        # Find pending files in the default path and map to ABFS path
        parquet_paths = list(map(lambda s: self.parent_path + s.replace(self.default_path, ""), 
                                glob.glob(self.default_path + self.file_mask, recursive=True)))
        
        if parquet_paths:
            
            # Find pending files in the default path and map to ABFS path
            control_ws_items_list = fabric.list_items(workspace=self.control_workspace_id)
            notebooks_pre_execution = spark.createDataFrame(control_ws_items_list).select("Display Name")

            search_str = f"DE_NB_BRONZE_PRE_EXECUTION_{self.entity_name}"
            notebooks_pre_execution = notebooks_pre_execution.filter(notebooks_pre_execution["Display Name"].contains(search_str))

            if notebooks_pre_execution.count() > 0:
                for notebook in notebooks_pre_execution.collect():
                    # Run the pre-execution notebook
                    notebookutils.notebook.run(
                        notebook["Display Name"], 
                        90, 
                        {
                            "useRootDefaultLakehouse": True,
                            "workspace_id": f"{self.workspace_id}",
                            "lakehouse_id": f"{self.lakehouse_id}",
                            "parquet_paths": f"{','.join(parquet_paths)}"
                        },
                        self.control_workspace_id
                    )

            # Read all pending files
            self.entity = spark.read.parquet(*parquet_paths)
            rows = self.entity.count()

            if rows > 0: # Checks if dataframe is empty
                self._clean_column_names()
                self._remove_duplicates()

                print(f"*INFO*: ✅ {rows} rows readed. Pending to write to the destination entity {self.entity_name}")

                # Writes destination table
                self._write()

                print(f"*INFO*: ✅ {rows} rows has been written in {self.entity_name}")

                # Move pending files to the processed folder
                self._move_processed_files(parquet_paths)
        else:
            print(f"*INFO*: ▶️ No pending files to process...")
    
    def enrich(self) -> None:
        """
        Synchronizes data for the silver layer: reads, trims, and writes data to the destination table.
        """
        start = datetime.now()
        print(f"*INFO*: ▶️ Starting | silver | {self.entity_name} | {start}")

        if self._check_if_directory_or_table_exists(self.source_path):
            self.entity = spark.read.format("delta").load(self.source_path)
            rows = self.entity.count()
            
            if rows > 0: # Checks if dataframe is empty
                self._trim_columns()

                self.entity = self.entity.withColumn("loaded_at", to_timestamp(col("loaded_at"), "yyyy-MM-dd'T'HH:mm:ss"))

                print(f"*INFO*: ✅ {rows} rows readed. Pending to write to the destination entity {self.entity_name}")
                print(f"*INFO*: ▶️ Writing | {self.entity_name} | load_pattern | {self.load_pattern}")

                # Writes destination table
                self._write()

                print(f"*INFO*: ✅ {rows} rows has been written in {self.entity_name}")
            else:
                print(f"*INFO*: ▶️ No rows in {self.entity_name} entity.")
        else:
            print(f"*INFO*: ▶️ Entity {self.entity_name} not exists.")

    def curate(self) -> None:
        """
        Synchronizes data for the gold layer: reads from a SQL view and writes data to the destination table.
        """
        start = datetime.now()
        print(f"*INFO*: ▶️ Starting | gold | {self.entity_name} | {start}")

        # Runs the notebook where the transformation view is created
        notebookutils.notebook.run(self.transformation_notebook, 3600)
        
        # Eexcutes the view previously created
        sql_query = f"SELECT * FROM {self.source_path}"
        self.entity = spark.sql(sql_query)

        rows = self.entity.count()

        if rows > 0: # Checks if dataframe is empty
            print(f"*INFO*: ✅ {rows} rows readed. Pending to write to the destination entity {self.entity_name}")
            
            # Writes destination table
            self._write()

            print(f"*INFO*: ✅ {rows} rows has been written in {self.entity_name}")
        else:
            print(f"*INFO*: ▶️ No rows in {self.entity_name} entity.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

entity = Entity(layer_name, control_workspace_id, workspace_id, lakehouse_id, file_mask, entity_name, transformation_notebook, sql_view, primary_key, load_pattern)
if layer_name == "bronze":
    entity.persist()
elif layer_name == "silver":
    entity.enrich()
elif layer_name == "gold":
    entity.curate()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
