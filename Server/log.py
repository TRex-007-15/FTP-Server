from datetime import datetime

def log_event(event_type, message):
    with open("log.txt", "a") as logfile:
        logfile.write(f"{datetime.now()} - {event_type.upper()}: {message}\n")

def login_event(username):
    log_event("login", f"User '{username}' logged in")

def delete_event(filename,username):
    log_event("delete", f"File '{filename}' was deleted ' by ' {username}")

def upload_event(uploaded_file,username):
    log_event("upload", f"Uploaded file '{uploaded_file}' by '{username}'")

def download_event(downloaded_file, username):
    log_event("download", f"Downloaded file '{downloaded_file}' by '{username}'")

def logout_event(username):
    log_event("logout",f"User '{username}' logged out")

def read_log():
    with open("log.txt","+r") as logfile:
        data = logfile.read()
        return data
def clear_log():
    open('log.txt', 'w').close()

