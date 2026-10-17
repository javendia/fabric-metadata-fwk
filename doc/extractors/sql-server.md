# Índice

1. [Obtención de metadatos](#obtención-de-metadatos)
1. [Proceso](#proceso)

# Obtención de metadatos

El primer paso para obtener los metadatos de las tablas a ingestar consiste en rellenar manualmente la tabla **[md].[sharepoint_ingest_control_sources]** de la base de datos de metadatos, la cual contiene las siguientes columnas:

- **id**: Valor auto incremental.
- **source_id**: Identificador del origen de datos. Hace referencia al identificador de la tabla ***[md].[ingest_control_sources]***
- **source_server**: Servidor SQL Server.
- **source_database_name**: Base de datos.
- **source_schema**: Esquema en el cual residen las tablas a consultar.
- **source_tables**: Listado de tablas (separado por comas) de las que obtener sus metadatos.

Una vez rellenada la tabla, a continuación se adjunta un diagrama que enumera los pasos llevados a cabo para leer los metadatos de las tablas en el origen e insertar dicha información en la base de datos de metadatos:

![Obtención de metadatos](/doc/resources/assets/sqlserver-metadata.drawio.svg)

1. La canalización **DE_PIP_SQLSERVER_GET_TABLES**:

    - Obtiene el **listado de tablas** de las cuales obtener sus metadatos para el **origen de datos SQL Server (source_id) recibido como parámetro**:

        ```sql
            SELECT 
                [id]
                ,[source_server]
                ,[source_database_name]
                ,[source_schema]
                ,[source_tables]
            FROM [md].[sqlserver_ingest_control_sources]
            WHERE [source_id] = ?
        ```
    - Invoca a la canalización **DE_PIP_SQLSERVER_GET_METADATA_TABLES** para obtener los metadatos necesarios de cada una de las tablas del listado.

1. La canalización **DE_PIP_SQLSERVER_GET_METADATA_TABLES**:

    - Copia los metadatos resultado de ejecutar la siguiente consulta en la tabla auxiliar **[md].[sqlserver_ingest_control_tables_temp]**, ``?`` corresponde a la lista de tablas a leer:

        ```sql
            SELECT
                tab.[name] AS [source_table_name],
                REPLACE(LEFT(column_names, len(column_names)-1), '' '', '''') AS [primary_key]
            FROM sys.tables tab
                LEFT JOIN sys.indexes pk
                    ON tab.object_id = pk.object_id 
                    AND pk.is_primary_key = 1
                CROSS APPLY (SELECT col.[name] + '', ''
                                FROM sys.index_columns ic
                                    INNER join sys.columns col
                                        ON ic.object_id = col.object_id
                                        AND ic.column_id = col.column_id
                                WHERE ic.object_id = tab.object_id
                                    AND ic.index_id = pk.index_id
                                        ORDER BY col.column_id
                                        FOR XML PATH ('''')) D (column_names)
            WHERE tab.name IN (?)
            ORDER BY schema_name(tab.schema_id),
                tab.[name]
        ```
    - Inserta los metadatos en la tabla resultado **[md].[sqlserver_ingest_control_tables]** ejecutando el procedimiento almacenado **[md].[sp_md_sqlserver_mergetables]**.

> [!NOTE]
> Este proceso sólo inserta metadatos nuevos. La actualización de metadatos existentes debe realizarse manualmente.


# Proceso

Cada ejecución sigue la secuencia de acciones que se puede ver en el siguiente diagrama:

![Diseño](/doc/resources/assets/sqlserver-ingest.drawio.svg)

1. La canalización principal del extractor **DE_PIP_SQLSERVER_MAIN**:

    1. Obtiene los metadatos del origen de datos SQL Server, donde ```?`` corresponde al **identificador (source_id) ha recibido como parámetro:**

        ```sql
            SELECT
                ics.source_database_name AS [source_database_name],
                ics.source_schema AS [source_schema],
                ict.source_table_name AS [source_table_name],
                ict.source_table_name AS [target_table_name],
                ict.target_table_path AS [target_table_path],
                ict.file_extension AS [file_extension],
                ict.load_pattern_id AS [load_pattern_id],
                ict.enable_flag AS [enable_flag]
            FROM [md].[sqlserver_ingest_control_sources] AS ics
            INNER JOIN [md].[sqlserver_ingest_control_tables] AS ict
            ON ics.id = ict.sqlserver_source_id
            WHERE ics.source_id = ?
            AND ict.enable_flag = 1
        ```
    1. Seguidamente, en función del **patrón de carga (load_pattern_id)** con el que se deba ingestar la tabla, se lleva a cabo la carga de los datos.
        - La actividad de copiar datos añade como columnas de auditoría al fichero resultante la siguiente información: 
            - ``source_name``: Corresponde al nombre del origen de datos que recibe como parámetro la canalización.
            - ``loaded_at``: Fecha y hora de ingesta de los datos, en formato ``yyyy-MM-ddTHH:mm:ss``
    1. Los **ficheros resultantes** se almacenan **en la ruta especificada** en los metadatos **(target_table_path)**.
        - Bajo esta ruta, se crea la carpeta **Pending** donde dejar los archivos leídos en una estructura de carpetas **Año > Mes > Día** que hace referencia a la fecha de extracción del archivo.