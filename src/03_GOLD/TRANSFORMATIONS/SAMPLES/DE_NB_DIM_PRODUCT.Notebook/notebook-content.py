# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "2a8e80b2-3ff9-4aa3-8840-d24d0c97032c",
# META       "default_lakehouse_name": "DE_LH_GOLD",
# META       "default_lakehouse_workspace_id": "ca7b88ec-a3e6-48f7-9117-29cc5b7946a8",
# META       "known_lakehouses": [
# META         {
# META           "id": "2a8e80b2-3ff9-4aa3-8840-d24d0c97032c"
# META         }
# META       ]
# META     },
# META     "environment": {
# META       "environmentId": "5b536ce4-9e39-8d79-4ac0-8d134aef92e1",
# META       "workspaceId": "00000000-0000-0000-0000-000000000000"
# META     }
# META   }
# META }

# MARKDOWN ********************

# ## Variables

# CELL ********************

parent_source_path = "Files/02_SILVER/"

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# MARKDOWN ********************

# #### dim_Product

# CELL ********************

dim_product_source_path = parent_source_path + "CONTOSO_Product"
dim_product_view_name = "etl_dim_product"

sql_query = f"""

CREATE OR REPLACE VIEW {dim_product_view_name} AS
        SELECT
                ProductKey AS sk_dim_product,
                ProductKey AS bk_dim_product,
                ProductCode,
                ProductName,
                Manufacturer,
                Brand,
                Color,
                WeightUnit,
                Weight,
                Cost,
                Price,
                SubcategoryKey,
                SubCategoryName,
                CategoryKey,
                CategoryName
        FROM
                delta.`{dim_product_source_path}`
"""
dim_product = spark.sql(sql_query)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
