CREATE TABLE [md].[refresh_semantic_model_control]
(
  [id] INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
  [workspace_id] VARCHAR(50) NOT NULL,
  [semantic_model_id] VARCHAR(50) NOT NULL,
  [enable_flag] BIT NOT NULL DEFAULT(0) -- 1 = enabled, 0 = disabled
  CONSTRAINT [UNIQUE_smcontrol_entity_name] UNIQUE ([semantic_model_id])
)
