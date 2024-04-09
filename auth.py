import json

users = {}

with open('./users.json', 'r') as users_file:
    data = users_file.read()
    users = json.loads(data)

def update_users_json(users):
    with open('./users.json', 'w') as users_file:
        json.dump(users, users_file)

def authenticate(username, password):
    if username not in users:
        return 'UserNotFound'
    elif username in users and users[username] == password:
        return 'AuthSuccess'
    else:
        return 'AuthFail'
    
def addUser(username, password):
    if username in users:
        return 'UsernameAlreadyExists'
    
    users[username] = password
    update_users_json(users)
    return 'UserAdded'
    
def deleteUser(username):
    if username not in users:
        return 'UserNotFound'
    
    del users[username]
    update_users_json(users)
    return 'UserDeleted'

        



