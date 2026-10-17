# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# MARKDOWN ********************

# # dim_Calendario

# MARKDOWN ********************

# ## Parameters

# PARAMETERS CELL ********************

gold_workspace_id = ""
gold_lakehouse_id = ""
from_date = ""

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql.functions import *
from datetime import datetime, timedelta

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# ## Variables

# CELL ********************

parent_source_path = f"abfss://{gold_workspace_id}@onelake.dfs.fabric.microsoft.com/{gold_lakehouse_id}/Files/02_SILVER/"
parent_destination_path = f"abfss://{gold_workspace_id}@onelake.dfs.fabric.microsoft.com/{gold_lakehouse_id}/Tables/"

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

dim_calendario_destination_full_path = parent_destination_path + "dim_Calendario"
# limits
startdate = datetime.strptime(from_date, "%Y-%m-%d")
enddate = (datetime.now() + timedelta(days=365)).replace(month=12, day=31)

# explode dates between the defined boundaries into one column
start = int(startdate.timestamp())
stop  = int(enddate.timestamp())
dim_calendario = spark.range(start, stop, 60*60*24).select(col("id").cast("timestamp").cast("date").alias("fecha"))

dim_calendario = dim_calendario.withColumn("id", date_format("fecha", "yyyyMMdd").cast("int")) \
        .withColumn("anyo", year("fecha")) \
        .withColumn("nro_cuatrimestre", to_csv(struct("fecha"), {"dateFormat": "QQQ", "locale": "es"})) \
        .withColumn("cuatrimestre", to_csv(struct("fecha"), {"dateFormat": "QQQQ", "locale": "es"})) \
        .withColumn("nro_mes", month("fecha")) \
        .withColumn("nro_mes_texto", date_format("fecha", "MM")) \
        .withColumn("mes_corto", to_csv(struct("fecha"), {"dateFormat": "LLL", "locale": "es"})) \
        .withColumn("mes", to_csv(struct("fecha"), {"dateFormat": "LLLL", "locale": "es"})) \
        .withColumn("semana_anyo", weekofyear("fecha")) \
        .withColumn("semana_anyo_texto", lpad(weekofyear("fecha"), 2, '0')) \
        .withColumn("dia_semana", dayofweek("fecha")) \
        .withColumn("dia_semana_texto", lpad(dayofweek("fecha"), 2, '0')) \
        .withColumn("nombre_dia_semana_corto", to_csv(struct("fecha"), {"dateFormat": "EEE", "locale": "es"})) \
        .withColumn("nombre_dia_semana", to_csv(struct("fecha"), {"dateFormat": "EEEE", "locale": "es"})) \

dim_calendario.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(dim_calendario_destination_full_path)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
