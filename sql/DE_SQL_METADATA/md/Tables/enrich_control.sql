CREATE TABLE [md].[enrich_control]
(
  [id] INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
  [load_pattern_id_bronze] INT NOT NULL DEFAULT(1),
  [load_pattern_id_silver] INT NOT NULL DEFAULT(1),
  [active_for_load_bronze] BIT NOT NULL DEFAULT(0), -- 1 = enabled, 0 = disabled
  [active_for_load_silver] BIT NOT NULL DEFAULT(0), -- 1 = enabled, 0 = disabled
  [file_mask] VARCHAR(400) NOT NULL,
  [entity] VARCHAR(100) NOT NULL,
  [primary_key] VARCHAR(100) NOT NULL DEFAULT('N/A') -- Primary key for the entity, if applicable
  CONSTRAINT [FK_rel_enrichcontrol_loadpatterns_bronze] FOREIGN KEY (load_pattern_id_bronze)
  REFERENCES md.load_patterns(id)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION
  CONSTRAINT [FK_rel_enrichcontrol_loadpatterns_silver] FOREIGN KEY (load_pattern_id_silver)
  REFERENCES md.load_patterns(id)
  ON DELETE NO ACTION
  ON UPDATE NO ACTION
)
