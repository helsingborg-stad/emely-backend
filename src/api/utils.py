import socket

def is_gcp_instance():
    """Check if it's GCE instance via DNS lookup to metadata server.
    """
    try:
        socket.getaddrinfo('metadata.google.internal', 80)
    except socket.gaierror:
        return False
    return True

# TODO: Implement this function
def update_firestore_conversation(collection_db, firestore_conversation):
    raise NotImplementedError

# TODO: Implement
def update_firestore_message(collection_db, firestore_message):
    raise NotImplementedError



