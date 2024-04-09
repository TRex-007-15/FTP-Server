import json

users = {}

with open('./users.json', 'r') as users_file:
    data = users_file.read()
    users = json.loads(data)

def authenticate(username, password):
    if username not in users:
        return 'UNF'
    elif username in users and users[username] == password:
        return 'ASF'
    else:
        return 'ANS'
    
def addUser(username, password):
    if username in users:
        return 'UsernameAlreadyExists'
    else:
        users[username] = password
        with open('./users.json', 'w') as users_file:
            json.dump(users, users_file)
        return 'UserAddedSuccessfully'



