-- This file contains SQL statements that will be executed after the build script.

-- md.load_patterns
-- This table is used to define the load patterns for data ingestion.

IF ('$(Environment)' = 'DEV')
BEGIN
    IF NOT EXISTS(SELECT 1 FROM [md].[load_patterns])
    BEGIN
        INSERT INTO [md].[load_patterns] (pattern_name)
        VALUES
        ('full'),
        ('differential'),
        ('append')
    END;

    IF NOT EXISTS(SELECT 1 FROM [md].[ingest_control_sources])
    BEGIN
        INSERT INTO [md].[ingest_control_sources] (source_name, source_type, enable_flag)
        VALUES
        ('CONTOSO', 'SQLSERVER', 1),
        ('EVIDENCIAS', 'SHAREPOINT', 1)
    END;

    -- md.sqlserver_ingest_control_sources
    -- This table is used to control the ingestion of data from various SQL Server sources.
    IF NOT EXISTS(SELECT 1 FROM [md].[sqlserver_ingest_control_sources])
    BEGIN
        INSERT INTO [md].[sqlserver_ingest_control_sources] (source_id, source_server, source_database_name, source_schema, source_tables)
        VALUES
        (1, 'localhost', 'Contoso10M', 'Data', '''Customer'',''Date'',''OrderRows'',''Orders'',''Product'',''Sales'',''Store''')
    END;

    -- md.sharepoint_ingest_control_sources
    -- This table is used to control the ingestion of data from various SharePoint sources.
    IF NOT EXISTS(SELECT 1 FROM [md].[sharepoint_ingest_control_sources])
    BEGIN
        INSERT INTO [md].[sharepoint_ingest_control_sources] 
            (source_id, site_id, resource, list_name, key_vault, client_id_secret_name, client_secret_name, tenant_secret_name, url_root_path, url_relative_path, filter_patterns)
        VALUES
        (2, 'a565509d-987b-418e-8247-af55d3816d22', 'encamina.sharepoint.com', 'Documentos', 'kv0fabric0demo', 'ClientID', 'ClientSecret', 'TenantID',
            'Reporte Evidencias/', '/6. Residuos', '_(GREL|MANUAL|MAPEO)_')
    END;

    IF NOT EXISTS(SELECT 1 FROM [md].[sharepoint_ingest_control_patterns])
    BEGIN
        INSERT INTO [md].[sharepoint_ingest_control_patterns] 
            (sharepoint_source_id, file_pattern_name, source_file_extension, sheet_id, destination_root_path, columns, column_mapping, column_types, enable_flag)
        VALUES
        (1, 'GREL', '.xlsx', 1, 'Data/Landing/Reporte Evidencias/SHAREPOINT/GREL/',
            '[0,1,2,3,4,5,6,7,8,9,10,11,12]',
            '{"column_1": "cod_ler", "column_2": "peligroso", "column_3": "descripcion", "column_4": "cantidad", "column_5": "fecha_inicio", "column_6": "fecha_entrega", "column_7": "albaran", "column_8": "nima_gestor", "column_9": "nombre_gestor", "column_10": "nima_productor", "column_11": "nombre_productor", "column_12": "cod_tratamiento", "column_13": "tratamiento"}',
            '{0: "string", 1: "string", 2: "string", 3: "string", 4: "string", 5: "string", 6: "string", 7: "string", 8: "string", 9: "string", 10: "string", 11: "string", 12: "string"}', 1),
        (1, 'MANUAL', '.xlsx', 1, 'Data/Landing/Reporte Evidencias/SHAREPOINT/MANUAL/',
            '[0,1,2,3]',
            '{"column_1": "waste", "column_2": "kg_quantity", "column_3": "waste_destination", "column_4": "waste_management"}',
            '{0: "string", 1: "string", 2: "string", 3: "string"}', 1),
        (1, 'MANUAL', '.xlsx', 2, 'Data/Landing/Reporte Evidencias/SHAREPOINT/MANUAL/',
            '[0,1,2,3]',
            '{"column_1": "waste", "column_2": "kg_quantity", "column_3": "waste_destination", "column_4": "waste_management"}',
            '{0: "string", 1: "string", 2: "string", 3: "string"}', 1),
        (1, 'MAPEO', '.xlsx', 1, 'Data/Landing/Reporte Evidencias/SHAREPOINT/MAPEO/',
            '[0,1,2]',
            '{"column_1": "cod_tratamiento", "column_2": "tratamiento", "column_3": "destino_eliminacion"}',
            '{0: "string", 1: "string", 2: "string"}', 1)
    END;
END;