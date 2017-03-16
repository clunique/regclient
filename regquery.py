#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys, getopt
from optparse import OptionParser
from regclient import DockerRegistryClient, DockerImageInfo

usage = "usage: %prog [options] arg1 arg2"

parser = OptionParser(usage=usage)
parser.add_option("-H", "--hostname",
                  action="store", dest="hostname", type="string",
                  help="the hostname of the docker registry server")

parser.add_option("-p", "--port",
                  action="store", dest="port", default=5000, type="int",
                  help="the port of the docker registry server")

parser.add_option("-u", "--username",
                  action="store", dest="username", type="string",
                  help="the username to login the docker registry server")

parser.add_option("-P", "--password",
                  action="store", dest="password", type="string",
                  help="the password of the docker registry server")

parser.add_option("-c", "--cert",
                  action="store", dest="cert", type="string",
                  help="the cert file for the docker registry server")

parser.add_option("-s", "--ssl-enable", action="store_true", dest="ssl_enable", default='False',
                  help="ssl enabled or not [default]")

parser.add_option("-i", "--image",
                  action="store", dest="image", type="string",
                  help="the image name to query")

(options, args) = parser.parse_args(sys.argv[1:])

#print "hostname: %s" % options.hostname

if not options.hostname:
    print "Docker Registry server should be defined."
    exit(1)

if not options.username:
    print "Username should be defined."
    exit(1)

if not options.password:
    print "Password should be defined."
    exit(1)

if not options.cert and options.ssl_enable:
    print "Cert file should be set when ssl is enabled."
    exit(1)

reg_server = options.hostname
port = options.port
username = options.username
password = options.password
cert = options.cert
ssl_enable = options.ssl_enable
image = options.image

rc = DockerRegistryClient(reg_server, port, username, password, cert, ssl_enable)

if rc.check():
    print("OK to connect registry %s. " % rc.server)
else:
    print("Fail to connect registry %s. " % rc.server)


if not image:
    repos = rc.get_repo()
    count = len(repos)
    if count > 0:
        print "There are %d repositories in server %s:%s" % (count, reg_server, port)
        index = 1
        for repo in repos:
            print "[%d]\t%s" % (index, repo)
            index += 1
    else:
        print "repository is empty!"
else:
    status_code, tags = rc.get_tag_list(image)
    if status_code == rc.STATUS_OK:
        print "There are %d images of %s in server %s:%s" % (len(tags), image, reg_server, port)
        j = 1
        for tag in tags:
            status_code2, img = rc.get_image_info(image, tag)
            if status_code2 == rc.STATUS_OK:
                print "[%d]. %s:%s \t\t %s" % (j, image, tag, img.digest)
            else:
                print "[%d]. Fail to get image information: %s/%s." % (j, image, tag)

            j = j + 1
    else:
        print "Fail to get tag list of %s." % (image)

