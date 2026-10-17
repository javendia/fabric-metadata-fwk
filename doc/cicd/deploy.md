# Índice
1. [Introducción](#introducción)
1. [Diseño de la solución](#diseño-de-la-solución)
1. [Recursos y permisos](#recursos-y-permisos)
1. [Entornos, variables y secretos](#entornos-variables-y-secretos)
1. [Flujo de despliegue](#entornos-variables-y-secretos)
    1. [Disparadores](#disparadores)
    1. [Trabajos](#trabajos)

# Introducción

El objetivo de este documento es detallar cómo, empleando acciones de GitHub, se automatiza el despliegue de la solución en Microsoft Fabric, gestionando la instalación, configuración y publicación de artefactos.

# Diseño

A continuación, se adjunta un diagrama del proceso de despliegue:

![Ejemplo](/doc/resources/assets/cicd.drawio.svg)

Actualmente, existen dos formas de desencadenar la canalización de despliegue

1. En el entorno de producción:
    1. Los desarrolladores, una vez completados los cambios y listos para ser promocionados a producción, realizan una **solicitud de incorporación de cambios** para llevar dichos cambios a la rama principal (main).
    1. Se requiere realizar una sincronización manual
1. En el entorno de desarrollo:
    1. En el arranque de un nuevo proyecto, desplegar el marco de trabajo automáticamente.

# Recursos y permisos

A continuación, se listan los recursos necesarios para la correcta ejecución de la canalización de despliegue:

- En la plataforma GitHub:
    - Dos entornos (```DEV```, ```PRO```) junto a las variables y secretos recogidas en el apartado [Entornos, variables y secretos](#entornos-variables-y-secretos) en el repositorio de código.
- En la nube de Azure:
    - Una entidad de servicio
        - Se deben crear las siguientes credenciales federadas para el repositorio GitHub:
            - Para el entorno ```DEV```.
            - Para el entorno ```PRO```.
            - Para la solicitud de incorporación de cambios a la rama main.

# Entornos, variables y secretos

Como se ha comentado con anterioridad, es necesario la creación en el repositorio de GitHub de dos entornos y del conjunto de variables/secretos que se muestran a continuación para cada uno de ellos:

| Tipo | Nombre| Valor por defecto | Descripción |
| --- | --- | --- | --- |
| Secreto | AZURE_CLIENT_ID | - | Identificador de la entidad de servicio. |
| Secreto | AZURE_SUBSCRIPTION_ID | - | Identificador de la suscripción donde se encuentra la capacidad de Microsoft Fabric. |
| Secreto | AZURE_TENANT_ID | - | Identificador del directorio. |
| Secreto | FAB_ADMIN_UPNS | - | Listado, separado por comas, de los identificadores de usuarios a añadir como administradores de las áreas de trabajo que se crean durante el proceso de instalación. |
| Variable | BRONZE_LAKEHOUSE_NAME | DE_LH_BRONZE | Lago de datos de la capa bronce. |
| Variable | BRONZE_WORKSPACE_NAME | WS_DLH_DEV | Área de trabajo para la capa bronce. |
| Variable | CONTROL_WORKSPACE_NAME | WS_CONTROL_DEV | Área de trabajo para la capa de gestión y código fuente. |
| Variable | FAB_CAPACITY | - | Nombre de la capacidad de Microsoft Fabric. |
| Variable | GOLD_LAKEHOUSE_NAME | - | Lago de datos de la capa oro. |
| Variable | GOLD_WORKSPACE_NAME | - | Área de trabajo para la capa oro. |
| Variable | METADATA_DATABASE | - | Nombre de la base de datos de metadatos. |
| Variable | SILVER_LAKEHOUSE_NAME | - | Lago de datos de la capa plata. |
| Variable | SILVER_WORKSPACE_NAME | - | Área de trabajo para la capa plata. |

# Flujo de despliegue

## Disparadores
- **push** y **pull_request** sobre la rama `main`.
- **workflow_dispatch** manual, permitiendo seleccionar el entorno (`DEV` o `PRO`).

## Trabajos

### 1. set-environment
- Determina el entorno de despliegue (`DEV` o `PRO`) según el tipo de ejecución (automática o manual).
- Expone la variable `current_env` para los siguientes pasos.

### 2. deploy
- Realiza el checkout del código y prepara el entorno Python.
- Instala dependencias desde `src/requirements.txt`.
- Inicia sesión en Fabric CLI usando credenciales federadas de Azure.
- Ejecuta el script de instalación (`scripts/cicd/install.py`) con las variables de entorno necesarias.
- Inicia sesión en Azure para la gestión de recursos.
- Publica artefactos mediante el script `publish.py`, pasando como parámetros el identificador del área de trabajo de control y el entorno (```DEV```,```PRO```) destino.
- Compila el proyecto de base de datos y obtiene la cadena de conexión.
- Publica el archivo DACPAC sobre la base de datos de Fabric creada previamente.