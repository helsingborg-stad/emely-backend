import functools
import time
import socket


def timer(func):
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        tic = time.perf_counter()
        value = func(*args, **kwargs)
        toc = time.perf_counter()
        elapsed_time = toc - tic
        print(f"Elapsed time for {func}: {elapsed_time:0.4f} seconds")
        return value

    return wrapper_timer


def is_gcp_instance():
    """ Returns true if we're running on a GCP instance. Used for automatic authorization """
    try:
        socket.getaddrinfo("metadata.google.internal", 80)
    except socket.gaierror:
        return False
    return True
