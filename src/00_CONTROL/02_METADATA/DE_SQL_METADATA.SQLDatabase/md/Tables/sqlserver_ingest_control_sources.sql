CREATE TABLE [md].[sqlserver_ingest_control_sources] (
    [id]                   INT           IDENTITY (1, 1) NOT NULL,
    [source_id]            INT           NOT NULL,
    [source_server]        VARCHAR (150) NOT NULL,
    [source_database_name] VARCHAR (150) NOT NULL,
    [source_schema]        VARCHAR (50)  NOT NULL,
    [source_tables]        VARCHAR (800) NOT NULL,
    PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT [FK_rel_sqlservercontrolsources_controlsources] FOREIGN KEY ([source_id]) REFERENCES [md].[ingest_control_sources] ([id]) ON DELETE CASCADE ON UPDATE CASCADE
);


GO

