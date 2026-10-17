CREATE TABLE [md].[sharepoint_ingest_control_sources] (
    [id]                    INT           IDENTITY (1, 1) NOT NULL,
    [source_id]             INT           NOT NULL,
    [site_id]               VARCHAR (100) NOT NULL,
    [resource]              VARCHAR (50)  NOT NULL,
    [list_name]             VARCHAR (50)  NOT NULL,
    [key_vault]             VARCHAR (50)  NOT NULL,
    [client_id_secret_name] VARCHAR (50)  NOT NULL,
    [client_secret_name]    VARCHAR (50)  NOT NULL,
    [tenant_secret_name]    VARCHAR (50)  NOT NULL,
    [url_root_path]         VARCHAR (100) NOT NULL,
    [url_relative_path]     VARCHAR (100) NULL,
    [filter_patterns]       VARCHAR (100) NULL,
    PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT [FK_rel_sharepointcontrolsources_controlsources] FOREIGN KEY ([source_id]) REFERENCES [md].[ingest_control_sources] ([id]) ON DELETE CASCADE ON UPDATE CASCADE
);


GO

