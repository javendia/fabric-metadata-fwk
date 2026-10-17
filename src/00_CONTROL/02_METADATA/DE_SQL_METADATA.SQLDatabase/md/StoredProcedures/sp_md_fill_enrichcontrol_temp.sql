CREATE PROCEDURE [md].[sp_md_fill_enrichcontrol_temp]
AS
BEGIN
    SET NOCOUNT ON;

    -- SQL Server
    IF (OBJECT_ID('md.sqlserver_ingest_control_tables') IS NOT NULL)
    BEGIN
      INSERT INTO md.enrich_control_temp (file_mask, entity, primary_key)
      SELECT
        CONCAT(target_table_path, '/Pending/**/*.parquet') AS file_mask,
        target_table_name AS entity,
        primary_key
      FROM md.sqlserver_ingest_control_tables
      WHERE enable_flag = 1
    END

    -- SharePoint
    IF (OBJECT_ID('md.sharepoint_ingest_control_patterns') IS NOT NULL)
    BEGIN
      INSERT INTO md.enrich_control_temp (file_mask, entity, primary_key)
      SELECT DISTINCT
        CONCAT(SP.destination_root_path, '**/Pending/**/*.parquet') AS file_mask,
        CONCAT(S.source_name, '_', SP.file_pattern_name) AS entity,
        'N/A' AS primary_key
      FROM md.sharepoint_ingest_control_patterns AS SP
      INNER JOIN md.sharepoint_ingest_control_sources AS SS
        ON SP.sharepoint_source_id = SS.id
      INNER JOIN md.ingest_control_sources AS S
        ON SS.source_id = S.id
      WHERE SP.enable_flag = 1
    END
END;

GO

