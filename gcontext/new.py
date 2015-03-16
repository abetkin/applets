
from gcontext import TC, post_hook, pre_hook
from django.views.generic import View

class Dj(TC):
    url = '/'

    # .request .view

    @post_hook(View.dispatch)
    def m(self, view, req, ):
        1

    @pre_hook()
    def replace(self):
        1


'''

subTests (subtest failure -> ?)
global exc_info (exc from ?)



def for_this_url():
    return '/'

%% for_this_url
print(req)

'''

# ---------------

# ipython: inject / remove ns

# --------------
