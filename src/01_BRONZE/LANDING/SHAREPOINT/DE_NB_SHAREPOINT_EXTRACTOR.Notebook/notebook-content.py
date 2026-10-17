# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "jupyter",
# META     "jupyter_kernel_name": "python3.11"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************

%pip install fastexcel
%pip install unidecode

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

import requests
import polars as pl
from io import StringIO
import notebookutils
import json
from ast import literal_eval
from urllib.parse import unquote
import re
from datetime import datetime
from zoneinfo import ZoneInfo
from unidecode import unidecode

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# PARAMETERS CELL ********************

site_id = ""
resource = ""
list_name = ""
kv = ""
client_id_secret_name = ""
client_secret_name = ""
tenant_secret_name = ""
url_root_folder = ""
url_subfolder = ""
filter_patterns = ""
patterns_files = ""

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

class SharePointExtractor:
    """
    Extracts, processes, and moves files from a SharePoint site using Microsoft Graph API.

    This class authenticates with Azure Key Vault credentials, lists folders and files in a SharePoint drive,
    filters files by pattern, downloads and processes Excel files, writes them to a lakehouse, and moves processed files
    to a 'Processed' folder.

    ...

    Attributes
    ----------
        - resource (str): Azure resource identifier.
        - site_id (str): SharePoint site ID.
        - list_name (str): Name of the SharePoint drive/list.
        - kv (str): Azure Key Vault name.
        - client_id_secret_name (str): Secret name for client ID in Key Vault.
        - client_secret_name (str): Secret name for client secret in Key Vault.
        - tenant_secret_name (str): Secret name for tenant ID in Key Vault.
        - url_root_folder (str): Root folder path in SharePoint.
        - url_subfolder (str): Subfolder path in SharePoint.
        - filter_patterns (str): Regex pattern to filter files.
        - patterns (str): JSON string with file type patterns and metadata.

    Methods
    -------
        - get_access_token(): Authenticates and retrieves a Microsoft Graph API access token.
        - get_drive_id(): Gets the drive ID for the specified SharePoint list.
        - list_folders(): Lists folders in the SharePoint drive matching the root and subfolder.
        - create_processed_folders(folders): Ensures a 'Processed' folder exists in each folder.
        - list_folder_contents(folders): Lists and filters files in the given folders.
        - download_files(files): Downloads, processes, writes, and moves files.
        - run(): Orchestrates the extraction and processing workflow.
    """
    def __init__(self, resource, site_id, list_name, kv, 
                    client_id_secret_name, client_secret_name, tenant_secret_name, url_root_folder, url_subfolder, filter_patterns, patterns):
        self.resource = resource
        self.site_id = site_id
        self.list_name = list_name
        self.kv = kv
        self.client_id_secret_name = client_id_secret_name
        self.client_secret_name = client_secret_name
        self.tenant_secret_name = tenant_secret_name
        self.base_url = "https://graph.microsoft.com/v1.0/"
        self.url_root_folder = url_root_folder
        self.url_subfolder = url_subfolder
        self.filter_patterns = filter_patterns
        self.patterns = patterns
        # Authenticate and get access token and drive id
        self.access_token = self.get_access_token()
        self.drive_id = self.get_drive_id()
    
    def get_access_token(self) -> str:
        notebookutils.credentials.getToken("keyvault")
        # Retrieve secrets from Key Vault
        client_id = notebookutils.credentials.getSecret(f"https://{self.kv}.vault.azure.net/", f"{self.client_id_secret_name}")
        client_secret = notebookutils.credentials.getSecret(f"https://{self.kv}.vault.azure.net/", f"{self.client_secret_name}")
        tenant_id = notebookutils.credentials.getSecret(f"https://{self.kv}.vault.azure.net/", f"{self.tenant_secret_name}")

        # Prepare OAuth2 request for Microsoft Graph
        base_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"  
        data = {
            "grant_type": "client_credentials",
            "client_id": f"{client_id}@{tenant_id}",
            "scope": "https://graph.microsoft.com/.default",
            "client_secret": client_secret
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"} 
        try:
            # Request the access token
            response = requests.post(base_url, headers=headers, data=data)
            response.raise_for_status()
            bearer_token = response.json()['access_token']
            
            return bearer_token
        except Exception as err:
            raise RuntimeError(f"Failed to obtain access token: {err}")
    
    def get_drive_id(self) -> str:
        """
        Retrieves the drive ID for the specified SharePoint list.
        Returns
        -------
        str
            The drive ID.
        """
        drive_id = ""
        drives_url = f"{self.base_url}sites/{self.site_id}/drives"
        try:
            response = requests.get(drives_url, headers={'Authorization': f'Bearer {self.access_token}'})
            response.raise_for_status()
            drives = response.json().get('value', [])
            for drive in drives:
                if drive['name'] == self.list_name:
                    return drive['id']
            raise ValueError(f"Drive with name '{self.list_name}' not found.")
        except Exception as e:
            raise RuntimeError(f"Failed to retrieve drive ID: {e}")

    def list_folders(self) -> list:
        """
        Lists folders in the SharePoint drive matching the root and subfolder.
        Returns
        -------
        list of dict
            List of folders with their eTag and path.
        """
        next_page = True
        folders_url = f"{self.base_url}sites/{self.site_id}/lists/{self.list_name}/items?$filter=contentType/name eq 'Carpeta'"
        folders_list = []

        print(f"*INFO*: ▶️ List | {self.list_name} | {self.drive_id}")

        while(next_page):
            try:
                response = requests.get(folders_url, headers={"Authorization": f"Bearer {self.access_token}"})
                response.raise_for_status()
                items = response.json()
            except Exception as err:
                print(f"*ERROR*: ❌ Error fetching folders: {err}")
                break
            
            next_page = "@odata.nextLink" in items
            if next_page:
                folders_url = items["@odata.nextLink"]
            
            if "value" in items:
                for item in items['value']:
                    item_web_url = unquote(item['webUrl'])
                    if self.url_root_folder in item_web_url and item_web_url.endswith(self.url_subfolder):
                        try:
                            match = re.search(f"{self.url_root_folder}(.*?){self.url_subfolder}", item_web_url)
                            if match:
                                folders_list.append({
                                    'eTag': item['eTag'].split(',')[0].replace('"', ''),
                                    'path': match.group(1) + self.url_subfolder
                                })
                        except Exception as err:
                            print(f"*WARNING*: ⚠️ Could not extract folder path from {item_web_url}: {err}") 
        if folders_list:
            print(f"*INFO*: ▶️ {len(folders_list)} folders to process.")
        else:
            print(f"*INFO*: ✅ No folders to process.")
        
        return folders_list
    
    def create_processed_folders(self, folders) -> list:
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        body = {
            "name": "Processed",
            "folder": { },
            "@microsoft.graph.conflictBehavior": "fail"
        }
        new_folders_list = []

        if folders:
            
            print(f"*INFO*: ▶️ Creating folders to processed files...")

            for folder in folders:
                url = f"{self.base_url}sites/{self.site_id}/drives/{self.drive_id}/items/{folder['eTag']}/children"
                response = requests.post(url, headers=headers, json=body)
                output = response.json()

                etag = folder['eTag']

                if response.status_code == 201:
                    print(f"*INFO*: ✅ Folder (id={output['id']}) created successfully.")

                    new_folders_list.append({
                            'eTag': etag,
                            'path': folder['path'],
                            'processedFolderId': output['id']
                    })

                else:
                    try:
                        response = requests.get(url, headers={"Authorization": f"Bearer {self.access_token}"}).json()
                        processed_folder_id = [ processed_folder['id'] for processed_folder in response['value'] if processed_folder['name'] == "Processed"][0]

                        print(f"*ERROR*: ❌ Folder (id={processed_folder_id}) already exists.")

                        new_folders_list.append(
                            {
                                'eTag': etag, 
                                'path': folder['path'], 
                                'processedFolderId': processed_folder_id
                            }
                        )
                    except Exception as err:
                        print(f"*ERROR*: ❌ Unable to create Processed subfolder on folder {etag}.") 
        
        return new_folders_list
    
    def list_folder_contents(self, folders) -> list:
        """
        Lists and filters files in the given folders according to the filter_patterns.
        Parameters
        ----------
        folders : list of dict
            List of folders to scan.
        Returns
        -------
        list of dict
            List of files with metadata for processing.
        """
        files_list = []

        if folders:
            for folder in folders:
                folder_contents_url = f"{self.base_url}sites/{self.site_id}/drives/{self.drive_id}/items/{folder['eTag']}/children"
                response = requests.get(folder_contents_url, headers={'Authorization': f'Bearer {self.access_token}'})
                folder_contents = response.json()
                
                if 'value' in folder_contents:
                    for item in folder_contents['value']:
                        if 'file' in item:
                            item_name = item['name']

                            matches = re.search(self.filter_patterns, item_name, re.IGNORECASE)

                            if matches:
                                files_list.append(
                                    {
                                        'file_pattern_name': matches[0].upper().replace('_', ''), 
                                        'source_file_extension': item_name[item_name.rfind('.'):], 
                                        'id': item['id'], 
                                        'name': item_name,
                                        'path': folder['path'],
                                        'processedFolderId': folder['processedFolderId']
                                    }
                                )
        if files_list:
            patterns = pl.read_json(StringIO(self.patterns))
            filtered_files = pl.DataFrame(files_list).join(patterns, on="file_pattern_name")
            files_list = filtered_files.rows(named=True)

        print(f"*INFO*: ▶️ {len(files_list)} files to process.")
        
        return files_list

    def download_files(self, files) -> None:
        """
        Downloads, processes, writes, and moves files from SharePoint.
        Parameters
        ----------
        files : list of dict
            List of files to process.
        """
        if files:
            for file in files:
                file_url = f"{self.base_url}sites/{self.site_id}/drives/{self.drive_id}/items/{file['id']}/content"
                response = requests.get(file_url, headers={'Authorization': f'Bearer {self.access_token}'})

                if response.status_code == 200:

                    # EXCEL
                    
                    if file['source_file_extension'] == ".xlsx":
                        file_name = file['name']
                        sheet_index = file['sheet_id']
                        try:
                            df = pl.read_excel(response.content, sheet_id=sheet_index, has_header=False, columns=literal_eval(file['columns']), read_options={"skip_rows": 1, "schema_sample_rows": None, "dtypes": literal_eval(file['column_types']) })
                            df = df.rename(json.loads(file['column_mapping']))
                            print(f"\n*INFO*: ✅ File {file_name} has been readed successfully.")

                            local_time = datetime.now(tz=ZoneInfo("Europe/Madrid"))

                            df = df.with_columns([
                                pl.lit(file_name).alias("file_name")
                            ]).with_columns([
                                pl.lit(local_time.strftime("%Y-%m-%dT%H:%M:%S")).alias("loaded_at")
                            ])

                            # PERSONALIZATION, REPLACE ME IF THERE ARE DIFFERENT REQUIREMENTS
                            # ---------------------------------------------------------------

                            file_date = None
                            country_name = None
                            waste_type = None

                            try:
                                res = True

                                try:
                                    res = bool(datetime.strptime(file_name.split('_')[0], "%Y-%m-%d"))
                                except ValueError:
                                    res = False

                                if res:
                                    file_date = file_name.split('_')[0]
                            except Exception as err:
                                print(f"*ERROR*: ❌ Unable to get file date from {file_name}, error message: {err=}")
                            
                            try:
                                countries = ["ANGOLA", "ARGENTINA", "AUSTRALIA", "BRASIL", "CAMERUN", "CHILE",
                                                "COLOMBIA", "DOMINICANA", "ESPANA", "ESTADOS UNIDOS", "HONDURAS",
                                                "ITALIA", "MEXICO", "PANAMA", "PERU", "PORTUGAL", "REINO UNIDO", "URUGUAY"]
                                
                                country_name_aux = file_name.split('_')[2].upper()

                                if unidecode(country_name_aux) in countries:
                                    country_name = country_name_aux
                            except Exception as err:
                                print(f"*ERROR*: ❌ Unable to get country name from {file_name}, error message: {err=}")

                            try:                            
                                default_path = "/lakehouse/default/Files/"

                                if file['file_pattern_name'] == "MANUAL" and sheet_index == 1:
                                    waste_type = "NO PELIGROSO"
                                    df = df.with_columns([
                                        pl.lit(waste_type).alias("tipo")
                                    ])
                                    destination_folder_path = f"{default_path}{file['destination_root_path']}{file['path']}/NO PELIGROSOS/Pending/{local_time.year}/{local_time.strftime('%m')}/{local_time.strftime('%d')}/"
                                elif file['file_pattern_name'] == "MANUAL" and sheet_index == 2:
                                    waste_type = "PELIGROSO"
                                    df = df.with_columns([
                                        pl.lit(waste_type).alias("tipo")
                                    ])
                                    destination_folder_path = f"{default_path}{file['destination_root_path']}{file['path']}/PELIGROSOS/Pending/{local_time.year}/{local_time.strftime('%m')}/{local_time.strftime('%d')}/"
                                else:
                                    destination_folder_path = f"{default_path}{file['destination_root_path']}{file['path']}/Pending/{local_time.year}/{local_time.strftime('%m')}/{local_time.strftime('%d')}/"

                                # ---------------------------------------------------------------
                            except Exception as err:
                                print(f"*ERROR*: ❌ Unable to get waste type from {file_name}, error message: {err=}")

                            df = df.with_columns([
                                pl.lit(country_name).alias("pais")
                            ]).with_columns([
                                pl.lit(file_date).alias("fecha_fichero")
                            ])
                            
                            try:
                                notebookutils.fs.mkdirs(destination_folder_path)

                                destination_file_name = re.sub('[^A-Za-z0-9]+', '_', unidecode(file_name[:file_name.rfind('.')])) + file['destination_file_extension']
                                
                                df.write_parquet(f"{destination_folder_path}{destination_file_name}", compression="snappy")
                                print(f"*INFO*: ✅ File {destination_file_name} has been written successfully. Path {destination_folder_path}")

                                # Move processed file
                                move_file_url = f"{self.base_url}sites/{self.site_id}/drives/{self.drive_id}/items/{file['id']}"
                                headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
                                body = {
                                    "parentReference": {"id": f"{file['processedFolderId']}"},
                                    "name": f"{file_name}",
                                    "@microsoft.graph.conflictBehavior": "replace"
                                }

                                response = requests.patch(move_file_url, headers=headers, json=body)

                                if response.status_code == 200:
                                    print(f"*INFO*: ✅ File {file_name} has been moved to Processed folder successfully.\n")
                                else:
                                    print(f"*ERROR*: ❌ El fichero {file_name} has not been moved to Processed folder.\n")

                            except Exception as err:
                                print(f"*ERROR*: ❌ Unable to write {destination_file_name} file, error message: {err=}")
                        except Exception as err:
                            print(f"*ERROR*: ❌ Unable to read {file_name}, error message: {err=}")

        else:
            print(f"*INFO*: ✅ No files to process.")
    
    def run(self):
        pending_folders = self.list_folders()
        pending_processed_folders = self.create_processed_folders(pending_folders)
        files = self.list_folder_contents(pending_processed_folders)
        self.download_files(files)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }

# CELL ********************

extractor = SharePointExtractor(resource, site_id, list_name, kv, 
                                    client_id_secret_name, client_secret_name, tenant_secret_name, 
                                    url_root_folder, url_subfolder, filter_patterns, patterns_files)
extractor.run()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "jupyter_python"
# META }
