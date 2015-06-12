#
# class Exit(Exception):
#     def __init__(self, **kwargs):
#         self.__dict__.update(kwargs)
#
#
# class CriticalHook(Hook):
#
#     def __init__(self, func):
#         super().__init__(func)
#         self.error = Exit()
#
#     def __enter__(self):
#         super().__enter__()
#         return self.error
#
#     def __exit__(self, *exc):
#         super().__exit__(*exc)
#         if exc and issubclass(exc[0], Exit):
#             return True
#
#
# class exit_before(CriticalHook):
#
#     type = pre_hook
#
#     def execute(self, *args, **kwargs):
#         self.error.args = args
#         self.error.kwargs = kwargs
#         raise self.error
#
#
# class exit_after(CriticalHook):
#
#     type = post_hook
#
#     def execute(self, *args, ret=Missing, **kwargs):
#         self.error.args = args
#         self.error.kwargs = kwargs
#         self.error.ret = ret
#         raise self.error
