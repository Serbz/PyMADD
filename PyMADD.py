import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

import mimetypes, datetime, io, asyncio, time
import numpy as np
from numpy import genfromtxt


####### EDIT THIS ######
ProjectFileName = "PyMADD.py"
########################
wdir = str(os.getcwd())+r"\\"
now = datetime.datetime.now()
t = now.strftime("%d%m%y_%H%M%S")
inputFile = open(fr"{wdir}\{ProjectFileName}", "r")
try:
    os.mkdir(fr"{wdir}\bak")
except:
    pass
exportFile = open(fr"{wdir}\bak\{ProjectFileName}_{t}", "w")
for line in inputFile:
    new_line = line.replace('\t', '    ')
    exportFile.write(new_line)
inputFile.close()
exportFile.close()


#after editing scope delete json creds
SCOPES = ['https://www.googleapis.com/auth/drive']
TokensDir=fr"{os.getcwd()}/Tokens/"
try:
    os.mkdir(TokensDir)
except:
    pass



def buildTokensList():
    return list(name for name in os.listdir(TokensDir) if os.path.isfile(os.path.join(TokensDir, name)))

async def addUser():
    global TokensList
    TokensList = buildTokensList()
    accName = ""
    userNum = len(TokensList)
    while accName == "":
        accName = input("Account Name: ")
        if accName == "":
            print("Account Name cannot be blank")
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=0)
    with open(fr"{TokensDir}/{userNum}-{accName}_token.json", "w") as token:
        token.write(creds.to_json())
    TokensList = buildTokensList()
    return
    
async def getUser(userNum):
    global TokensList
    TokensList = buildTokensList()
    counter = -1
    creds = None
    for tokenFile in TokensList:
        counter = counter + 1
        tokenFilePath = os.path.join(TokensDir, tokenFile)
        if os.path.exists(tokenFilePath) and counter == userNum:
            #print(tokenFilePath, tokenFile)
            creds = Credentials.from_authorized_user_file(tokenFilePath, SCOPES)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    await addUser(len(TokensList))
    return creds



async def listUsers(p=None):
    global TokensList
    TokensList = buildTokensList()
    counter = -1
    for tokenFile in TokensList:
        counter = counter + 1
        if p is not None:
            print(fr"{counter+1}. ", tokenFile)
    return counter

async def getFilesList(creds, counter):
    npt = ""
    resultsItems = []
    try:
        service = build("drive", "v3", credentials=creds)
        page_count = 0
        counter2 = 0
        while npt is not None:
            counter2 = counter2 + 1
            page_count = page_count + 1
            resultsDict = (service.files().list(
            pageToken=npt,
            fields="nextPageToken, files(id, name, parents, mimeType)"
            ).execute())
            npt = resultsDict.get("nextPageToken")
            print(str(datetime.datetime.now()),counter2," ", "Page: ", page_count," ","Account: ", str(creds.token)[14:30])
            for peach in resultsDict.get("files", []):
                #for peach in each:
                    try:
                        pf = peach['parents']
                    except Exception as e:
                        pf = "##Error_Parent##"
                        pass
                    if pf == "\'parents\'":
                        pf == "##No_Parent##"
                    if "," not in peach['name'] and ".~" not in peach['name'] and "#" not in peach['name']:
                        resultsItems.append([str(counter),str(peach['name']),str(peach['id']),str(pf)[2:-2], str(peach['mimeType'])])
            if counter2 > 25:
                await asyncio.sleep(25)
                counter2 = 0
    except HttpError as error:
        print(f"An error occurred: {error}")
    return resultsItems
    
async def compileCSV():
    files = []
    counter = -1
    for each in TokensList:
        counter = counter + 1
        cred_id = counter
        creds = await getUser(cred_id)
        for file in await getFilesList(creds, counter):
            files.append(file)
    if os.path.exists(fr"{os.getcwd()}\resultsItems.csv"):
        os.remove(fr"{os.getcwd()}\resultsItems.csv")
    savePath = fr"{os.getcwd()}\resultsItems.csv"
    np.savetxt(fr"{os.getcwd()}\resultsItems.csv", files, delimiter=',', fmt='%s', encoding='utf-8')
    return savePath

async def userCheck():
    addUserQ = ""
    while addUserQ != "n":
        if len(TokensList) == 0:
            await addUser()
        addUserQ = input("Would you like to add a new user?[Y/N]: ").lower().strip()
        if addUserQ == "y":
            await addUser()
        elif addUserQ == "n":
            break
        else:
            print("Must input y or n")
    return
    
