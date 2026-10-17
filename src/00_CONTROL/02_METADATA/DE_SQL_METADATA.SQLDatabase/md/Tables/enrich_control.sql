CREATE TABLE [md].[enrich_control] (
    [id]                     INT           IDENTITY (1, 1) NOT NULL,
    [load_pattern_id_bronze] INT           DEFAULT ((1)) NOT NULL,
    [load_pattern_id_silver] INT           DEFAULT ((1)) NOT NULL,
    [active_for_load_bronze] BIT           DEFAULT ((0)) NOT NULL,
    [active_for_load_silver] BIT           DEFAULT ((0)) NOT NULL,
    [file_mask]              VARCHAR (400) NOT NULL,
    [entity]                 VARCHAR (100) NOT NULL,
    [primary_key]            VARCHAR (100) DEFAULT ('N/A') NOT NULL,
    PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT [FK_rel_enrichcontrol_loadpatterns_bronze] FOREIGN KEY ([load_pattern_id_bronze]) REFERENCES [md].[load_patterns] ([id]),
    CONSTRAINT [FK_rel_enrichcontrol_loadpatterns_silver] FOREIGN KEY ([load_pattern_id_silver]) REFERENCES [md].[load_patterns] ([id])
);


GO

