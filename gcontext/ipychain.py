from collections import ChainMap

import IPython
from IPython.core.magic import Magics, magics_class, line_magic, cell_magic

def load_ipython_extension(ip):
    ip.register_magics(ExtraContextMagics)
    # ip.events.register('pre_run_cell', auto_reload.pre_run_cell)
    # ip.events.register('post_execute', auto_reload.post_execute_hook)

additional_ctx = {
    'myglobal': int,
}

@magics_class
class ExtraContextMagics(Magics):

    @cell_magic
    def stop_after(self, line, cell):
        # raise error
        #
        opts = line
        user_ns = self.shell.user_ns
        self.shell.run_cell(cell)
        self.shell.user_ns = ChainMap(user_ns, {'line': line})

    # @line_magic
    # def inject(self, callabl):
    #     1
