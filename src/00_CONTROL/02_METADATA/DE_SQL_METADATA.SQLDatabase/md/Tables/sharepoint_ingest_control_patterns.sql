CREATE TABLE [md].[sharepoint_ingest_control_patterns] (
    [sharepoint_source_id]       INT           NOT NULL,
    [file_pattern_name]          VARCHAR (50)  NOT NULL,
    [source_file_extension]      VARCHAR (50)  NOT NULL,
    [sheet_id]                   INT           NULL,
    [destination_root_path]      VARCHAR (150) NOT NULL,
    [destination_file_extension] VARCHAR (50)  DEFAULT ('.parquet') NOT NULL,
    [columns]                    VARCHAR (400) NULL,
    [column_mapping]             VARCHAR (800) NULL,
    [column_types]               VARCHAR (800) NULL,
    [enable_flag]                BIT           DEFAULT ((0)) NOT NULL,
    CONSTRAINT [FK_rel_sharepointcontrolpatterns_sharepointcontrolsources] FOREIGN KEY ([sharepoint_source_id]) REFERENCES [md].[sharepoint_ingest_control_sources] ([id]) ON DELETE CASCADE ON UPDATE CASCADE
);


GO

