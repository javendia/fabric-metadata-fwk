CREATE TABLE [md].[ingest_control_sources] (
    [id]          INT           IDENTITY (1, 1) NOT NULL,
    [source_name] VARCHAR (150) NOT NULL,
    [source_type] VARCHAR (50)  NOT NULL,
    [enable_flag] BIT           DEFAULT ((0)) NOT NULL,
    PRIMARY KEY CLUSTERED ([id] ASC)
);


GO

