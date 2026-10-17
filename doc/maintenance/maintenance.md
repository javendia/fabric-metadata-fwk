# Índice

1. [Introducción](#introducción)
1. [Artefactos](#artefactos)
1. [Ejecución](#ejecución)

# Introducción

El objetivo del presente documento es exponer en detalle cómo se lleva a cabo el mantenimiento de las tablas delta en los lagos de datos que componen la solución, a través de operaciones como la compactación y la eliminación de ficheros demasiado antiguos.

# Artefactos

En este apartado, se listan los componentes empleados:

| Área de trabajo | Artefacto | Tipo | Descripción |
| --- | --- | --- | --- |
| *WS_CONTROL* | *00_CONTROL/03_MAINTENANCE/DE_NB_MAINTENANCE* | Cuaderno | Obtiene desde metadatos las tablas sobre las que realizar tareas de mantenimiento para cada una de las capas de la solución. |
| *WS_CONTROL* | *00_CONTROL/03_MAINTENANCE/DE_PIP_MAINTENANCE* | Canalización | Canalización principal del proceso de mantenimiento. Ejecuta el cuaderno anterior pasando los parámetros necesarios desde la biblioteca de variables. |

# Ejecución

El proceso de mantenimiento sigue la siguiente secuencia de operaciones:

1. La canalización **DE_PIP_MAINTENANCE**:
    1. Ejecuta el cuaderno **DE_NB_MAINTENANCE** pasando los parámetros necesarios, cuyos valores residen en la biblioteca de variables **DE_VL_CONTROL_VARIABLES**.
1. El cuaderno **DE_NB_MAINTENANCE**:
    1. Instala las siguientes dependencias:

        ```console
        %pip install semantic-link-labs ms-fabric-cli --q
        ```
    2. Inicializa las constantes necesarias, entre ellas las consultas SQL para la obtención de las tablas a procesar por cada capa, así como el periodo de retención:

        ```python
        RETENTION_PERIOD = 168 # 7 días
        ```
    3. Obtiene un token de acceso con la identidad del usuario que ejecuta el cuaderno.
    4. Empleando la herramienta Fabric CLI, lee los datos de conexión de la base de datos de metadatos.
    5. Por cada capa:
        1. Obtiene desde metadatos las entidades que se encuentran activas **(enable_flag = 1)**.
        1. Ejecuta el comando [OPTIMIZE](https://docs.delta.io/latest/optimizations-oss.html) a través del método disponible en la librería **semantic-link-labs**.
        1. Ejecuta el comando [VACUUM](https://docs.delta.io/latest/delta-utility.html#remove-files-no-longer-referenced-by-a-delta-table) a través del método disponible en la librería **semantic-link-labs**.