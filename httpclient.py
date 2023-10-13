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
import time
from typing import Union

def help():
    print("httpclient.py [GET/POST] [URL]\n")

class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

class Response:
    def __init__(self, raw: Union[bytearray, bytes]):
        self.raw = raw
        #parse response
        tokens = raw.split(b'\r\n')
        if len(tokens[0]) > 12:
            self.status = int(tokens[0][9: 12])
        else:
            self.status = 0
        self.headers = {}
        self.body = ""
        encoding = "utf-8" # default encoding
        tokens.pop(0)
        for token in tokens:
            if b':' in token:
                colon_indx = token.find(b":")
                header = token[:colon_indx].decode('utf-8').strip()
                value = token[colon_indx + 1:].decode('utf-8').strip()
                self.headers[header] = value
                if header == "Content-Type" and "charset" in value:
                    # extract encoding of the body
                    charset_indx = value.find("charset")
                    encoding = value[charset_indx + 8:]
            else:
                break
            
        body_start_index = raw.find(b"\r\n\r\n")
        if body_start_index != -1:
            # decode the body with the specified encoding
            self.body = raw[body_start_index + 4:].decode(encoding)


class HTTPClient(object):
    def fetch(self, url: str, init: dict=None) -> Response:
        # get host and port
        parse_result = urllib.parse.urlparse(url)
        host = parse_result.hostname
        port = parse_result.port
        request = self.build_http_request(url, init)
        if port is None:
            port = 80
    
        # create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # make connection
        sock.connect((host, port))

        # send request
        sock.sendall(request.encode('utf-8'))

        # receive response
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        sock.close()
        return Response(buffer)
    

    def build_http_request(self, url: str, options: dict=None) -> str:
        method = "GET"
        parse_result = urllib.parse.urlparse(url)
        host = parse_result.hostname
        path = parse_result.path
        if path == "":
            path = "/"
        query = parse_result.query
        if query != "":
            path += "?" + query
        headers = { # default headers
            "Connection": "close", # telling the server that we don't expect to keep the connection alive
            "Content-Length": 0, # default body length
            "Content-Type": "text/plain; charset=utf-8" # default content type
        }
        body = ""

        # handle options
        if options is not None:
            method = options.get('method', 'GET')
            option_headers = options.get('headers', {})
            # overriding the default headers
            for key, value in option_headers.items():
                headers[key] = value
            body = options.get('body', '')
        
        request = method + " " + path + " HTTP/1.1\r\nHost: " + host + "\r\n"

        for key, value in headers.items():
            request += key + ": " + str(value) + "\r\n"
        
        request += "\r\n" + body

        return request


    def GET(self, url, args=None):
        options = {}
        if args is not None:
            body = urllib.parse.urlencode(args)
            options['body'] = body
            options['headers'] = {
                "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
                "Content-Length": len(body)
            }
            

        response = self.fetch(url, options)
        code = response.status
        body = response.body
        # print(response.body)
        # print(response.header)

        return HTTPResponse(code, body)


    def POST(self, url, args=None):
        options = {
            "method": "POST"
        }
        if args is not None:
            body = urllib.parse.urlencode(args)
            options['body'] = body
            options['headers'] = {
                "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
                "Content-Length": len(body)
            }
            

        response = self.fetch(url, options)
        code = response.status
        body = response.body
        # print(response.body)
        # print(response.header)

        return HTTPResponse(code, body)

    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST( url, args )
        else:
            return self.GET( url, args )
    
if __name__ == "__main__":
    client = HTTPClient()
    # client.GET("http://slashdot.org/")
    client.POST("http://www.google.com/")
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
