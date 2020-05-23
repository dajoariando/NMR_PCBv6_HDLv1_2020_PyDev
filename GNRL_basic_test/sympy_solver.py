# this is from tutorial in Youtube : https://www.youtube.com/watch?v=kx2GzBeGPco
# named "SymPy (Symbolic Expressions on Python) in one video"

import numpy as np
from sympy import *
import matplotlib.pyplot as plt
import numpy as np

# defining symbols
x = symbols( 'x' )
f = x ** 2
ans = f.subs( x, 2 )

# defining functions
print( N( sqrt( 2 ) ) )
f = sin( x )
fx = lambdify( x, f, modules = ['numpy'] )
xvals = np.linspace( -10, 10, 100 )
plt.plot( xvals, fx( xvals ) )
# plt.show()

# pretty print and latex
pprint( sqrt( x ** 2 ) )
print( latex( sqrt( x ** 2 ) ) )

# simplify expressions
f = sin( x ) ** 2 + cos( x ) ** 2 + sin( x )
print( f.simplify() )

# expand expressions
f = ( x + 1 ) ** 2
print( f.expand() )

# factor expressions
f = ( x ** 3 - x ** 2 + x - 1 )
print( f.factor() )

# defining multiple symbols
a = Symbol( 'a' )
x, y, z = symbols ( 'x y z' )

# collect
f = x * y + x - 3 + 2 * x ** 2 - z * x ** 2 + x ** 3
pprint( f )
pprint( collect( f, x ) )

# cancel variables
f = ( x ** 2 + 2 * x + 1 ) / ( x ** 2 + x )
pprint( f )
pprint( cancel( f ) )

# partial fraction
f = ( 4 * x ** 3 + 21 * x ** 2 + 10 * x + 12 ) / ( x ** 4 + 5 * x ** 3 + 5 * x ** 2 + 4 * x )
pprint( f )
print( '--------' )
pprint( apart( f ) )

# trigonometri identities
f = sin( x ) ** 4 - 2 * sin( x ) ** 2 * cos( x ) ** 2 + cos( x ) ** 4
print( '--------' )
pprint( f )
print( '--------' )
pprint( simplify( f ) )
print( '--------' )
pprint( trigsimp( f ) )

f = sin( x + y )
print( '--------' )
pprint( f )
print( '--------' )
pprint( expand_trig( f ) )

print( '--------' )

pprint( expand_trig( tan( 2 * x ) ) )

# power simpification
a, b = symbols( 'a b' )
f = x ** a * x ** b
pprint( f )
pprint( powsimp( f ) )

f = x ** a * y ** a
pprint( f )
pprint( powsimp( f, force = 'True' ) )

# log operation
f = log( x ** 2 )
pprint( expand_log( f, force = 'True' ) )

# Solvers
f = Eq( x ** 2, 1 )
pprint( f )
ans = solveset( f, x )  # function and the variable to solve
print( ans )

ans = solveset( sin( x ) - 1, x )
pprint( f )

print( '--------' )

# linear equation solver
ans = linsolve( [x + y + z - 1, x + y + 2 * z - 3], ( x, y, z ) )
pprint( ans )

ans = linsolve( [x + y + z - 1, x + y + 2 * z - 3, 2 * x + y - z - 5], ( x, y, z ) )
pprint( ans )

# variable substitution
f1 = x + y + z - 1
f2 = x + y + 2 * z - 3
f3 = 2 * x + y - z - 5
print( f1.subs( x, 8 ).subs( y, -9 ).subs( z, 2 ) )

# matrix representation
A = Matrix( ( ( 1, 1, 1 ), ( 1, 1, 2 ), ( 2, 1, -1 ) ) )
pprint( A )
B = Matrix( ( 1, 3, 5 ) )
pprint( B )

system = A, B
ans = linsolve( system )
pprint( ans )

# system of nonlinear equation
ans = nonlinsolve( [x ** 2 + 1, y ** 2 + 1], [x, y] )
pprint( ans )


# system with defined functions and multiple non-linear equation
def addition( a, b ):
    return a + b


def subtract( a, b ):
    return a - b


x, y = symbols( 'x y' )
f = Eq( addition( x, y ), 50 )
g = Eq( subtract( x, y ), 10 )
ans = linsolve( [f, g], ( x, y ) )
