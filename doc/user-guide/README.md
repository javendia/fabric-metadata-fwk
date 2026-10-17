# Información básica

| Versión actual | Contacto |
| --- | --- |
| [VERSION](/VERSION) | [📧](mailto:jbuendia@encamina.com) |

# Índice
1. [Introducción](#introducción)
1. [Nomenclatura](#nomenclatura)
1. [Diseño de la solución](#diseño-de-la-solución)
    1. [Ingesta de datos](#ingesta-de-datos)
    1. [Consolidación](#consolidación)
        1. [Directed Acyclic Graph](#Directed-Acyclic-Graph)
    1. [Refinamiento](#refinamiento)
    1. [Transformación](#transformación)

# Introducción

El objetivo del presente documento es exponer en detalle el marco de trabajo para la ingeniería de datos sobre la plataforma Microsoft Fabric, mostrando el diseño de la solución, desgranando las distintas partes del desarrollo y recopilando las cuestiones a tener en cuenta.

# Nomenclatura

Tanto la solución implementada como esta documentación siguen la nomenclatura definida en el siguiente [fichero](/doc/user-guide/nomenclature.md).

# Diseño de la solución

![Diseño](/doc/resources/assets/diagrama.drawio.svg)

La solución se organiza de la siguiente manera:
- Un área de trabajo donde reside el código fuente, así como los artefactos necesarios para la gestión de metadatos.
- Al menos un área de trabajo que aglutine las capas de una arquitectura medallón, donde los datos se organizan en función de su calidad:
    - La capa bronce se divide en dos zonas:
        - *Landing* o *zona de aterrizaje* donde los datos se ingestan en crudo a la espera de ser procesados una vez han sido extraídos de los distintos orígenes de datos empleando canalizaciones, cuadernos u otros artefactos.
        - *Conformance* o *zona de consolidación* donde los datos se consolidan en tablas delta sin realizarse modificaciones.
    - En la capa plata o de refinamiento:
        - El origen de datos es un [enlace](https://learn.microsoft.com/es-es/fabric/onelake/onelake-shortcuts) a las tablas delta de la capa bronce.
        - Se llevan a cabo operaciones como, por ejemplo, la eliminación de espacios al inicio o al final de los valores de las columnas de tipo texto.
    - En la capa oro:
        - Mediante el uso de Spark SQL, se llevan a cabo las transformaciones necesarias y se aplica la lógica de negocio correspondiente sobre los datos. 
        - Del mismo modo que en el punto anterior, el origen de datos de la capa oro es un [enlace](https://learn.microsoft.com/es-es/fabric/onelake/onelake-shortcuts) a las tablas delta de la capa plata.

# Ingesta de datos

> [!IMPORTANT]
> Este paso no aplica si se lleva a cabo el reflejo de las tablas desde el origen de datos.

El objetivo del marco de trabajo para la ingesta de datos es generar extractores que permitan, mediante el uso de metadatos, estandarizar la ingesta de información de diferentes orígenes de datos. No son un reemplazo a los conectores oficiales, si no que trabajan conjuntamente.

Actualmente, se han construido extractores para los siguientes orígenes de datos:

| Origen | Documentación |
| --- | --- |
| SQL Server | [🔗](/doc/extractors/sql-server.md) |
| SharePoint Online | [🔗](/doc/extractors/sharepoint.md) |

## Metadatos

Como se ha comentado previamente, el corazón de la solución es el uso de metadatos. De cara a la ingesta de datos, cada uno de los orígenes obtiene los metadatos mediante el siguiente mecanismo:

| Origen | Obtención de metadatos |
| --- | --- |
| SQL Server | Automática |
| SharePoint Online | Manual |

Para aquellos extractores que cuentan con un proceso automático para la obtención de dichos metadatos, se sigue el siguiente procedimiento:

1. En primer lugar, es necesario ejecutar la canalización principal para la obtención de metadatos **DE_PIP_METADATA_SOURCES**.
1. La canalización **DE_PIP_METADATA_SOURCES**:
    
    - Lista los orígenes de datos existentes en la tabla **[md].[ingest_control_sources]**.
    - Filtra aquellos que se encuentran activos (*enable_flag = 1*).
    - Invoca a la canalización principal de obtención de metadatos para cada uno de los orígenes de datos donde se encuentra disponible.

Para más información sobre el proceso de obtención de metadatos para cada uno de los extractores, consultar el apartado **Obtención de metadatos** de la documentación de cada uno de ellos.

# Consolidación

> [!IMPORTANT]
> Este paso no aplica si se lleva a cabo el reflejo de las tablas desde el origen de datos.

Finalizada la ingesta, llega el momento de consolidar los datos en la capa bronce como tablas delta.

Como se ha comentado en el apartado, los ficheros generados durante la extracción estarán por defecto en formato ``.parquet``. Cabe recordar que los archivos Parquet son inmutables y no se pueden modificar.

Tomando el ejemplo de una ingesta realizada desde SQL Server, dichos archivos se organizarán de la siguiente manera:

```md
📁 Data
└── 📁 Landing
    └── 📁 CONTOSO                  # source_name
        └── 📁 SQLSERVER            # source_type
            └── 📁 Data_Customer    # source_schema + source_table
                ├── 📁 Pending      # Ficheros pendientes de procesar
                    └── 📁 2025
                        ├── 📁 11
                            └── 📄 Customer_2025-06-11T09:39:34.parquet
                        └── 📁 13
                            └── 📄 Customer_2025-06-13T08:25:29.parquet
                └── 📁 Processed    # Ficheros ya procesados
                    └── 📁 2025
                        ├── 📁 05
                            └── 📄 Customer_2025-06-05T14:04:33.parquet
                        └── 📁 10
                            ├── 📄 Customer_2025-06-10T13:18:17.parquet
                            └── 📄 Customer_2025-06-10T13:28:36.parquet
```

- En la carpeta **Pending** estarán almacenados tantos ficheros como extracciones pendientes de procesar haya.
- Una vez consolidados los datos de dichas extracciones sobre las tablas delta de la capa bronce, los archivos .parquet son movidos a la subcarpeta que hace referencia a la fecha de extracción bajo la carpeta principal **Processed**.

## Metadatos

Para llevar a cabo el proceso de consolidación, se emplean una serie de metadatos:

- **Tabla:** *[md].[load_patterns]*
- **Columnas**:
    - **id**: Valor auto incremental.
    - **pattern_name**: Patrón de carga. A fecha de este documento, el marco de trabajo cuenta con los siguientes patrones implementados:
        - ``full``: Sobreescritura completa de la tabla.
- **Tabla:** *[md].[enrich_control]*
- **Columnas**:
    - **id**: Valor auto incremental.
    - **load_pattern_id_bronze**: Patrón de carga a emplear para la consolidación de los datos en la capa bronce.
    - **active_for_load_bronze**: Determina si la carga a la capa bronce se encuentra activa.
    - **file_mask**: Ruta con máscara donde se encuentran los ficheros a consolidar en Landing. Como ejemplo:

        ```
        Data/Landing/CONTOSO/SQLSERVER/localhost_Contoso10M/Data_Customer/Pending/**/*.parquet
        ```
    - **entity**: Nombre de la entidad en la capa bronce.
    - **primary_key**: Clave primaria de la tabla. En caso de no disponer de clave primaria informada, se asigna el valor N/A.

## Artefactos

Seguidamente, se listan los componentes empleados en esta fase:

| Artefacto | Tipo | Descripción |
| --- | --- | --- |
| *00_CONTROL/01_COMMON/DE_NB_ENTITY* | Cuaderno | Clase que representa una entidad. Se emplea para realizar las operaciones necesarias para llevar los datos de una capa a otra en la arquitectura medallón. |
| *01_BRONZE/DE_NB_BRONZE_ORCHESTRATOR* | Cuaderno | Orquestador de la capa bronce. Desde la base de datos de metadatos, lista las tablas a procesar y ejecuta el cuaderno anterior para cada una de ellas a través de la creación de un DAG (Directed Acyclic Graph). |

## Proceso

Cada ejecución sigue la siguiente secuencia de acciones:

1. El orquestador principal **DE_PIP_MAIN_ORCHESTRATOR** consulta los metadatos necesarios:

    ```sql
    SELECT 
        [load_pattern_id_bronze]
        ,[file_mask]
        ,[entity]
        ,[primary_key]
    FROM [md].[enrich_control]
    WHERE [active_for_load_bronze] = 1
    ```

1. El cuaderno **DE_NB_BRONZE_ORCHESTRATOR**:
    1. Recibe como parámetro de la canalización principal **DE_PIP_MAIN_ORCHESTRATOR** los metadatos del lago de datos de la capa bronce, así como el listado de tablas a procesar fruto de la consulta anterior.
    1. Ejecuta la siguiente secuencia de operaciones:
        1. Establece el lago de datos de bronce como el lago de datos por defecto del cuaderno.
        1. Añade las configuraciones necesarias a la sesión de Spark.
        1. Invoca la ejecución del cuaderno **DE_NB_ENTITY** por cada una de las tablas.

            La orquestación del procesamiento de cada una de las tablas se realiza a través de la creación de un DAG.

            ### Directed Acyclic Graph

            DAG son las siglas en inglés de Directed Acyclic Graph (grafo acíclico dirigido). Representa una forma de grafo en la que los nodos individuales están dirigidos hacia otros nodos y estructurados para evitar ciclos. Cada nodo puede estar en el grafo sólo una vez. En el contexto de la orquestación de cuadernos, este grafo puede utilizarse para gestionar las dependencias entre cuadernos estableciendo una cierta secuencia o paralelismo.

            ![DAG](/doc/resources/assets/dag_sample.svg)

        1. Invocado el cuaderno para una tabla en cuestión, se llevan a cabo en secuencia las siguientes tareas:
            1. Se instancia la clase Entity con los parámetros y se ejecuta el método ``persist()`` ya que ``layer_name = bronze`` al tratarse de la **capa bronce**.
            1. El método ``persist()``:
                1. **Busca** si en la ruta especificada como origen de datos para la tabla existen **ficheros pendientes de procesar**.
                1. En caso de así serlo, **ejecuta cuadernos de preejecución en caso de existir**.
                Un **cuaderno de preejecución** de la capa bronce se identifica de la siguiente forma:
                    - **Se ubica en** la ruta **01_BRONZE/CONFORMANCE**.
                    - Comienza por **[DE_NB_BRONZE_PRE_EXECUTION_]**.
                    - Finaliza con el nombre de la tabla que se está procesando.
                1. Lee simultáneamente todos los ficheros parquet pendientes de procesar.
                1. Escribe la tabla en el destino con el nombre y el patrón de carga especificado en metadatos.

# Refinamiento

Finalizada la ingesta y consolidación en la capa bronce, el siguiente paso consiste en realizar transformaciones generales sobre los datos como paso previo a los trabajos para la confección del modelo dimensional de la capa oro.

## Metadatos

Se emplean los siguientes metadatos:

- **Tabla:** *[md].[enrich_control]*
- **Columnas**:
    - **id**: Valor auto incremental.
    - **load_pattern_id_silver**: Patrón de carga a emplear para el refinamiento de los datos en la capa plata. Es posible obtener más información sobre los patrones de carga en el apartado [Consolidación de datos](consolidación).
    - **active_for_load_silver**: Determina si la carga a la capa plata se encuentra activa.
    - **entity**: Nombre de la entidad en la capa plata.
    - **primary_key**: Clave primaria de la tabla. En caso de no disponer de clave primaria informada, se asigna el valor N/A.

## Artefactos

Seguidamente, se listan los componentes empleados en esta fase:

| Artefacto | Tipo | Descripción |
| --- | --- | --- |
| *00_CONTROL/01_COMMON/DE_NB_ENTITY* | Cuaderno | Clase que representa una entidad. Se emplea para realizar las operaciones necesarias para llevar los datos de una capa a otra en la arquitectura medallón. |
| *02_SILVER/DE_NB_SILVER_ORCHESTRATOR* | Cuaderno | Orquestador de la capa plata. Desde la base de datos de metadatos, lista las tablas a procesar y ejecuta el cuaderno anterior para cada una de ellas a través de la creación de un DAG (Directed Acyclic Graph). |

## Proceso

Cada ejecución sigue la siguiente secuencia de acciones:

1. El orquestador principal **DE_PIP_MAIN_ORCHESTRATOR** consulta los metadatos necesarios:

    ```sql
    SELECT *
    FROM [md].[enrich_control]
    WHERE [active_for_load_silver] = 1
    ```

1. El cuaderno **DE_NB_SILVER_ORCHESTRATOR**:
    1. Recibe como parámetro de la canalización principal **DE_PIP_MAIN_ORCHESTRATOR** los metadatos del lago de datos de la capa plata, así como el listado de tablas a procesar fruto de la consulta anterior.
    1. Ejecuta la siguiente secuencia de operaciones:
        1. Establece el lago de datos de plata como el lago de datos por defecto del cuaderno.
        1. Añade las configuraciones necesarias a la sesión de Spark.
        1. Invoca la ejecución del cuaderno **DE_NB_ENTITY** por cada una de las tablas a través de la creación de un DAG.
            1. Se instancia la clase Entity con los parámetros y se ejecuta el método ``enrich()`` ya que ``layer_name = silver`` al tratarse de la **capa plata**.
            1. El método ``enrich()``:
                1. Comprueba si la entidad que se intenta llevar a la capa plata existe con el mismo nombre en la capa bronce.
                1. En caso de así serlo, lee la tabla de la capa bronce.
                1. Convierte la columna ``loaded_at``, añadida por el extractor en cuestión, a fecha y hora.
                1. Escribe la tabla en el destino con el nombre y el patrón de carga especificado en metadatos.

# Transformación

Finalmente, los datos de la plata son utilizados como punto de partida para la construcción del modelo dimensional en la capa oro, donde se aplican todas las transformaciones necesarias (filtros, uniones, agregaciones, etc.).

## Metadatos

Se emplean los siguientes metadatos:

- **Tabla:** *[md].[curated_control]*
- **Columnas**:
    - **id**: Valor auto incremental.
    - **load_pattern_id_gold**: Patrón de carga a emplear para la entidad en la capa oro. Es posible obtener más información sobre los patrones de carga en el apartado [Consolidación de datos](consolidación).
    - **active_for_load_gold**: Determina si la carga a la capa oro se encuentra activa.
    - **transformation_notebook**: Nombre del cuaderno donde se construye la entidad dimensional.
    - **sql_view**: Nombre de la vista de Spark con la construcción de la entidad.
    - **entity_name**: Nombre de la entidad en la capa oro.
    - **primary_key**: Clave primaria de la entidad. En caso de no disponer de clave primaria informada, se asigna el valor N/A.
    - **dependencies**: Listado de entidades que deben ejecutarse previamente. Como ejemplo:

        ```
        "dim_Customer","dim_Product"
        ```

## Artefactos

Seguidamente, se listan los componentes empleados en esta fase:

| Artefacto | Tipo | Descripción |
| --- | --- | --- |
| *03_GOLD/TRANSFORMATIONS* | Cuadernos | Conjunto de cuadernos (uno por entidad) que contienen la construcción en Spark SQL de la vista empleada como origen de datos para la carga de datos de la entidad destino.
| *00_CONTROL/01_COMMON/DE_NB_ENTITY* | Cuaderno | Clase que representa una entidad. Se emplea para realizar las operaciones necesarias para llevar los datos de una capa a otra en la arquitectura medallón. |
| *03_GOLD/DE_NB_GOLD_ORCHESTRATOR* | Cuaderno | Orquestador de la capa oro. Desde la base de datos de metadatos, lista las tablas a procesar y ejecuta el cuaderno anterior para cada una de ellas a través de la creación de un DAG (Directed Acyclic Graph). |

## Proceso

1. El cuaderno **DE_NB_GOLD_ORCHESTRATOR**:
    1. Recibe como parámetro de la canalización principal **DE_PIP_MAIN_ORCHESTRATOR** los metadatos del lago de datos de la capa oro, así como el listado de tablas a procesar fruto de la consulta anterior.
    1. Ejecuta la siguiente secuencia de operaciones:
        1. Establece el lago de datos de oro como el lago de datos por defecto del cuaderno.
        1. Añade las configuraciones necesarias a la sesión de Spark.
        1. Invoca la ejecución del cuaderno **DE_NB_ENTITY** por cada una de las entidades a través de la creación de un DAG.
            1. Se instancia la clase Entity con los parámetros y se ejecuta el método ``curate()`` ya que ``layer_name = gold`` al tratarse de la **capa oro**.
            1. El método ``curate()``:
                1. Lanza el cuaderno identificado en los metadatos para la entidad.
                1. Ejecuta la vista resultante, resultado de la ejecución del cuaderno anterior.
                1. Escribe los datos devueltos por la vista anterior siguiendo el patrón de carga establecido en los metadatos.