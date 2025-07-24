import hashlib
import subprocess


# calculates the sha1 checksum of a file
def sha1(fname):
    hash_sha1 = hashlib.sha1()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha1.update(chunk)
    return hash_sha1.hexdigest()


# returns the first line of a file that a search term is present in
def get_line_num(path, search_term):
    with open(path, "r") as file:
        for i, line in enumerate(file):
            if search_term in line:
                return i
        return False


# returns the first line of a file that a search term is present in
def get_line_content(path, search_term):
    with open(path, "r") as file:
        for line in file:
            if search_term in line:
                return line
