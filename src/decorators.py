import functools
from colorama import Fore, Style

def welcome(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(Fore.RED + f'Welcome to {func.__name__}!', end='')
        print(Style.RESET_ALL)
        return func(*args, **kwargs)
    return wrapper

def debug(func):
    '''Print the debug info incl. function name and arguments'''
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        funcs_args = [repr(a) for a in args]
        funcs_kwargs = [f"{kw}={val!r}" for kw, val in kwargs.items()]
        print(Fore.RED+'[DEBUG] ', end='')
        print(Style.RESET_ALL, end='')
        print(f"Called {func.__name__}({','.join(funcs_args + funcs_kwargs)})")
        value = func(*args, **kwargs)
        print(Fore.RED+'[DEBUG] ', end='')
        print(Style.RESET_ALL, end='')
        print(f"{func.__name__!r} returned\n{value!r}")
        return value
    return wrapper