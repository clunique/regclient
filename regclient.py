#!/usr/bin/python
# -*- coding: UTF-8 -*-

import requests, json
import datetime


class DockerImageInfo():
    name = ''
    tag = ''
    digest = ''
    last_update = ''

    def __init__(self, name, tag):
        self.name = name
        self.tag = tag

    def __lt__(self, other):
        return self.last_update < other.last_update

class DockerRegistryClient:
    username = ''
    password = ''
    server = ''
    port = 5000
    ssl = False
    cert = ''
    STATUS_TIMEOUT = 501
    STATUS_OK = 200
    STATUS_ACCEPT = 202

    def format_url(self):
        url = ''
        if self.ssl :
            url = "https://%s:%s" % (self.server, self.port)
        else:
            url = "http://%s:%s" % (self.server, self.port)
        return url

    def __init__(self, svr, port, user, passwd, cert = '', ssl = False):
        self.username = user
        self.password = passwd
        self.server = svr
        self.cert = cert
        self.port = port
        self.ssl = ssl

    def __get(self, path, headers={}):
        url = self.format_url() + path
        #print "url: ", url
        timeout = 5
        try:
            if self.ssl:
                if len(self.cert) > 0 :
                    response = requests.get(url, auth=(self.username, self.password), verify=self.cert, headers=headers, timeout=timeout)
                else:
                    response = requests.get(url, auth=(self.username, self.password), verify=False,  headers=headers, timeout=timeout)
            else:
                response = requests.get(url, auth=(self.username, self.password),  headers=headers, timeout=timeout)
        except requests.exceptions.ConnectTimeout:
            return self.STATUS_TIMEOUT, None
        #print "response: ", response
        return response.status_code, response

    def __delete(self, path):
        url = self.format_url() + path
        #print "url: ", url
        if self.ssl:
            if len(self.cert) > 0 :
                response = requests.delete(url, auth=(self.username, self.password), verify=self.cert)
            else:
                response = requests.delete(url, auth=(self.username, self.password), verify=False)
        else:
            response = requests.delete(url, auth=(self.username, self.password))
        return response.status_code

    def __catalog(self):
        path = '/v2/_catalog'
        status_code, response = self.__get(path)
        if status_code == self.STATUS_OK:
            return status_code, response
        else:
            return status_code, ''

    def check(self):
        path = '/v2/'
        status_code, _ = self.__get(path)
        return status_code == self.STATUS_OK

    def get_repo(self):
        status_code, response = self.__catalog()
        if status_code == self.STATUS_OK:
            json = response.json()
            repositories = json['repositories']
            return repositories
        else:
            return ''

    def get_tag_list(self, repo):
        path = "/v2/%s/tags/list" % repo
        status_code, response = self.__get(path)
        if status_code == self.STATUS_OK:
            #print "tag list content: ", response.content
            json = response.json()
            tags = json['tags']
            return status_code, tags
        else:
            return status_code, ''

    def get_image_info(self, name, reference):
        headers = {'Accept': 'application/vnd.docker.distribution.manifest.v2+json'}
        path = "/v2/%s/manifests/%s" % (name, reference)
        status_code, response = self.__get(path, headers)
        GMT_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'
        img = DockerImageInfo(name, reference)
        if status_code == self.STATUS_OK:
            #print "digest headers: ", response.headers
            img.digest = response.headers.get('Docker-Content-Digest')
            tm_gmt = response.headers.get('Last-Modified')
            img.last_update = datetime.datetime.strptime(tm_gmt, GMT_FORMAT)
            return status_code, img
        else:
            return status_code, img

    def delete(self, image):
        path = "/v2/%s/manifests/%s" % (image.name, image.digest)
        status_code = self.__delete(path)
        return status_code == self.STATUS_ACCEPT


if __name__ == '__main__':
    MAX_REMAIN = 20
    dr = DockerRegistryClient('registry.nscloud.local', 5006, 'admin', 'admin123', '/etc/pki/ca-trust/source/anchors/nexus.crt', True)
    # dr = DockerRegistry('registry.nscloud.local', 5006, 'admin', 'admin123', '', True)
    if dr.check():
        print("OK to connect registry %s. " % dr.server)
    else:
        print("Fail to connect registry %s. " % dr.server)

    repos = dr.get_repo()
    if len(repos) > 0:
        print "repositories: ", repos
    else:
        print "repository is empty!"

    i = 0
    for repo in repos:
        #print "repo[%d]: %s" %(i, repo)
        status_code, tags = dr.get_tag_list(repo)
        if status_code == dr.STATUS_OK:
            j = 0
            img_list = []
            for tag in tags:
                #print "tag[%d]: %s" % (j, tag)
                status_code2, img = dr.get_image_info(repo, tag)
                if status_code2 == dr.STATUS_OK:
                    img_list.append(img)
                    print "Digest of image %s:%s is (%s) \n %s" % (img.name, img.tag, img.last_update, img.digest)
                else:
                    print "Fail to get image information: %s/%s." % (img.name, img.tag)

                j = j + 1


            img_list.sort()
            total = len(img_list)
            remain = total
            for image in img_list:
                if remain < 20:
                    break
                if dr.delete(image):
                    print "OK to delete image %s:%s", (image.name, image.tag)
                remain = remain - 1

        else:
            print "Fail to get tag list of %s." % (repo)

        i = i + 1