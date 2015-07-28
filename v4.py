#!/usr/bin/python

import OpenSSL
import socket
import subprocess
import signal
import sys
import struct
import re
from datetime import datetime

# Handle alarm signal if alarm timeout in seconds is reached
def signal_handler(signum=None, frame=None):
    grains = {}
    print("handshake timed out!")
    return grains

# Main function which returns grain data
# This function takes a port number, grains dictionary, host string, and vhost boolean as arguments
def run(port=1, grains={}, host='localhost', vhost=False,):
    # grains['cert'] = {}
    print(port)
    # Determine the operating system platform we're running on
    platform = sys.platform
    # Get on SSL Context (we choose SSLv23 for best compatibility)
    context = OpenSSL.SSL.Context(OpenSSL.SSL.SSLv23_METHOD)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Set a 5 second timeout value on the socket
    s.settimeout(5)
    # Create our SSL connection using the context and socket objects
    connection = OpenSSL.SSL.Connection(context, s)
    connection.setblocking(1)
    # If we're on Windows, set socket options and specify a timeout value. This doesn't work in linux, unsure why not.
    if platform == 'win32':
        tv = struct.pack('ii', int(6), int(0))
        connection.setsockopt(socket.SOL_SOCKET, socket.SO_RCVTIMEO, tv)
    # Attempt a connection to [host] on [port]
    try:
        print("Connecting to port: ", host, int(port))
        connection.connect((host, int(port)))
    except socket.error:
        print("Connection refused to port", int(port))
    # Windows doesn't support signal alarms, but *nix does
    # Set an alarm with a 2 second timer, and attach the signal handler defined above
    if platform != 'win32':
        signal.signal(signal.SIGALRM, signal_handler)
        signal.alarm(2)
    print("Attempting handshake...")
    # Attempt the SSL/TLS handshake. Depending on the platform, if the handshake hangs or times out, either the alarm
    # signal handler will kick in or the socket timeout value will take effect
    try:
        connection.do_handshake()
        # Format the end date of the peer certificate
        end = datetime.strftime(datetime.strptime(connection.get_peer_certificate().get_notAfter()[:-1], '%Y%m%d%H%M%S'), '%b %d %H:%M:%S %Y %Z')
        # Format the start of the peer certificate
        start = datetime.strftime(datetime.strptime(connection.get_peer_certificate().get_notBefore()[:-1], '%Y%m%d%H%M%S'), '%b %d %H:%M:%S %Y %Z')
        # Set up array to store the various components of the subject string
        subject_components = []
        for x, y in connection.get_peer_certificate().get_subject().get_components():
            subject_components.append('/' + x + '=')
            subject_components.append(y)
        subject = "".join(subject_components)
        # cn = subject_components[-1]
        # print(subject)
        # Search the 'subject' object for the CN pattern to extract just the CN value
        cn_pattern = re.search('CN=[^\/]*', subject)
        # Split the cn_pattern to just get the value part of CN=value
        cn = cn_pattern.group(0).split('=')[1]
        grains['cert']['expired'] = ''
        # Set expired to True if the certificate has expired, otherwise set it to False
        expired = True if connection.get_peer_certificate().has_expired() == 1 else False
        # Get the SHA1 fingerprint of the certificate
        fingerprint = connection.get_peer_certificate().digest('sha1')
        # Get the serial number of the certificate
        serial = connection.get_peer_certificate().get_serial_number()
        if expired:
            # Set the 'expired' key to True if expired boolean is True
            grains['cert']['expired'] = True
            grains['cert']['ports'][port] = {}
        if grains['cert']['expired']:
            grains['cert']['expired'] = True
            # Create a  dictionary for the port we are attempting to connect to
            grains['cert']['ports'][port] = {}
            # If we are not connecting to a vhost, just get the information about the cer
            if not vhost:
                grains['cert']['ports'][port]['start'] = start
                grains['cert']['ports'][port]['end'] = end
                grains['cert']['ports'][port]['subject'] = subject
                grains['cert']['ports'][port]['cn'] = cn
                grains['cert']['ports'][port]['expired'] = expired
                grains['cert']['ports'][port]['fingerprint'] = fingerprint
                grains['cert']['ports'][port]['serial'] = serial
                return grains['cert']['ports'][port]
            else:
                grains['cert']['vhosts'][port] = {}
                grains['cert']['vhosts'][port]['start'] = start
                grains['cert']['vhosts'][port]['end'] = end
                grains['cert']['vhosts'][port]['subject'] = subject
                grains['cert']['vhosts'][port]['cn'] = cn
                grains['cert']['vhosts'][port]['expired'] = expired
                grains['cert']['vhosts'][port]['fingerprint'] = fingerprint
                grains['cert']['vhosts'][port]['serial'] = serial
                grains['cert']['vhosts'][port]['vhost'] = host
                return grains['cert']['vhosts'][port]
        else:
            # Set the 'expired' key to False if expired boolean is False
            grains['cert']['expired'] = False
            grains['cert']['ports'][port] = {}
            if not vhost:
                grains['cert']['ports'][port]['start'] = start
                grains['cert']['ports'][port]['end'] = end
                grains['cert']['ports'][port]['subject'] = subject
                grains['cert']['ports'][port]['cn'] = cn
                grains['cert']['ports'][port]['expired'] = expired
                grains['cert']['ports'][port]['fingerprint'] = fingerprint
                grains['cert']['ports'][port]['serial'] = serial
                return grains['cert']['ports'][port]
            else:
                grains['cert']['vhosts'][host] = {}
                grains['cert']['vhosts'][host]['start'] = start
                grains['cert']['vhosts'][host]['end'] = end
                grains['cert']['vhosts'][host]['subject'] = subject
                grains['cert']['vhosts'][host]['cn'] = cn
                grains['cert']['vhosts'][host]['expired'] = expired
                grains['cert']['vhosts'][host]['fingerprint'] = fingerprint
                grains['cert']['vhosts'][host]['serial'] = serial
                return grains['cert']['vhosts'][host]
        connection.shutdown()
    except OpenSSL.SSL.Error:
        print("Could not connect")
    if platform != 'win32':
        signal.alarm(0)


