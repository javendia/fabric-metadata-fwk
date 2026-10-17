CREATE TABLE [md].[curated_control]
(
  [id] INT NOT NULL IDENTITY(1,1) PRIMARY KEY,
  [load_pattern_id_gold] INT NOT NULL DEFAULT(1),
  [active_for_load_gold] BIT NOT NULL DEFAULT(0), -- 1 = enabled, 0 = disabled
  [transformation_notebook] VARCHAR(400) NOT NULL,
  [sql_view] VARCHAR(100) NOT NULL,
  [entity_name] VARCHAR(100) NOT NULL,
  [primary_key] VARCHAR(150) NOT NULL DEFAULT('N/A'), -- Primary key for the entity, if applicable,
  [dependencies] VARCHAR(400) NULL -- Comma-separated list of dependencies
  CONSTRAINT [UNIQUE_curatedcontrol_entity_name] UNIQUE ([entity_name])
  CONSTRAINT [FK_rel_curatedcontrol_loadpatterns] FOREIGN KEY (load_pattern_id_gold)
  REFERENCES md.load_patterns(id)
  ON DELETE CASCADE
  ON UPDATE CASCADE
)