#!/usr/bin/env python3

"""
requirements: pip3 install pygments prompt_toolkit requests
"""

import argparse
import jsbeautifier
import base64
import mimetypes
import os
import pygments
import requests
import shutil
import html5print
import subprocess
import tempfile
import time

import prompt_toolkit
from prompt_toolkit import Application
from prompt_toolkit import PromptSession
from prompt_toolkit import print_formatted_text
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import WordCompleter, Completer
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.formatted_text import PygmentsTokens
from prompt_toolkit.key_binding import KeyBindings, key_processor
from prompt_toolkit.layout.containers import VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.shortcuts import confirm
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Frame, TextArea
from pygments.lexers.python import PythonLexer
from pygments.lexers.textfmts import HttpLexer
from pygments.token import Token
from urllib.parse import urlparse
from http.server import BaseHTTPRequestHandler
from io import BytesIO
import bs4


def get_extention(r: requests.Response):
    if content_type := r.headers.get('content-type').split(";")[0]:
        ext = mimetypes.guess_extension(content_type)

    if not ext:
        ext = os.path.splitext(r.url)[1]

    return ext if ext else ".bin"

class HTTPRequest(BaseHTTPRequestHandler):
    def __init__(self, request_text):
        self.rfile = BytesIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message



class HTTPCompleter(Completer):
    def get_completions(self, document, complete_event):
        yield Completion('completion', start_position=0)

http_completer = WordCompleter([
    'OPTIONS', 'GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'TRACE', 'CONNECT',
    'PROPFIND', 'PROPPATCH', 'MKCOL', 'COPY', 'MOVE', 'LOCK', 'UNLOCK',
    'VERSION-CONTROL', 'REPORT', 'CHECKOUT', 'CHECKIN', 'UNCHECKOUT',
    'MKWORKSPACE', 'UPDATE', 'LABEL', 'MERGE', 'BASELINE-CONTROL',
    'MKACTIVITY', 'ORDERPATCH', 'ACL', 'PATCH', 'SEARCH', 'ARBITRARY',

    'HTTP', '/', '0.9', '1.0', '1.1',

    'Accept: ', 'Accept-Charset: ', 'Accept-Datetime: ', 'Accept-Encoding: ',
    'Accept-Language: ', 'Authorization: ', 'Cache-Control: ', 'Connection: ',
    'Content-Length: ', 'Content-MD5: ', 'Content-Type: ', 'Cookie: ', 'Date: ',
    'Expect: ', 'Forwarded: ', 'From: ', 'Host: ', 'If-Match: ', 'If-Modified-Since: ',
    'If-None-Match: ', 'If-Range: ', 'If-Unmodified-Since: ', 'Max-Forwards: ',
    'Origin: ', 'Pragma: ', 'Proxy-Authorization: ', 'Range: ', 'Referer: ', 'TE: ',
    'Upgrade: ', 'User-Agent: ', 'Via: ', 'Warning: ',

    'DNT: ', 'Front-End-Https: ', 'Proxy-Connection: ', 'X-Att-Deviceid: ',
    'X-CSRFToken: ', 'X-Correlation-ID: ', 'X-Csrf-Token: ', 'X-XSRF-TOKEN: ',
    'X-Do-Not-Track: ', 'X-Forwarded-For: ', 'X-Forwarded-For: ',
    'X-Forwarded-Host: ', 'X-Forwarded-Host: ', 'X-Forwarded-Proto: ',
    'X-HTTP-Method-Override: ', 'X-ProxyUser-Ip: ', 'X-Request-ID: ',
    'X-Requested-With: ', 'X-UIDH: ', 'X-Wap-Profile: ', 'X-XSRF-TOKEN: ',
    'Client-IP: ', 'True-Client-IP: ', 'Cluster-Client-IP: '

], ignore_case=True, WORD=True)

style = Style.from_dict({
    'completion-menu.completion': 'bg:#008888 #ffffff',
    'completion-menu.completion.current': 'bg:#00aaaa #000000',
    'scrollbar.background': 'bg:#88aaaa',
    'scrollbar.button': 'bg:#222222',
})


