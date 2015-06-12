import gcontext as g

class D:

    @g.grab_instance('dd')
    def f(self):
        print('context:', g.get_context())
        return 1


d = D()

class C:

    @g.grab_instance('cc')    # g.grabctx(grabber) # {''cc': _.self}
    def m(self):
        res = d.f()
        print('->', res)




def myhook(*args, **kw):
    print(args, kw)


g.pre_signal(C.m).connect(myhook)


if __name__ == '__main__':
    ob = C()
    ob.m()