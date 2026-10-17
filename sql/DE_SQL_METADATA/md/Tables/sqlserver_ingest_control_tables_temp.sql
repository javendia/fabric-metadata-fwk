CREATE TABLE [md].[sqlserver_ingest_control_tables_temp]
(
  [sqlserver_source_id] INT NOT NULL,
  [source_name] VARCHAR(150) NOT NULL,
  [source_schema] VARCHAR(50) NOT NULL,
  [source_table_name] VARCHAR(150) NOT NULL,
  [source_table_columns] VARCHAR(800) NOT NULL,
  [primary_key] VARCHAR(150) NOT NULL,
  [target_table_name] AS (CONCAT([source_name], '_', [source_table_name])) PERSISTED,
  [target_root_path] VARCHAR(800) NOT NULL,
  [target_table_path] AS (CONCAT([target_root_path], '/', [source_schema], '_', [source_table_name])) PERSISTED,
  [load_pattern_id] SMALLINT NOT NULL DEFAULT(1), -- 1 = full load, 2 = incremental load
  [enable_flag] BIT NOT NULL DEFAULT(0), -- 1 = enabled, 0 = disabled
)