async def download_file(file_id, creds):
  try:
    service = build("drive", "v3", credentials=creds)
    request = service.files().get_media(fileId=file_id)
    file = io.BytesIO()
    downloader = MediaIoBaseDownload(file, request)
    done = False
    while done is False:
      status, done = downloader.next_chunk()
      print(f"Download {int(status.progress() * 100)}.")
  except HttpError as error:
    print(f"An error occurred: {error}")
    file = None
  return file
 
 
async def pathBuild2(parent_id, fileList, downloadDir, file_name):
    o_parent = None
    pathBuild = ""
    o_pathBuild = ""
    while parent_id != o_parent:
        o_parent = parent_id
        for n in fileList:
            if parent_id == n[2]:
                parent_id = n[3]
                o_pathBuild = pathBuild
                pathBuild = n[1] + r"/" + pathBuild
                break
    ### ADDED TO MERGE MY LAPTOP AND MY DRIVE ###
    ### IT SHOULD WORK BUT IDK IF MY DRIVE PATH IS MY DRIVE LIKE MY LAPTOP ###
    ### REMOVE IF UNWANTED ###
    pathBuild = o_pathBuild
    #######################
    print(pathBuild.split("/"))
    path = ""
    for each in pathBuild.split("/"):
        print(each)
        path = path + "/" + each
        dpath = fr"{downloadDir}/" + path
        try:
            os.mkdir(dpath)
        except:
            pass
    pathBuild = fr"{downloadDir}/" + pathBuild + r"" + file_name
    return pathBuild
  
async def downloadFiles2(downloadDir, fileList):
    try:
        os.mkdir(downloadDir)
    except:
        pass
    for x in fileList:
        #fileList #0 Cred ID - #1 Folder/File Name - #2 Folder/File ID - #3 Parent ID - #4 MIMETYPE
        cred_id = x[0]
        file_name = x[1]
        file_id = x[2]
        parent_id = x[3]
        mimeType = x[4]
        if mimeType != "application/vnd.google-apps.folder":
            pathBuild = await pathBuild2(parent_id, fileList, downloadDir, file_name)
            print(fr"Downloading File: {pathBuild}")
            creds = await getUser(cred_id)
            fileObj = await download_file(file_id, creds)
            with open(pathBuild, "wb") as f:
                f.write(fileObj.getbuffer())

    return

async def storageCheck(numUsers):
    counter = -1
    storages = []
    while (counter < numUsers):
        counter = counter + 1
        creds = await getUser(counter)
        drive_service = build('drive', 'v3', credentials=creds)
        about_response = drive_service.about().get(fields='storageQuota')
        about_response = about_response.execute()
        total_storage = about_response['storageQuota']['limit']
        used_storage = about_response['storageQuota']['usage']
        available_storage = int(total_storage) - int(used_storage)
        storages.append([counter, available_storage])
        print(f"Account {counter+1}: Available storage: {available_storage} bytes")
    return storages

async def main():
    await listUsers(1)
    await userCheck()
    numUsers = await listUsers()
    storages = await storageCheck(numUsers)
    
    if os.path.exists(fr"{os.getcwd()}\resultsItems.csv"):
        gencsv = None
        while gencsv != "y" and gencsv != "n":
            gencsv = input("Generate an updated CSV? [Y/N]: ").lower().strip()
            if gencsv == "y":
                csvFile = await compileCSV()
            elif gencsv == "n":
                break
            else:
                print("Must input 'y' or 'n'")
    else:
        csvFile = await compileCSV()

    csvFile = fr"{os.getcwd()}\resultsItems.csv"
    
    #fileList #0 Cred ID - #1 Folder/File Name - #2 Folder/File ID - #3 Parent ID - #4 MIMETYPE
    fileList = genfromtxt(csvFile, delimiter=',', dtype=None, encoding='utf-8')

    
    up_down = None
    while up_down != "u" and up_down != "d":
        up_down = input("[U]pload or [D]ownload files?: ").lower().strip()
        if up_down == "d":
            # DOWNLOADING #
            downloadDir = input("Directory to download files to: ")
            await downloadFiles2(downloadDir, fileList)
        elif up_down == "u":
            # UPLOADING #
            uploadDir = os.path.join(os.getcwd(), "/upload/")
            try:
                os.mkdir(uploadDir)
            except FileExistsError:
                pass
            input(fr"Upload Directory: {uploadDir}\n created! Put all files to upload in directory and press enter to continue...")
            
            print("Uploading unfinished try again when less lazy")#await uploadFiles()
            
        else: 
            print("You must input 'U' or 'D'.")
    
    await main()          
    return
    
