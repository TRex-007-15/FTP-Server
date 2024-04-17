import socket
import sys
import os
import struct

# Initialize socket stuff
TCP_IP = input("Enter server IP address: ")  # IP address of the server
TCP_PORT = 1456  # Same port as server
BUFFER_SIZE = 1024  # Standard choice
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def conn():
    # Connect to the server
    print("Sending server request...")
    try:
        s.connect((TCP_IP, TCP_PORT))
        print("Connection successful")
    except:
        print("Connection unsuccessful. Make sure the server is online.")

    # Authentication
    authenticated = False
    while not authenticated:
        s.send(b"AUTH")
        username = input("Enter your username: ")
        password = input("Enter your password: ")
        s.send(username.encode())
        s.send(password.encode())
        auth_status = s.recv(BUFFER_SIZE).decode()
        if auth_status == "1":
            authenticated = True
            print("Authentication successful")
        else:
            print("Authentication failed, please try again")

def upld(file_name):
    # Upload a file
    print("\nUploading file: {}...".format(file_name))
    try:
        # Check the file exists
        content = open(file_name, "rb")
    except:
        print("Couldn't open file. Make sure the file name was entered correctly.")
        return
    try:
        # Make upload request
        s.send(b"UPLD")
    except:
        print("Couldn't make server request. Make sure a connection has been established.")
        return
    try:
        # Wait for server acknowledgement then send file details
        # Wait for server ok
        s.recv(BUFFER_SIZE)
        # Send file name size and file name
        s.send(struct.pack("h", len(file_name)))
        s.send(file_name.encode())
        # Wait for server ok then send file size
        s.recv(BUFFER_SIZE)
        s.send(struct.pack("i", os.path.getsize(file_name)))
    except:
        print("Error sending file details")
    try:
        # Send the file in chunks defined by BUFFER_SIZE
        # Doing it this way allows for unlimited potential file sizes to be sent
        l = content.read(BUFFER_SIZE)
        print("\nSending...")
        while l:
            s.send(l)
            l = content.read(BUFFER_SIZE)
        content.close()
        # Get upload performance details
        upload_time = struct.unpack("f", s.recv(4))[0]
        upload_size = struct.unpack("i", s.recv(4))[0]
        print("\nSent file: {}\nTime elapsed: {}s\nFile size: {}b".format(file_name, upload_time, upload_size))
    except:
        print("Error sending file")
        return
    return

def list_files():
    # List the files available on the file server
    print("Requesting files...\n")
    try:
        # Send list request
        s.send(b"LIST")
    except:
        print("Couldn't make server request. Make sure a connection has been established.")
        return
    try:
        # First get the number of files in the directory
        number_of_files = struct.unpack("i", s.recv(4))[0]
        # Then enter into a loop to receive details of each, one by one
        for i in range(int(number_of_files)):
            # Get the file name size first to slightly lessen amount transferred over socket
            file_name_size = struct.unpack("i", s.recv(4))[0]
            file_name = s.recv(file_name_size).decode()
            # Also get the file size for each item in the server
            file_size = struct.unpack("i", s.recv(4))[0]
            print("\t{} - {}b".format(file_name, file_size))
            # Make sure that the client and server are synchronized
            s.send(b"1")
        # Get total size of directory
        total_directory_size = struct.unpack("i", s.recv(4))[0]
        print("Total directory size: {}b".format(total_directory_size))
    except:
        print("Couldn't retrieve listing")
        return
    try:
        # Final check
        s.send(b"1")
        return
    except:
        print("Couldn't get final server confirmation")
        return

