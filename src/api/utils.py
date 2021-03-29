import socket

def is_gcp_instance():
    """Check if it's GCE instance via DNS lookup to metadata server.
    """
    try:
        socket.getaddrinfo('metadata.google.internal', 80)
    except socket.gaierror:
        return False
    return True