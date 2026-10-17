import subprocess

def run_fab_command(
        command: str,
        skip_errors: bool = False
):
    """
    Runs a Fabric command using the `ms-fabric-cli` library.
    
    Args:
        command (str): The command to run.
    Returns:
        None
    Raises:
        Exception: If the command fails to execute.
    """

    result = subprocess.run(
        ["fab", "-c", command], capture_output=True, text=True
    )

    if not (skip_errors) and (result.returncode > 0 or result.stderr):
        raise Exception(
            f"*ERROR*: ❌ Error running fab command. exit_code: '{result.returncode}'; stderr: '{result.stderr}'"
        )
    
    return result.stdout.strip().split("\n")[-1]  # Return the last line of output

def create_workspace(
    workspace_name: str, 
    capacity_name: str, 
    upns: list = None
):
    """
    Creates a new Fabric workspace.
    
    Parameters:
        workspace_name (str): The name of the workspace to create.
        capacity_name (str): The name of the capacity to assign to the workspace
        description (str): An optional description for the workspace.
    Returns:
        None
    """

    print(f"Creating workspace '{workspace_name}' in the capacity '{capacity_name}'")

    command = f"create /{workspace_name}.Workspace -P capacityName={capacity_name}"

    run_fab_command(command, skip_errors=True)

    if upns:
 
        upns = [x for x in upns if x.strip()]

        if len(upns) > 0:
            
            print(f"*INFO*: ▶️ Adding users to workspace '{workspace_name}'")
            
            for upn in upns:
                run_fab_command(
                    f"acl set -f /{workspace_name}.Workspace -I {upn} -R admin"
                )
    workspace_id = run_fab_command(
        f"get /{workspace_name}.Workspace -q id"
    )

    print(f"*INFO*: ✅ Workspace '{workspace_name}' created with ID: {workspace_id}")

    return workspace_id

def create_sqldatabase(
    workspace_name: str,
    database_name: str
):
    """
    Creates a new Fabric SQL database.
    
    Parameters:
        database_name (str): The name of the SQL database to create.
        workspace_name (str): The name of the workspace to associate with the SQL database.
    Returns:
        None
    """

    print(f"*INFO*: ▶️ Creating SQL database '{database_name}' in workspace '{workspace_name}'")

    command = f"create /{workspace_name}.Workspace/{database_name}.SQLDatabase"

    run_fab_command(command, skip_errors=True)

    database_id = run_fab_command(
        f"get /{workspace_name}.Workspace/{database_name}.SQLDatabase -q id"
    )
    
    print(f"*INFO*: ✅ SQL database '{database_name}' created with ID: {database_id}")

def create_lakehouse(
    workspace_name: str,
    lakehouse_name: str
):
    """
    Creates a new Fabric lakehouse.
    
    Parameters:
        lakehouse_name (str): The name of the lakehouse to create.
        workspace_name (str): The name of the workspace to associate with the lakehouse.
    Returns:
        None
    """

    print(f"*INFO*: ▶️ Creating lakehouse '{lakehouse_name}' in workspace '{workspace_name}'")

    command = f"create /{workspace_name}.Workspace/{lakehouse_name}.Lakehouse"

    run_fab_command(command, skip_errors=True)

    lakehouse_id = run_fab_command(
        f"get /{workspace_name}.Workspace/{lakehouse_name}.Lakehouse -q id"
    )
    
    print(f"*INFO*: ✅ Lakehouse '{lakehouse_name}' created with ID: {lakehouse_id}")

def create_shortcut(
    source_workspace_name: str,
    source_lakehouse_name: str,
    target_workspace_name: str,
    target_lakehouse_name: str,
    shortcut_name: str
):
    """
    Creates a shortcut in a Fabric lakehouse.

    Parameters:
        source_workspace_name (str): The name of the source workspace.
        source_lakehouse_name (str): The name of the source lakehouse.
        target_workspace_name (str): The name of the target workspace.
        target_lakehouse_name (str): The name of the target lakehouse.
        shortcut_name (str): The name of the shortcut to create.
    Returns:
        None
    """

    print(f"*INFO*: ▶️ Creating shortcut '{shortcut_name}' in lakehouse '{source_lakehouse_name}' of workspace '{source_workspace_name}' to lakehouse '{target_lakehouse_name}' in workspace '{target_workspace_name}'")

    command = f"ln /{source_workspace_name}.Workspace/{source_lakehouse_name}.Lakehouse/Files/{shortcut_name}.Shortcut \
                --type oneLake --target ../../{target_workspace_name}.Workspace/{target_lakehouse_name}.Lakehouse/Tables -f"

    run_fab_command(command, skip_errors=True)

    print(f"*INFO*: ✅ Shortcut '{shortcut_name}' created successfully.")