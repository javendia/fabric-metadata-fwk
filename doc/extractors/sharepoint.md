# Índice
1. [Recursos adicionales](#recursos-adicionales)
1. [Seguridad](#seguridad)
1. [Obtención de metadatos](#obtención-de-metadatos)
1. [Metadatos](#metadatos)
1. [Artefactos](#artefactos)
1. [Flujo de datos](#flujo-de-datos)

# Recursos adicionales

Más allá de la capacidad de Fabric aprovisionada, a continuación se enumeran los recursos necesarios para el uso del extractor:

| Tipo | Descripción |
| --- | --- |
| *Entidad de servicio* | Aplicación empleada para llevar a cabo la autenticación sobre el sitio de SharePoint Online. |
| *Almacén de claves* | Almacena los secretos empleados en la extracción de ficheros. |

# Seguridad

Se deben otorgar los siguientes roles/permisos para el usuario/grupo de usuarios encargados de la ejecución:

- Al menos rol **Colaborador** sobre el área de trabajo **WS_CONTROL**.
- Rol **Usuario de secretos** sobre el almacén de claves.

Adicionalmente, se requieren permisos de escritura para la entidad de servicio sobre el sitio de SharePoint Online. Para asignar dichos permisos, es necesario ejecutar el script [SetSharePointSitePermissions.ps1](/scripts/powershell/SetSharePointSitePermissions.ps1)

# Obtención de metadatos

Para este extractor, no existe un proceso automatizado que obtenga los metadatos necesarios del origen de datos SharePoint. Por tanto, resulta necesario rellenar manualmente las tablas **[md].[sharepoint_ingest_control_sources]** y **[md].[sharepoint_ingest_control_patterns]**.

# Metadatos

A continuación, se enumeran las tablas de metadatos empleadas en la construcción del extractor:

- **Tabla:** *[md].[sharepoint_ingest_control_sources]*
- **Columnas**:
    - **id**: Valor auto incremental.
    - **source_id**: Identificador del origen de datos. Hace referencia al identificador de la tabla **[md].[ingest_control_sources]**
    - **site_id**: Identificador GUID del sitio/subsitio de SharePoint Online. Como ejemplo:

        ```
        Sitio → a565509d-987b-418e-8247-af55d3816d22
        Subsitio → ed65cfc0-4cd0-443b-8e86-910d8e9b18c9,8f7d7330-519e-42bf-b442-5d75a2010376
        ```
    - **resource**: Dominio (p. ej. *encamina.sharepoint.com*)
    - **list_name**: Nombre de la lista/biblioteca de documentos.
    - **key_vault**: Nombre del almacén de claves creado previamente.
    - **client_id_secret_name**: Nombre del secreto en el almacén de claves que almacena el identificador GUID de la entidad de servicio.
    - **client_secret_name**: Nombre del secreto en el almacén de claves que almacena el secreto de la entidad de servicio.
    - **tenant_secret_name**: Nombre del secreto en el almacén de claves que almacena el identificador GUID del tenant.
    - **url_root_path**: Directorio raíz a partir del cual obtener ficheros.
    - **url_relative_path**: Subdirectorio a partir del cual obtener ficheros.
    - **filter_patterns**: Palabras clave que debe contener el nombre de los ficheros para segmentar la extracción.
- **Tabla:** *[md].[sharepoint_ingest_control_patterns]*
- **Columnas**:
    - **sharepoint_source_id**: Identificador del origen de datos SharePoint.
    - **source_file_extension**: Extensión del patrón de fichero a extraer.
    - **sheet_id**: En el caso de ficheros Excel, índice (empezando en 1) de la hoja a obtener.
    - **destination_root_path**: Ruta donde almacenar los ficheros de ese patrón en el destino.
    - **destination_file_extension**: Extensión en el destino (.parquet por defecto).
    - **columns**: Número de columnas a considerar.
    - **column_mapping**: Diccionario con los nombres que deben recibir las columnas.
    - **column_types**: Tipos de datos para dichas columnas.

# Artefactos

En este apartado, se listan los componentes empleados en la construcción del extractor:

| Área de trabajo | Artefacto | Tipo | Descripción |
| --- | --- | --- | --- |
| *WS_CONTROL* | *01_BRONZE/LANDING/SHAREPOINT/DE_NB_SHAREPOINT_EXTRACTOR* | Cuaderno | Extractor de SharePoint Online. Mediante el uso de la API de Microsoft Graph, obtiene los ficheros pendientes de extraer y mueve automáticamente a la carpeta de ficheros procesados aquellos ya leídos. |
| *WS_CONTROL* | *01_BRONZE/LANDING/SHAREPOINT/DE_PIP_SHAREPOINT_MAIN* | Canalización | Canalización principal del extractor. Lista los orígenes de este tipo existentes en los metadatos y ejecuta el cuaderno para realizar la ingesta de cada uno de ellos. |

# Proceso

Cada ejecución sigue la secuencia de acciones que se puede ver en el siguiente diagrama:

![Diseño](/doc/resources/assets/shp-ingest.drawio.svg)

- La canalización principal del extractor **DE_PIP_SHAREPOINT_MAIN**:

    - Obtiene los metadatos del origen de datos SharePoint **cuyo identificador (source_id) ha recibido como parámetro:**

        ```sql
        SELECT *
        FROM [md].[sharepoint_ingest_control_sources]
        WHERE [source_id] = ?
        ```

    - Obtiene los metadatos de los patrones de ficheros a obtener de dicho origen:

        ```sql
        SELECT * 
        FROM [md].[sharepoint_ingest_control_patterns]
            WHERE enable_flag = 1
            AND sharepoint_source_id = ?
        ```

    - Invoca al cuaderno **DE_NB_SHAREPOINT_EXTRACTOR**, pasando como parámetros los metadatos anteriores.

- El extractor realiza las siguientes acciones en secuencia:
    1. Instancia la clase **SharePointExtractor**, obteniendo un token de acceso tras leer los secretos del almacén de claves, así como el identificador GUID de la lista/biblioteca de documentos.
    1. Enumera las carpetas de la lista/biblioteca de documentos donde la raíz y el subdirectorio se encuentran presentes en la url de dicha carpeta.
    1. Crea en la carpeta obtenida una subcarpeta **Processed** donde mover los ficheros una vez leídos. Si la subcarpeta ya existe, obtiene su identificador.
    1. Lista el contenido de la carpeta
    1. Descarga los ficheros existentes de la carpeta, realizando las siguientes acciones basándose en la información de los metadatos:
        - Lee las N columnas.
        - Aplica el diccionario para asignarles un nombre.
        - Elimina la primera línea del archivo, para reemplazar las cabeceras.
        - Añade una posible capa de personalización, de manera que se pudieran añadir columnas adicionales al fichero resultante.
        - Compone la ruta destino que:
            - Comienza con la carpeta raíz especificada en metadatos.
            - Contiene las carpetas entre la raíz y la carpeta donde se encuentran los ficheros en el origen de datos.
            - En esta carpeta, se crea la carpeta **Pending** donde dejar los archivos leídos en una estructura de carpetas **Año > Mes > Día** que hace referencia a la fecha de extracción del archivo.
        - Elimina caracteres extraños en el nombre del fichero origen de cara a almacenarlo en el destino.
        - Escribe o sobrescribe en caso de existir el fichero en destino.