import json
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive


def save_template(name, exercises):
    with open(f"{name}.json", "w") as f:
        json.dump(exercises, f)

    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()  # Аутентификация
    drive = GoogleDrive(gauth)
    file = drive.CreateFile({"title": f"{name}.json"})
    file.SetContentFile(f"{name}.json")
    file.Upload()


def load_template(name):
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()
    drive = GoogleDrive(gauth)
    file_list = drive.ListFile().GetList()
    for file in file_list:
        if file["title"] == f"{name}.json":
            file.GetContentFile(f"{name}.json")
            with open(f"{name}.json", "r") as f:
                return json.load(f)
    return None