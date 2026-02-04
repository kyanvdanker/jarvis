stored_value = None

def remember_value(value):
    global stored_value
    stored_value = value

def recall_value():
    return stored_value
