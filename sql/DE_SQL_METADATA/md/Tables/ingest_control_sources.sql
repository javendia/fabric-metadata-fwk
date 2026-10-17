CREATE TABLE [md].[ingest_control_sources]
(
  [id] INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
  [source_name] VARCHAR(150) NOT NULL,
  [source_type] VARCHAR(50) NOT NULL,
  [enable_flag] BIT NOT NULL DEFAULT(0) -- 1 = enabled, 0 = disabled
)