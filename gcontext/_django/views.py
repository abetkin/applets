
import gcontext as g


class ContextDispatch:

    @g.method
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
