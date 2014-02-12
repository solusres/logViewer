#!/usr/bin/env python

import sys
import os
import cgi
import re
import BaseHTTPServer
from StringIO import StringIO
from SimpleHTTPServer import SimpleHTTPRequestHandler
from functools import partial
from urllib import unquote
import pygrep

CHANNEL_NAME = "#channelName"
SERVER_NAME = "serverName"

logname_regex = re.compile("(\d{4}-\d{2}-\d{2}\.log)")
link_lognames = partial(logname_regex.sub, r'<a href="\1">\1</a>')

def search(query):
    f = StringIO()

    query = unquote(query)

    results = pygrep.do(query)
    
    if (results is not None):
        qre = re.compile("(%s)" % query)
        results = qre.sub(r'<span class="query">\1</span>', results)

        results = results.split('\n')
        
        results = map(lambda x: "<hr/>" if x=="--" else x, results)

        results = ["<div>%s</div>" % line for line in map(link_lognames, results)]
    else:
        results = "No results found."
    
    style = """
    <style>
        .query {
            background: yellow;
        }
    </style>
    """
    
    f.write("<title>Search results for %s</title>" % query)
    f.write(style)
    f.write("<code>")
    f.write("".join(results))
    f.write("</code>")
    f.seek(0)
    return f
    

class MyRequestHandler(SimpleHTTPRequestHandler):
    # Changes here
    SimpleHTTPRequestHandler.extensions_map['.log'] = "text/plain"
    allowed_filetypes = ["log"]

    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).

        Return value is either a file object, or None (indicating an
        error).  In either case, the headers are sent, making the
        interface the same as for send_head().

        """
        try:
            list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        
        # Changes here
        list = [entry for entry in list if entry[-3:] in MyRequestHandler.allowed_filetypes]
        
        list.sort(lambda a, b: cmp(a.lower(), b.lower()))
        f = StringIO()
        
        # Changes here
        f.write("<title>%s Logs</title>\n" % CHANNEL_NAME)
        f.write("<h2>Logs from %s on %s</h2>\n" % (CHANNEL_NAME, SERVER_NAME))
        
        f.write("<p>Looking for something in particular?  Try searching with the query string, like <a href='?example'>this</a>.  (Regex works too!)</p>")
        
        f.write("<hr>\n<ul>\n")
        for name in list:
            fullname = os.path.join(path, name)
            displayname = linkname = name = cgi.escape(name)
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays with @ and links with /
            f.write('<li><a href="%s">%s</a>\n' % (linkname, displayname))
        f.write("</ul>\n<hr>\n")
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        return f
        
    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """
        
        # Changes here
        if "?" in self.path:
            ctype = "text/html"
            f = search(self.path[self.path.index("?")+1:])
        else:
            path = self.translate_path(self.path)
            
            f = None
            if os.path.isdir(path):
                for index in "index.html", "index.htm":
                    index = os.path.join(path, index)
                    if os.path.exists(index):
                        path = index
                        break
                else:
                    return self.list_directory(path)


            else:
                ctype = self.guess_type(path)
                if ctype.startswith('text/'):
                    mode = 'r'
                else:
                    mode = 'rb'
                try:
                    f = open(path, mode)
                except IOError:
                    self.send_error(404, "File not found")
                    return None
                
        self.send_response(200)
        self.send_header("Content-type", ctype)
        self.end_headers()
        return f

if sys.argv[1:]:
    port = int(sys.argv[1])
else:
    port = 8888
    
server_address = ('', port)

httpd = BaseHTTPServer.HTTPServer(server_address, MyRequestHandler)

sa = httpd.socket.getsockname()

print "Serving HTTP on", sa[0], "port", sa[1], "..."

httpd.serve_forever()
