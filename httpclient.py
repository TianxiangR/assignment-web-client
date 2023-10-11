#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
# you may use urllib to encode data appropriately
import urllib.parse

def help():
    print("httpclient.py [GET/POST] [URL]\n")

class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

class ParsedHttpResponse:
    def __init__(self, status_code: int, headers: dict, body: str | None):
        self.status_code = status_code
        self.headers = headers
        self.body = body

class HTTPClient(object):


    # 3xx codes that has redirections
    # https://stackoverflow.com/questions/16194988/for-which-3xx-http-codes-is-the-location-header-mandatory
    redirection_codes = set([301, 302, 303, 307, 308])
    def get_host_port(self,url):
        parse_result = urllib.parse.urlparse(url)
        return [parse_result.hostname, parse_result.port]

    def connect(self, host, port) -> socket.socket:
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        s.connect((host, port))
        return s

    def parse_http_response(self, data) -> ParsedHttpResponse:
        tokens = data.split("\r\n")
        status_code = int(tokens[0][9: 12])
        headers = {}
        body = ""
        for i in range(1, len(tokens)):
            if ":" in tokens[i]:
                colon_indx = tokens[i].find(":")
                header = tokens[i][:colon_indx]
                value = tokens[i][colon_indx + 1:].lstrip()
                if header in headers and isinstance(headers[header], list):
                    headers[header] = [headers[header], value]
                else:
                    headers[header] = value
            else:
                break
        body_start_index = data.find("\r\n\r\n")
        if body_start_index != -1:
            body = data[body_start_index + 4:]
        rval = ParsedHttpResponse(status_code, headers, body)
        return rval        

    # read everything from the socket
    def recvall(self, sock):
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return buffer.decode('utf-8')

    def GET(self, url, args=None):
        parse_result = urllib.parse.urlparse(url)
        host = parse_result.hostname
        port = parse_result.port
        if port is None:
            port = 80
        path = parse_result.path
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.connect((host, port))
        request = b"GET / HTTP/1.1\r\nHost:www.google.com\r\n\r\n"
        sock.sendall(b"GET / HTTP/1.1\r\nHost:www.google.com\r\n\r\n")
        sock.shutdown(socket.SHUT_WR)
        buffer = b''
        while True:
            part = sock.recv(4096)
            if part:
                buffer += part
            else:
                break
        response = buffer.decode('utf-8')
        print("GET:", response)
        parsed_response = self.parse_http_response(response)
        headers = parsed_response.headers
        code = parsed_response.status_code
        body = parsed_response.body
        
        if parsed_response in self.redirection_codes and 'Location' in headers:
            redirected_location = headers['Location']
            if isinstance(redirected_location, list):
                redirected_location = redirected_location[0]
            return self.GET(redirected_location)

        return HTTPResponse(code, body)


    def POST(self, url, args=None):
        code = 500
        body = ""
        return HTTPResponse(code, body)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )
    
if __name__ == "__main__":
    client = HTTPClient()
    client.GET('http://www.google.com/')
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command( sys.argv[2], sys.argv[1] ))
    else:
        print(client.command( sys.argv[1] ))
