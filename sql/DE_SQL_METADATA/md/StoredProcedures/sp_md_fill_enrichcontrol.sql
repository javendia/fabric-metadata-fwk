CREATE PROCEDURE [md].[sp_md_fill_enrichcontrol]
AS
BEGIN
    SET NOCOUNT ON;

    EXEC md.sp_md_fill_enrichcontrol_temp;

    MERGE md.enrich_control AS tgt
    USING md.enrich_control_temp AS src
        ON tgt.entity = src.entity
    WHEN MATCHED THEN
        UPDATE SET
            tgt.file_mask = src.file_mask,
            tgt.primary_key = src.primary_key
    WHEN NOT MATCHED BY TARGET THEN
        INSERT (file_mask, entity, primary_key)
        VALUES (src.file_mask, src.entity, src.primary_key);
END;
GO