def dwld(file_name):
    # Download given file
    print("Downloading file: {}".format(file_name))
    try:
        # Send server request
        s.send(b"DWLD")
    except:
        print("Couldn't make server request. Make sure a connection has been established.")
        return
    try:
        # Wait for server ok, then make sure file exists
        s.recv(BUFFER_SIZE)
        # Send file name length, then name
        s.send(struct.pack("h", len(file_name)))
        s.send(file_name.encode())
        # Get file size (if exists)
        file_size = struct.unpack("i", s.recv(4))[0]
        if file_size == -1:
            # If file size is -1, the file does not exist
            print("File does not exist. Make sure the name was entered correctly")
            return
    except:
        print("Error checking file")
    try:
        # Send ok to receive file content
        s.send(b"1")
        # Enter loop to receive file
        output_file = open(file_name, "wb")
        bytes_received = 0
        print("\nDownloading...")
        while bytes_received < file_size:
            # Again, file broken into chunks defined by the BUFFER_SIZE variable
            l = s.recv(BUFFER_SIZE)
            output_file.write(l)
            bytes_received += len(l)
        output_file.close()
        print("Successfully downloaded {}".format(file_name))
        # Tell the server that the client is ready to receive the download performance details
        s.send(b"1")
        # Get performance details
        time_elapsed = struct.unpack("f", s.recv(4))[0]
        print("Time elapsed: {}s\nFile size: {}b".format(time_elapsed, file_size))
    except:
        print("Error downloading file")
        return
    return

def delf(file_name):
    # Delete specified file from file server
    print("Deleting file: {}...".format(file_name))
    try:
        # Send request, then wait for go-ahead
        s.send(b"DELF")
        s.recv(BUFFER_SIZE)
    except:
        print("Couldn't connect to server. Make sure a connection has been established.")
        return
    try:
        # Send file name length, then file name
        s.send(struct.pack("h", len(file_name)))
        s.send(file_name.encode())
    except:
        print("Couldn't send file details")
        return
    try:
        # Get confirmation that file does/doesn't exist
        file_exists = struct.unpack("i", s.recv(4))[0]
        if file_exists == -1:
            print("The file does not exist on server")
            return
    except:
        print("Couldn't determine file existence")
        return
    try:
        # Confirm user wants to delete file
        confirm_delete = input("Are you sure you want to delete {}? (Y/N)\n".format(file_name)).upper()
        # Make sure input is valid
        # Unfortunately python doesn't have a do while style loop, as that would have been better here
        while confirm_delete != "Y" and confirm_delete != "N" and confirm_delete != "YES" and confirm_delete != "NO":
            # If user input is invalid
            print("Command not recognized, try again")
            confirm_delete = input("Are you sure you want to delete {}? (Y/N)\n".format(file_name)).upper()
    except:
        print("Couldn't confirm deletion status")
        return
    try:
        # Send confirmation
        if confirm_delete == "Y" or confirm_delete == "YES":
            # User wants to delete file
            s.send(b"Y")
            # Wait for confirmation file has been deleted
            delete_status = struct.unpack("i", s.recv(4))[0]
            if delete_status == 1:
                print("File successfully deleted")
                return
            else:
                # Client will probably send -1 to get here, but an else is used as more of a catch-all
                print("File failed to delete")
                return
        else:
            s.send(b"N")
            print("Delete abandoned by user!")
            return
    except:
        print("Couldn't delete file")
        return

def quit():
    s.send(b"QUIT")
    # Wait for server go-ahead
    s.recv(BUFFER_SIZE)
    s.close()
    print("Server connection ended")
    return

print("\n\nWelcome to the FTP client.\n\nCall one of the following functions:\nCONN           : Connect to server\nUPLD file_path : Upload file\nLIST           : List files\nDWLD file_path : Download file\nDELF file_path : Delete file\nQUIT           : Exit")

while True:
    # Listen for a command
    prompt = input("\nEnter a command: ")
    if prompt[:4].upper() == "CONN":
        conn()
    elif prompt[:4].upper() == "UPLD":
        upld(prompt[5:])
    elif prompt[:4].upper() == "LIST":
        list_files()
    elif prompt[:4].upper() == "DWLD":
        dwld(prompt[5:])
    elif prompt[:4].upper() == "DELF":
        delf(prompt[5:])
    elif prompt[:4].upper() == "QUIT":
        quit()
        break
    else:
        print("Command not recognized; please try again")
