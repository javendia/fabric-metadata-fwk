CREATE TABLE [md].[refresh_semantic_model_control] (
    [id]                INT          IDENTITY (1, 1) NOT NULL,
    [workspace_id]      VARCHAR (50) NOT NULL,
    [semantic_model_id] VARCHAR (50) NOT NULL,
    [enable_flag]       BIT          DEFAULT ((0)) NOT NULL,
    PRIMARY KEY CLUSTERED ([id] ASC),
    CONSTRAINT [UNIQUE_smcontrol_entity_name] UNIQUE NONCLUSTERED ([semantic_model_id] ASC)
);


GO

