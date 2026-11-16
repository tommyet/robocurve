"""Compiled numerical kernels for the uncreased sheet (no task geometry)."""
import math
import numpy as np
from numba import njit


@njit(cache=True)
def hinges(p, bends):
    angle = np.empty(len(bends))
    grad = np.empty((len(bends), 4, 3))
    for i in range(len(bends)):
        q0, q1, q2, q3 = bends[i]
        ex, ey, ez = p[q1,0]-p[q0,0],p[q1,1]-p[q0,1],p[q1,2]-p[q0,2]
        ux, uy, uz = p[q2,0]-p[q0,0],p[q2,1]-p[q0,1],p[q2,2]-p[q0,2]
        vx, vy, vz = p[q3,0]-p[q0,0],p[q3,1]-p[q0,1],p[q3,2]-p[q0,2]
        ax, ay, az = ey*uz-ez*uy, ez*ux-ex*uz, ex*uy-ey*ux
        bx, by, bz = vy*ez-vz*ey, vz*ex-vx*ez, vx*ey-vy*ex
        ll = max(math.sqrt(ex*ex+ey*ey+ez*ez), 1e-10)
        aa = max(ax*ax+ay*ay+az*az, 1e-16)
        bb = max(bx*bx+by*by+bz*bz, 1e-16)
        norm = math.sqrt(aa*bb)
        sine = ((ay*bz-az*by)*ex+(az*bx-ax*bz)*ey+(ax*by-ay*bx)*ez)/(norm*ll)
        cosine = (ax*bx+ay*by+az*bz)/norm
        angle[i] = math.atan2(sine, cosine)
        grad[i,2,0],grad[i,2,1],grad[i,2,2] = -ax*ll/aa,-ay*ll/aa,-az*ll/aa
        grad[i,3,0],grad[i,3,1],grad[i,3,2] = -bx*ll/bb,-by*ll/bb,-bz*ll/bb
        t2 = (ux*ex+uy*ey+uz*ez)/(ll*ll)
        t3 = (vx*ex+vy*ey+vz*ez)/(ll*ll)
        for k in range(3):
            grad[i,0,k] = -(1-t2)*grad[i,2,k]-(1-t3)*grad[i,3,k]
            grad[i,1,k] = -t2*grad[i,2,k]-t3*grad[i,3,k]
    return angle, grad


@njit(cache=True)
def stretch(p, edges, rest, order, w):
    for index in order:
        i, j = edges[index]
        x = p[j, 0] - p[i, 0]
        y = p[j, 1] - p[i, 1]
        z = p[j, 2] - p[i, 2]
        ll = math.sqrt(x*x + y*y + z*z)
        scale = (ll-rest[index]) / max(ll*(w[i]+w[j]), 1e-12)
        p[i, 0] += x*scale*w[i]
        p[i, 1] += y*scale*w[i]
        p[i, 2] += z*scale*w[i]
        p[j, 0] -= x*scale*w[j]
        p[j, 1] -= y*scale*w[j]
        p[j, 2] -= z*scale*w[j]


@njit(cache=True)
def solve(p, edges, rest, order, bends, stiffness, rest_angle, w,
          ids, targets, floor, iterations):
    for _ in range(iterations):
        stretch(p, edges, rest, order, w)
        angle, grad = hinges(p, bends)
        delta = np.zeros_like(p)
        counts = np.zeros(len(p))
        for i in range(len(bends)):
            error = math.atan2(math.sin(angle[i]-rest_angle[i]),
                               math.cos(angle[i]-rest_angle[i]))
            den = 0.
            for j in range(4):
                den += w[bends[i, j]]*(grad[i,j,0]**2+grad[i,j,1]**2+grad[i,j,2]**2)
            strength = -stiffness[i]*error/max(den, 1e-12)
            for j in range(4):
                index = bends[i, j]
                counts[index] += 1.
                for k in range(3):
                    delta[index, k] += grad[i, j, k]*strength*w[index]
        for i in range(len(p)):
            for k in range(3):
                p[i, k] += delta[i, k]/max(1., counts[i]/2.)
            p[i, 2] = max(p[i, 2], floor)
        for i in range(len(ids)):
            p[ids[i]] = targets[i]


@njit(cache=True)
def restore_stretch(p, edges, rest, order, w, floor, iterations):
    for _ in range(iterations):
        stretch(p, edges, rest, order, w)
        for i in range(len(p)):
            p[i, 2] = max(p[i, 2], floor)
