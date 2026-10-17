import os
from utils import *

CAPACITY_NAME = os.getenv("FAB_CAPACITY")
CONTROL_WORKSPACE_NAME = os.getenv("CONTROL_WORKSPACE_NAME")
METADATA_DATABASE = os.getenv("METADATA_DATABASE")
BRONZE_WORKSPACE_NAME = os.getenv("BRONZE_WORKSPACE_NAME")
BRONZE_LAKEHOUSE_NAME  = os.getenv("BRONZE_LAKEHOUSE_NAME")
SILVER_WORKSPACE_NAME  = os.getenv("SILVER_WORKSPACE_NAME")
SILVER_LAKEHOUSE_NAME  = os.getenv("SILVER_LAKEHOUSE_NAME")
GOLD_WORKSPACE_NAME  = os.getenv("GOLD_WORKSPACE_NAME")
GOLD_LAKEHOUSE_NAME  = os.getenv("GOLD_LAKEHOUSE_NAME")
FAB_ADMIN_UPNS = os.getenv("FAB_ADMIN_UPNS")

if FAB_ADMIN_UPNS:
    FAB_ADMIN_UPNS = [upn.strip() for upn in FAB_ADMIN_UPNS.split(",")]

# Create control workspace
workspace_id = create_workspace(
    workspace_name = CONTROL_WORKSPACE_NAME,
    capacity_name = CAPACITY_NAME,
    upns = FAB_ADMIN_UPNS
)

# Set the workspace ID as an environment variable for GitHub Actions
echo_statement="echo \"CONTROL_WORKSPACE_ID=" + workspace_id + "\" >> $GITHUB_ENV"
os.system(echo_statement)

# Create metadata database
create_sqldatabase(
    workspace_name = CONTROL_WORKSPACE_NAME,
    database_name = METADATA_DATABASE
)

# Create bronze workspace and lakehouse
create_workspace(
    workspace_name = BRONZE_WORKSPACE_NAME,
    capacity_name = CAPACITY_NAME,
    upns = FAB_ADMIN_UPNS
)

create_lakehouse(
    workspace_name = BRONZE_WORKSPACE_NAME,
    lakehouse_name = BRONZE_LAKEHOUSE_NAME
)

# Create silver workspace and lakehouse
create_workspace(
    workspace_name = SILVER_WORKSPACE_NAME,
    capacity_name = CAPACITY_NAME,
    upns = FAB_ADMIN_UPNS
)

create_lakehouse(
    workspace_name = SILVER_WORKSPACE_NAME,
    lakehouse_name = SILVER_LAKEHOUSE_NAME
)

# Create gold workspace and lakehouse
create_workspace(
    workspace_name = GOLD_WORKSPACE_NAME,
    capacity_name = CAPACITY_NAME,
    upns = FAB_ADMIN_UPNS
)

create_lakehouse(
    workspace_name = GOLD_WORKSPACE_NAME,
    lakehouse_name = GOLD_LAKEHOUSE_NAME
)

# Create 01_BRONZE shortcut
create_shortcut(
    source_workspace_name = SILVER_WORKSPACE_NAME,
    source_lakehouse_name = SILVER_LAKEHOUSE_NAME,
    target_workspace_name = BRONZE_WORKSPACE_NAME,
    target_lakehouse_name = BRONZE_LAKEHOUSE_NAME,
    shortcut_name = "01_BRONZE"
)

# Create 01_BRONZE shortcut
create_shortcut(
    source_workspace_name = GOLD_WORKSPACE_NAME,
    source_lakehouse_name = GOLD_LAKEHOUSE_NAME,
    target_workspace_name = SILVER_WORKSPACE_NAME,
    target_lakehouse_name = SILVER_LAKEHOUSE_NAME,
    shortcut_name = "02_SILVER"
)