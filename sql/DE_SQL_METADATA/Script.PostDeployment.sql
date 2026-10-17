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
END;