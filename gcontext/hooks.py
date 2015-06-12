
from .signal import pre_signal

def myhook(self, request, **kw):
    print(request)


pre_signal(APIView.get).connect(myhook)