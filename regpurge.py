#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys
from optparse import OptionParser
from regclient import DockerRegistryClient, DockerImageInfo

usage = "usage: %prog arg1 arg2"

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

parser.add_option("-r", "--remain-count",
                  action="store", dest="remain_count", default=5000, type="int",
                  help="remain count of the image, default is 20")

parser.add_option("-y", "--yes", action="store_true", dest="yes", default='False',
                  help="Don't prompt to input yes to purge")

(options, args) = parser.parse_args(sys.argv[1:])

if not options.hostname:
    print "Host name of Docker Registry server is required."
    exit(1)

if not options.username:
    print "Username is required."
    exit(1)

if not options.password:
    print "Password is required"
    exit(1)

if not options.cert and options.ssl_enable:
    print "Cert file is required when ssl is enabled."
    exit(1)

reg_server = options.hostname
port = options.port
username = options.username
password = options.password
cert = options.cert
ssl_enable = options.ssl_enable
image = options.image
remain_count = options.remain_count
yes = options.yes

stable_flag = "stable"

rc = DockerRegistryClient(reg_server, port, username, password, cert, ssl_enable)
if rc.check():
    print("OK to connect hostname %s. " % rc.server)
else:
    print("Fail to connect hostname %s. " % rc.server)
    exit(1)


status_code, tags = rc.get_tag_list(image)

if status_code == rc.STATUS_OK:
    j = 0
    img_list = []
    for tag in tags:
        # print "tag[%d]: %s" % (j, tag)
        status_code2, img = rc.get_image_info(image, tag)
        if status_code2 == rc.STATUS_OK:
            img_list.append(img)
            #print "Digest of image %s:%s is (%s) \n %s" % (img.name, img.tag, img.last_update, img.digest)
        else:
            print "Fail to get image information: %s/%s." % (img.name, img.tag)

        j = j + 1

    img_list.sort()
    total = len(img_list)

    print "There are %d images of %s in server %s:%s" % (total, image, reg_server, port)
    print "NO.\tLAST UPDATE\tIMAGE\tDIGEST"
    print "----\t-----------\t-----\t------"
    index = 1
    for img in img_list:
        print "[%d]\t%s\t%s:%s\t%s", (index, img.last_update, img.name, img.tag, img.digest)
        index += 1

    remain = total

else:
    print "Fail to get tag list of %s/%s." % (image)