def send_raw_request(raw_request):
    r = HTTPRequest(raw_request.encode('utf-8'))
    hostname = r.headers['Host']
    url = f"http://{hostname}{r.path}"
    response = requests.request(
        method=r.command, url=url, headers=r.headers, data=r.rfile.read())
    ApplicationState.response_history.append(response)
    return response


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    args = parser.parse_args()
    return args


def format_raw_response(res, showBody=True):
    return 'HTTP/1.1 {status_code}\n{headers}\n\n{body}'.format(
        status_code=res.status_code,
        headers='\n'.join('{}: {}'.format(k, v)
                          for k, v in res.headers.items()),
        body = res.content.decode('utf-8', errors='ignore') if showBody else "")


url_argument = parse_args()
url = urlparse(url_argument.url)

hostvalue = url.hostname if url.port is None else f"{url.hostname}:{url.port}"
default = f"""GET {url.path}?{url.query} HTTP/1.1
Host: {hostvalue}
User-Agent: sendrequest.py
Accept: */*
Accept-Encoding: gzip, deflate
"""

request_buffer = Buffer( completer=http_completer)
request_buffer.text = default
request_control = BufferControl( request_buffer, lexer=PygmentsLexer(HttpLexer, ), focus_on_click=True)
request_window = Window(request_control, wrap_lines=True)

response_buffer = Buffer(completer=http_completer)
response_control = BufferControl( response_buffer, lexer=PygmentsLexer(HttpLexer), focus_on_click=True)
response_window = Window(response_control, wrap_lines=True)

request_frame = Frame(request_window, title="Request")
response_frame = Frame(response_window, title="Response")

root_container = VSplit([
    request_frame,
    response_frame
],)

kb = KeyBindings()
layout = Layout(root_container)


@kb.add('c-p')
def prettify(event):
    buf = event.app.current_buffer
    response = ApplicationState.response_history[-1]
    headers = format_raw_response(response, showBody=False)
    soup = bs4.BeautifulSoup(response.content, 'lxml')
    body = soup.prettify()
    #body = html5print.HTMLBeautifier.beautify(response.conten.decode('utf-8')t)
    #body = jsbeautifier.beautify(response.content.decode('utf-8'))
    buf.text = headers + body

@kb.add('c-w')
def change_focus(event):
    event.app.layout.focus_next()

@kb.add('c-o')
def open_response(event):
    if not ApplicationState.response_history:
        return

    r = ApplicationState.response_history[-1]

    ext = get_extention(r)

    f = tempfile.NamedTemporaryFile(suffix=ext)
    r.raw.decode_content = True
    f.write(r.content)
    f.flush()

    def open_in_vim():
        subprocess.call(['vim', f.name], shell=False)
        f.close()

    prompt_toolkit.application.run_in_terminal(open_in_vim, in_executor=True)

    app.reset()

@kb.add('c-b')
def base64_encode_selection(event):
    buf = event.app.current_buffer
    start_pos, end_pos = buf.document.selection_range()

    toencode = (buf.text[start_pos:end_pos]).encode('utf-8')
    encoded_value =base64.b64encode(toencode).decode('utf-8')
    new_text = buf.text[:start_pos] + encoded_value + buf.text[end_pos+1:]
    buf.text = new_text


@kb.add('c-e')
def edit_http(event):
    if layout.has_focus(request_buffer):
        request_buffer.open_in_editor()

    if layout.has_focus(response_buffer):
        response_buffer.open_in_editor()

    response_buffer.tempfile_suffix = get_extention(ApplicationState.response_history[-1])

@kb.add('c-@')
def send_request(event):
    response = send_raw_request(request_buffer.text)
    response_buffer.text = format_raw_response(response)
    ApplicationState.response_history.append(response)


@kb.add('c-c')
def exit_for_real(event):
    event.app.exit()

class ApplicationState:
    response_history = []

app = Application(layout=layout, full_screen=True, key_bindings=kb,
                  editing_mode=EditingMode.VI, mouse_support=True)
app.run()
