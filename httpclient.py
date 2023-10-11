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
import json

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
    def get_host_port(self,url):
        parse_result = urllib.parse.urlparse(url)
        return [parse_result.hostname, parse_result.port]

    def parse_http_response(self, data) -> ParsedHttpResponse:
        tokens = data.split("\r\n")
        if len(tokens[0]) > 12: 
            status_code = int(tokens[0][9: 12])
        else:
            status_code = 0
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

    def fetch(self, host, port, request) -> str:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        sock.sendall(request.encode('utf-8'))
        sock.shutdown(socket.SHUT_WR)
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        sock.close()
        return buffer.decode('utf-8')
    
    def build_http_request(self, url, method, args):
        parse_result = urllib.parse.urlparse(url)
        host = parse_result.hostname
        path = parse_result.path
        if path == "":
            path = "/"
        query = parse_result.query
        headers = {}
        payload = ""

        if query != "":
            path += "?" + query
        if method == "POST":
            if args is not None:
                headers["Content-Type"] = "application/x-www-form-urlencoded"
                payload = urllib.parse.urlencode(args)
                headers["Content-Length"] = len(payload)
            else:
                headers["Content-Length"] = 0
        request = method + " " + path + " HTTP/1.1\r\nHost: " + host + "\r\n"

        for key, value in headers.items():
            request += key + ": " + str(value) + "\r\n"
        
        request += "\r\n" + payload

        return request


    def GET(self, url, args=None):
        parse_result = urllib.parse.urlparse(url)
        host = parse_result.hostname
        port = parse_result.port
        if port is None:
            port = 80
        
        request = self.build_http_request(url, "GET", args)
        response = self.fetch(host, port, request)
        parsed_response = self.parse_http_response(response)
        code = parsed_response.status_code
        body = parsed_response.body
        print(response)

        return HTTPResponse(code, body)


    def POST(self, url, args=None):
        parse_result = urllib.parse.urlparse(url)
        host = parse_result.hostname
        port = parse_result.port
        if port is None:
            port = 80
        
        request = self.build_http_request(url, "POST", args)
        response = self.fetch(host, port, request)
        print(response)
        parsed_response = self.parse_http_response(response)
        code = parsed_response.status_code
        body = parsed_response.body
        return HTTPResponse(code, body)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )
    
if __name__ == "__main__":
    client = HTTPClient()
    client.GET("http://slashdot.org/")
    # client.GET("http://www.google.com/")
    # client.GET("http://c2.com/cgi/wiki?CommonLispHyperSpec")
    # client.GET("http://[2605:fd00:4:1001:f816:3eff:fec0:41df]/parts/")
    # args = {
    #     "id": "a6372d7f-095f-4268-9c5f-9d7d2dbc7de5",
    #     "name": "Sapphire PULSE Radeon RX 7800 XT 16 GB Video Card",
    #     "type": "GPU",
    #     "release_date": 1693958400,
    #     "core_clock": 1295.0,
    #     "clock_unit": "MHz",
    #     "price": 745.9,
    #     "TDP": 266,
    #     "part_no": "11330-02-20GGGGGGGG"
    # }
    # client.POST("http://127.0.0.1:8000/parts/a6372d7f-095f-4268-9c5f-9d7d2dbc7de5", args)
    # client.POST('http://www.google.com/')
    # command = "GET"
    # if (len(sys.argv) <= 1):
    #     help()
    #     sys.exit(1)
    # elif (len(sys.argv) == 3):
    #     print(client.command( sys.argv[2], sys.argv[1] ))
    # else:
    #     print(client.command( sys.argv[1] ))
