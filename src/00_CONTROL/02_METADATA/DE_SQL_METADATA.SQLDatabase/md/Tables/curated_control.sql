CREATE TABLE [md].[curated_control] (
    [id]                      INT           IDENTITY (1, 1) NOT NULL,
    [load_pattern_id_gold]    INT           DEFAULT ((1)) NOT NULL,
    [active_for_load_gold]    BIT           DEFAULT ((0)) NOT NULL,
    [transformation_notebook] VARCHAR (400) NOT NULL,
    [sql_view]                VARCHAR (100) NOT NULL,
    [entity_name]             VARCHAR (100) NOT NULL,
    [primary_key]             VARCHAR (150) NOT NULL,
    [dependencies]            VARCHAR (400) NULL,
    PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT [FK_rel_curatedcontrol_loadpatterns] FOREIGN KEY ([load_pattern_id_gold]) REFERENCES [md].[load_patterns] ([id]) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT [UNIQUE_curatedcontrol_entity_name] UNIQUE NONCLUSTERED ([entity_name] ASC)
);


GO

