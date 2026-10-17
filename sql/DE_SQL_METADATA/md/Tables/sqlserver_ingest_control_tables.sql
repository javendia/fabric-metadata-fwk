CREATE TABLE [md].[sqlserver_ingest_control_tables]
(
  [sqlserver_source_id] INT NOT NULL,
  [source_table_name] VARCHAR(150) NOT NULL,
  [source_table_columns] VARCHAR(800) NOT NULL,
  [primary_key] VARCHAR(150) NOT NULL,
  [target_table_name] VARCHAR(150) NOT NULL,
  [target_table_path] VARCHAR(800) NOT NULL,
  [file_extension] VARCHAR(50) NOT NULL DEFAULT('.parquet'),
  [load_pattern_id] INT NOT NULL DEFAULT(1), -- 1 = full load, 2 = incremental load
  [enable_flag] BIT NOT NULL DEFAULT(0) -- 1 = enabled, 0 = disabled
  CONSTRAINT [FK_rel_sqlservercontroltables_sqlservercontrolsources] FOREIGN KEY (sqlserver_source_id)
    REFERENCES md.sqlserver_ingest_control_sources(id)
    ON DELETE CASCADE
    ON UPDATE CASCADE
  CONSTRAINT [FK_rel_sqlservercontroltables_loadpatterns] FOREIGN KEY (load_pattern_id)
    REFERENCES md.load_patterns(id)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION
)
