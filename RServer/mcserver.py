import socket
import sys
import os
import struct
import time
import threading
import auth
import log as log
# Initialize socket stuff
TCP_IP = "192.168.0.136"  # Listen on all available network interfaces
TCP_PORT = 1456  # Just a random choice
BUFFER_SIZE = 1024  # Standard size
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((TCP_IP, TCP_PORT))
s.listen(5)  # Maximum number of queued connections

print("\nWelcome to the FTP server.\n\nTo get started, connect a client.")

# Function to handle each client connection
def handle_client(conn, addr):
    print("\nConnected to by address: {}".format(addr))

    def upld():
        # Send message once server is ready to receive file details
        conn.send(b"1")
        # Receive file name length, then file name
        file_name_size = struct.unpack("h", conn.recv(2))[0]
        file_name = conn.recv(file_name_size).decode()
        # Send message to let client know server is ready for document content
        conn.send(b"1")
        # Receive file size
        file_size = struct.unpack("i", conn.recv(4))[0]
        # Initialize and enter loop to receive file content
        start_time = time.time()
        output_file = open(file_name, "wb")
        # This keeps track of how many bytes we have received, so we know when to stop the loop
        bytes_received = 0
        print("\nReceiving...")
        while bytes_received < file_size:
            l = conn.recv(BUFFER_SIZE)
            output_file.write(l)
            bytes_received += len(l)
        output_file.close()
        print("\nReceived file: {}".format(file_name))
        # Send upload performance details
        conn.send(struct.pack("f", time.time() - start_time))
        conn.send(struct.pack("i", file_size))
        return file_name


    def list_files():
        print("Listing files...")
        try:
            # Get list of files in directory
            listing = os.listdir(os.getcwd())
            # Send over the number of files, so the client knows what to expect (and avoid some errors)
            conn.send(struct.pack("i", len(listing)))
            total_directory_size = 0
            # Send over the file names and sizes while totaling the directory size
            for filename in listing:
                filepath = os.path.join(os.getcwd(), filename)
                filesize = os.path.getsize(filepath)
                # File name size
                conn.send(struct.pack("i", len(filename.encode())))
                # File name
                conn.send(filename.encode())
                # File content size
                conn.send(struct.pack("i", filesize))
                total_directory_size += filesize
                # Make sure that the client and server are synchronized
                conn.recv(BUFFER_SIZE)
            # Sum of file sizes in directory
            conn.send(struct.pack("i", total_directory_size))
            # Final check
            conn.recv(BUFFER_SIZE)
            print("Successfully sent file listing")
        except Exception as e:
            print("Error listing files:", e)
            

    def dwld():
        conn.send(b"1")
        file_name_length = struct.unpack("h", conn.recv(2))[0]
        file_name = conn.recv(file_name_length).decode()
        if os.path.isfile(file_name):
            # Then the file exists, and send file size
            conn.send(struct.pack("i", os.path.getsize(file_name)))
        else:
            # Then the file doesn't exist, and send error code
            print("File name not valid")
            conn.send(struct.pack("i", -1))
            return
        # Wait for ok to send file
        conn.recv(BUFFER_SIZE)
        # Enter loop to send file
        start_time = time.time()
        print("Sending file...")
        content = open(file_name, "rb")
        # Again, break into chunks defined by BUFFER_SIZE
        l = content.read(BUFFER_SIZE)
        while l:
            conn.send(l)
            l = content.read(BUFFER_SIZE)
        content.close()
        # Get client go-ahead, then send download details
        conn.recv(BUFFER_SIZE)
        conn.send(struct.pack("f", time.time() - start_time))
        return file_name

    def delf():
        # Send go-ahead
        conn.send(b"1")
        # Get file details
        file_name_length = struct.unpack("h", conn.recv(2))[0]
        file_name = conn.recv(file_name_length).decode()
        # Check file exists
        if os.path.isfile(file_name):
            conn.send(struct.pack("i", 1))
        else:
            # Then the file doesn't exist
            conn.send(struct.pack("i", -1))
        # Wait for deletion confirmation
        confirm_delete = conn.recv(BUFFER_SIZE).decode()
        if confirm_delete == "Y":
            try:
                # Delete file
                os.remove(file_name)
                conn.send(struct.pack("i", 1))
                return file_name
            except:
                # Unable to delete file
                print("Failed to delete {}".format(file_name))
                conn.send(struct.pack("i", -1))
        else:
            # User abandoned deletion
            # The server probably received "N", but else used as a safety catch-all
            print("Delete abandoned by client!")

    def quit():
        # Send quit confirmation
        conn.send(b"1")
        # Close and restart the server
        conn.close()
        s.close()
        os.execl(sys.executable, sys.executable, *sys.argv)


    # Authenticate client
    username = ""
    # authenticated = False
    # while not authenticated:
    #     conn.send(b"AUTH")
    #     username = conn.recv(BUFFER_SIZE).decode()
    #     password = conn.recv(BUFFER_SIZE).decode()
    #     auth_result = auth.authenticate(username, password)
    #     if auth_result == 'AuthSuccess':
    #         authenticated = True
    #         print("Authentication successful for user:", username)
    #         conn.send(b"1")  # Send authentication success message to client
    #     else:
    #         print("Authentication failed for user:", username)
    #         conn.send(b"0")  # Send authentication failure message to client
    #         continue

    while True:
        # Enter into a while loop to receive commands from client
        print("\n\nWaiting for instruction")
        data = conn.recv(BUFFER_SIZE).decode()
        print("\nReceived instruction: {}".format(data))
        # Check the command and respond correctly
        if data == "UPLD":
            file_name = upld()
            log.upload_event(file_name,username)
        elif data == "LIST":
            list_files()
        elif data == "DWLD":
            file_name = dwld()
            log.download_event(file_name,username)
        elif data == "DELF":
            file_name = delf()
            log.delete_event(file_name,username)
        elif data == "QUIT":
            quit()
            break
        # Reset the data to loop
        data = None

# Function to continuously accept new connections and spawn threads to handle them
def accept_connections():
    while True:
        conn, addr = s.accept()
        # Spawn a new thread to handle the connection
        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.start()

# Start accepting connections
accept_connections()