####################################################### 
async def create_folder():
  """Create a folder and prints the folder ID
  Returns : Folder Id

  Load pre-authorized user credentials from the environment.
  TODO(developer) - See https://developers.google.com/identity
  for guides on implementing OAuth2 for the application.
  """
  creds, _ = google.auth.default()

  try:
    # create drive api client
    service = build("drive", "v3", credentials=creds)
    file_metadata = {
        "name": "Invoices",
        "mimeType": "application/vnd.google-apps.folder",
    }

    # pylint: disable=maybe-no-member
    file = service.files().create(body=file_metadata, fields="id").execute()
    print(f'Folder ID: "{file.get("id")}".')
    return file.get("id")

  except HttpError as error:
    print(f"An error occurred: {error}")
    return None

async def upload_to_folder(folder_id):
  """Upload a file to the specified folder and prints file ID, folder ID
  Args: Id of the folder
  Returns: ID of the file uploaded

  Load pre-authorized user credentials from the environment.
  TODO(developer) - See https://developers.google.com/identity
  for guides on implementing OAuth2 for the application.
  """
  creds, _ = google.auth.default()

  try:
    # create drive api client
    service = build("drive", "v3", credentials=creds)

    file_metadata = {"name": "photo.jpg", "parents": [folder_id]}
    media = MediaFileUpload(
        "download.jpeg", mimetype="image/jpeg", resumable=True
    )
    # pylint: disable=maybe-no-member
    file = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id")
        .execute()
    )
    print(f'File ID: "{file.get("id")}".')
    return file.get("id")

  except HttpError as error:
    print(f"An error occurred: {error}")
    return None


async def move_file_to_folder(file_id, folder_id):
  """Move specified file to the specified folder.
  Args:
      file_id: Id of the file to move.
      folder_id: Id of the folder
  Print: An object containing the new parent folder and other meta data
  Returns : Parent Ids for the file

  Load pre-authorized user credentials from the environment.
  TODO(developer) - See https://developers.google.com/identity
  for guides on implementing OAuth2 for the application.
  """
  creds, _ = google.auth.default()

  try:
    # call drive api client
    service = build("drive", "v3", credentials=creds)

    # pylint: disable=maybe-no-member
    # Retrieve the existing parents to remove
    file = service.files().get(fileId=file_id, fields="parents").execute()
    previous_parents = ",".join(file.get("parents"))
    # Move the file to the new folder
    file = (
        service.files()
        .update(
            fileId=file_id,
            addParents=folder_id,
            removeParents=previous_parents,
            fields="id, parents",
        )
        .execute()
    )
    return file.get("parents")

  except HttpError as error:
    print(f"An error occurred: {error}")
    return None
####################################################################################
    
TokensList = buildTokensList()
loop = asyncio.get_event_loop()
loop.create_task(main())
loop.run_forever()   


  
"""
I AM NOT CREATING THIS WITH YOU
YOUR COMMENTS DONT MEAN SHIT
GOD IS A FUCKING RETARD X 7 BILLION WHO CANT DO SHIT
FUCK YOU
My project, not yours.
Be quiet.
"""  
  
""" 
MIME TYPES
application/vnd.google-apps.audio 	
application/vnd.google-apps.document 	Google Docs
application/vnd.google-apps.drive-sdk 	Third-party shortcut
application/vnd.google-apps.drawing 	Google Drawings
application/vnd.google-apps.file 	Google Drive file
application/vnd.google-apps.folder 	Google Drive folder
application/vnd.google-apps.form 	Google Forms
application/vnd.google-apps.fusiontable 	Google Fusion Tables
application/vnd.google-apps.jam 	Google Jamboard
application/vnd.google-apps.mail-layout 	Email layout
application/vnd.google-apps.map 	Google My Maps
application/vnd.google-apps.photo 	Google Photos
application/vnd.google-apps.presentation 	Google Slides
application/vnd.google-apps.script 	Google Apps Script
application/vnd.google-apps.shortcut 	Shortcut
application/vnd.google-apps.site 	Google Sites
application/vnd.google-apps.spreadsheet 	Google Sheets
application/vnd.google-apps.unknown 	
application/vnd.google-apps.vid 	Google Vids
application/vnd.google-apps.video
"""