def get_cert_info():
    """
    Return SSL/TLS certificate information
    """
    grains = {}
    grains['cert'] = {}
    grains['cert']['vhosts'] = {}
    grains['cert']['ports'] = {}
    platform = sys.platform
    if platform == 'win32':
        p1 = subprocess.Popen(['netstat', '-ano'], stdout=subprocess.PIPE).communicate()
        listening = [ line for line in p1[0].split('\r\n') if 'LISTEN' in line ]
        lines = []
        ports = []
        for line in listening:
            a = [x for x in line.split(' ') if x != '']
            lines.append(a)
            ports.append(a[1].split(':')[1])
            ports = [port for port in ports if port != '']
    else:
        ports = []
        first = ['netstat', '-antp']
        second = ['grep', 'LISTEN']
        third = ['awk', '{print $4}']
        p1 = subprocess.Popen(first, stdout=subprocess.PIPE)
        p2 = subprocess.Popen(second, stdin=p1.stdout, stdout=subprocess.PIPE)
        p3 = subprocess.Popen(third, stdin=p2.stdout, stdout=subprocess.PIPE)
        out = p3.communicate()[0]
        for x in out.split('\n'):
            if not (str(x.split(':')[-1])) == '':
                ports.append(str(x.split(':')[-1]))
    wildcard_vhosts = []
    standard_vhosts = []
    try:
        p = subprocess.Popen(['httpd', '-S'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()[0]
        p = [ x.strip() for x in p.split('\n') ]
        standard_pattern = re.compile('^(?:[0-9]{1,3}\.){3}[0-9]{1,3}:*\d*[^(]*')
        wildcard_pattern = re.compile('^port\s{1}\d+\s{1}namevhost\s{1}.+')
        for x in p:
            dict = {}
            if wildcard_pattern.match(x):
                dict['port'] = x.split(' ')[1]
                dict['host'] = x.split(' ')[3]
                if dict not in wildcard_vhosts:
                    wildcard_vhosts.append(dict)
        for x in p:
            dict = {}
            if standard_pattern.match(x):
                dict['port'] = re.compile('\s*').split(x)[0].split(':')[1]
                dict['host'] = re.compile('\s*').split(x)[0].split(':')[0]
                if dict not in wildcard_vhosts:
                    standard_vhosts.append(dict)
    except:
        print("httpd not found")
    for vhost in wildcard_vhosts:
        port = vhost['port']
        host = vhost['host']
        grains['cert']['vhosts'][host] = run(port, grains, host, True)
        print(grains)
    for vhost in standard_vhosts:
        port = vhost['port']
        host = vhost['host']
        grains['cert']['vhosts'][host] = run(port, grains, host, True)
        print(grains)
    for port in ports:
        res = run(port, grains)
        if res is not None:
            grains['cert']['ports'][port] = res
    if len(grains['cert']['vhosts']) == 0:
        grains['cert'].pop('vhosts', None)
    if len(grains['cert']) == 1 and grains['cert'].keys()[0] == 'expired':
        grains.pop('cert', None)
    for key in grains['cert']['ports'].keys():
        if len(grains['cert']['ports'][key]) == 0:
            grains['cert']['ports'].pop(key, None)
    return grains