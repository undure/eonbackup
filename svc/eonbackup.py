import os
import hashlib
import base64
from binascii import hexlify
import datetime
import getpass
import select
import socket
import sys
import time
import traceback
import json
import logging
import paramiko
import subprocess

import config

from wificlient import get_active_clients

logger = logging.getLogger('eonbackup')
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

def calculate_file_hash(filename):
    sha256_hash = hashlib.sha256()
    with open(filename,"rb") as f:
        for byte_block in iter(lambda: f.read(4096),b""):
            sha256_hash.update(byte_block)

    return (sha256_hash.hexdigest())

def download_files(sftp, session_name, file_defs):
    directory = os.path.join(config.root_dir, session_name)

    if not os.path.exists(directory):
        os.makedirs(directory)
    failed = False
    for fd in file_defs:
        h = fd[0]
        fn = fd[1]
        if os.path.exists(fn):
            logger.info("File {} was downloaded already".format(fn))
            continue

        fn_d = fn+".tdl"
        logger.info("Downloading: " + str(fn) + " " + h)
        sftp.get(fn, fn_d)
        h2 = calculate_file_hash(fn_d)
        if h2 == h:
            os.rename(fn_d, fn)
            logger.info("Download of {} complete".format(fn))
        elif os.path.exists(fn_d):
            os.remove(fn_d)
            failed = True

    if not failed:
        status_file = get_session_status_file_path(session_name)
        with open(status_file, "w") as fs:
            fs.write(json.dumps(file_defs))        


def get_file_stat(t, sftp, fn):
        command = "sha256sum " + fn 
        logger.info(command)

        session = t.open_channel(kind='session')
        session.exec_command(command)

        while not session.recv_ready():
            pass

        sha_result = filter(None, session.recv(512).strip().split(' '))
        stat = sftp.stat(sha_result[1])
        fd = {
                "name": sha_result[1], 
                "sha256hash": sha_result[0],
                "atime": stat.st_atime,
                "mtime": stat.st_mtime,
                "size": stat.st_size
            }
        
        return fd , sha_result

def get_session_status_file_path(session_name):
    return os.path.join(config.status_dir, session_name)

def sesson_sync_complete(session_name):
    directory = os.path.join(config.root_dir, session_name)
    if not os.path.exists(directory):
        return False
    
    status_file = get_session_status_file_path(session_name)
    if os.path.exists(status_file):
        return True

    return False

def init():
    if not os.path.exists(config.root_dir):
        os.makedirs(config.root_dir)

    if not os.path.exists(config.status_dir):
        os.makedirs(config.status_dir)

def connect(hostname, port, key):
    t = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((hostname, port))
        t = paramiko.Transport(sock)
        t.start_client()
        t.auth_publickey(config.username, key)
    except Exception as e:
        logger.info("Connection failed: " + str(e))
        return None

    return t

def load_files(t, sftp, session_dir, age):
    start_time = int((datetime.datetime.utcnow() - datetime.datetime(1970,1,1)).total_seconds())

    files = sftp.listdir(session_dir)
    sha_results = []

    for f in files:
        fn = os.path.join(session_dir, f)
        fd, sha_result = get_file_stat(t, sftp, fn)
        file_age = start_time - fd["atime"]

        if file_age < age:
            return None

        sha_results.append(sha_result)
    return sha_results

def process_session(t, sftp, session):
    if sesson_sync_complete(session):
        logger.info("Ignoring complete session {}".format(session))
        return

    session_dir = os.path.join(config.root_dir, session)

    sha_results = load_files(t, sftp, session_dir, 2 * 60)
    if sha_results:
        download_files(sftp, session, sha_results)
    else:
        logger.info("Ignoring recent session {}".format(session))

def process_host(t):
    sftp = paramiko.SFTPClient.from_transport(t)
    dirlist = sftp.listdir(config.root_dir)

    for d in dirlist:
        if not disk_ok():
            return
        process_session(t, sftp, d)

def disk_ok():
    df = subprocess.Popen(["df", "/data/"], stdout=subprocess.PIPE)
    output = df.communicate()[0]
    device, size, used, available, percent, mountpoint = \
        output.split("\n")[1].split()
    u = int(used)
    a = int(available)
    s = int(size)

    logger.info("Disk usage {}/{} {}".format(u, s,percent))

    if s == 0:
        return False
    
    return (u * 100 / s) < config.disk_full_percent

def main():
    init()
    if not disk_ok():
        logger.error("Disk full. Stopping.")
        return

    key = paramiko.RSAKey.from_private_key_file(config.key_path)
    hosts = get_active_clients()
    for host in hosts:
        logger.info("Trying host {}".format(host))
        hostname = host["ip"]

        t = connect(hostname, config.port, key)
        if not t:
            continue

        process_host(t)

if __name__ == "__main__":
    main()
