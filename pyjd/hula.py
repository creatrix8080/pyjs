import os
import sys
import hulahop
#from sugar import env
#hulahop.startup(os.path.join(env.get_profile_path(), 'gecko'))
hulahop.startup('/home/lkcl/test')

from hulahop.webview import WebView

import gtk
import gobject
import xpcom

from xpcom.nsError import *
from xpcom import components
from xpcom.components import interfaces

from progresslistener import ProgressListener


class ContentInvoker:
    _com_interfaces_ = interfaces.nsIDOMEventListener

    def __init__(self, browser, event_fn):
        self._browser = browser
        self._event_fn = event_fn

    def handleEvent(self, event):
        self._event_fn(self, event, False)

class Browser(WebView):
    def __init__(self, application, appdir):
        WebView.__init__(self)
        self.progress = ProgressListener()
        self.application = application
        self.appdir = appdir
        self.already_initialised = False

        io_service_class = components.classes[ \
        "@mozilla.org/network/io-service;1"]
        io_service = io_service_class.getService(interfaces.nsIIOService)

        # Use xpcom to turn off "offline mode" detection, which disables
        # access to localhost for no good reason.  (Trac #6250.)
        io_service2 = io_service_class.getService(interfaces.nsIIOService2)
        io_service2.manageOfflineStatus = False

        self.progress.connect('loading-stop', self._loaded)
        self.progress.connect('loading-progress', self._loading)

    def load_app(self):

        self.load_uri('file://'+os.path.abspath(self.application))

    def do_setup(self):
        WebView.do_setup(self)
        self.progress.setup(self)
        
    def addEventListener(self, node, event_name, event_fn):
        
        listener = xpcom.server.WrapObject(ContentInvoker(self, event_fn),
                                            interfaces.nsIDOMEventListener)
        node.addEventListener(event_name, listener, False)

    def mash_attrib(self, attrib_name):
        return attrib_name

    def _addWindowEventListener(self, event_name, event_fn):
        
        listener = xpcom.server.WrapObject(ContentInvoker(self, event_fn),
                                            interfaces.nsIDOMEventListener)
        self.window_root.addEventListener(event_name, listener, False)

    def _loaded(self, progress_listener):

        print "loaded"

        if self.already_initialised:
            return
        self.already_initialised = True

        dw = self.get_dom_window()
        doc = dw.document

        from pyjamas.__pyjamas__ import pygwt_processMetas, set_main_frame
        set_main_frame(self)

        (pth, app) = os.path.split(self.application)
        if self.appdir:
            pth = os.path.abspath(self.appdir)
        sys.path.append(pth)

        for m in pygwt_processMetas():
            minst = module_load(m)
            minst.onModuleLoad()

    def _loading(self, progress_listener, progress):

        print "loading", progress

def setup():

    import sys
    import os
    if len(sys.argv) < 2:
        print "usage: %s application[.py|.html]" % sys.argv[0]
        sys.exit(-1)
    if len(sys.argv) == 3:
        appdir = sys.argv[2]
    else:
        appdir = None

    win = gtk.Window(gtk.WINDOW_TOPLEVEL)
    win.set_size_request(800,600)
    win.connect('destroy', gtk.main_quit)

    global wv
    wv = Browser(sys.argv[1], appdir)

    wv.show()

    win.add(wv)

    win.show()

    #wv.load_uri('http://wiki.laptop.org/go/Guido_van_Robot')
    #wv.load_uri('file:///home/lkcl/src/pyjamas-desktop/pyjamas-gtkmozembed/blank.html')
    #wv.load_uri('file://'+os.path.abspath(sys.argv[1]))
    wv.load_app()

    dw = wv.get_dom_window()
    doc = wv.web_navigation.document
    print wv.web_navigation.currentURI

    gtk.main()

def module_load(m):
    minst = None
    exec """\
from %(mod)s import %(mod)s
minst = %(mod)s()
""" % ({'mod': m})
    return minst


def main():
    setup()
        