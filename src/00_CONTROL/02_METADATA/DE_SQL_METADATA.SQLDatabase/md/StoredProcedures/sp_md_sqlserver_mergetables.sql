CREATE PROCEDURE [md].[sp_md_sqlserver_mergetables]
AS
BEGIN
    SET NOCOUNT ON;

    MERGE md.sqlserver_ingest_control_tables AS tgt
    USING md.sqlserver_ingest_control_tables_temp AS src
        ON (tgt.sqlserver_source_id = src.sqlserver_source_id 
        AND tgt.source_table_name = src.source_table_name)
    WHEN NOT MATCHED BY TARGET THEN
        INSERT (sqlserver_source_id, source_table_name, source_table_columns, primary_key, target_table_name, target_table_path)
        VALUES (src.sqlserver_source_id, src.source_table_name, src.source_table_columns, src.primary_key, src.target_table_name, src.target_table_path);
END;

GO

