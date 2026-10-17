CREATE TABLE [md].[sqlserver_ingest_control_tables_temp] (
    [sqlserver_source_id]  INT           NOT NULL,
    [source_name]          VARCHAR (150) NOT NULL,
    [source_schema]        VARCHAR (50)  NOT NULL,
    [source_table_name]    VARCHAR (150) NOT NULL,
    [source_table_columns] VARCHAR (800) NOT NULL,
    [primary_key]          VARCHAR (150) NOT NULL,
    [target_table_name]    AS            (concat([source_name],'_',[source_table_name])) PERSISTED NOT NULL,
    [target_root_path]     VARCHAR (800) NOT NULL,
    [target_table_path]    AS            (concat([target_root_path],'/',[source_schema],'_',[source_table_name])) PERSISTED NOT NULL,
    [load_pattern_id]      SMALLINT      DEFAULT ((1)) NOT NULL,
    [enable_flag]          BIT           DEFAULT ((0)) NOT NULL
);


GO

