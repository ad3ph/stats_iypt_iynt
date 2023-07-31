import numpy as np
from time import sleep as sleep_sec

def rd(x,y=0):
    ''' A classical mathematical rounding by Voznica '''
    x = round(x, y+2)
    m = int('1'+'0'*y) # multiplier - how many positions to the right
    q = x*m # shift to the right by multiplier
    c = int(q) # new number
    i = int( (q-c)*10 ) # indicator number on the right

    if i >= 5:
        c += 1

    return c/m