"""Experimental, conservative icing model; this is not a robot demonstration.

A measured piston position compresses a finite reservoir. Pressure, yield stress
and nozzle resistance determine flow. Star-tip parcels fall under gravity and
transfer their entire volume into a free-surface grid on first contact. A
conservative, yield-limited surface flow allows the icing to spread/slump. No
target, shell count, rubric or planned nozzle path is visible to this model.

Limitations: a single-valued surface cannot represent overhangs, long suspended
threads or voids. The model is suitable for investigating low shell deposits,
not yet evidence of calibrated buttercream. Properties below are declared
engineering starting values, not measurements of a real recipe.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np


@dataclass(frozen=True)
class IcingParameters:
    initial_volume_m3: float = 20e-6
    piston_radius_m: float = .0125
    bulk_modulus_pa: float = 160_000.
    yield_pressure_pa: float = 6_000.
    conductance_m3_per_pa_s: float = 3e-11
    nozzle_radius_m: float = .0025
    star_depth: float = .28
    star_lobes: int = 6
    density_kg_m3: float = 850.
    yield_slope: float = .75
    surface_mobility_m_per_s: float = .0003
    pressure_transfer_depth_m: float = .002
    maximum_substep_s: float = 1 / 480

    @property
    def piston_area_m2(self):
        return math.pi * self.piston_radius_m**2

    @property
    def stroke_m(self):
        return self.initial_volume_m3 / self.piston_area_m2

    def validate(self):
        values = vars(self)
        if not all(np.isfinite(v) and v > 0 for v in values.values()):
            raise ValueError("All material parameters must be finite and positive")
        if self.star_depth >= 1 or int(self.star_lobes) != self.star_lobes:
            raise ValueError("Invalid star nozzle")


class Icing:
    """State is SI units. X/Y grid coordinates are cell centres, in world space."""

    def __init__(self, params=None, *, dx=.0005, xlim=(.18, .42), ylim=(-.12, .12),
                 cake_bounds=(.21, .39, -.07, .07), cake_top=.8005,
                 table_top=.7475):
        self.p = params or IcingParameters()
        self.p.validate()
        if not np.isfinite(dx) or dx <= 0:
            raise ValueError("Cell spacing must be finite and positive")
        self.dx = float(dx)
        self.x = np.arange(xlim[0] + dx/2, xlim[1], dx)
        self.y = np.arange(ylim[0] + dx/2, ylim[1], dx)
        self.X, self.Y = np.meshgrid(self.x, self.y, indexing="ij")
        x0, x1, y0, y1 = cake_bounds
        self.on_cake = ((self.X >= x0) & (self.X <= x1) &
                        (self.Y >= y0) & (self.Y <= y1))
        self.base = np.where(self.on_cake, cake_top, table_top)
        self.cake_top = cake_top
        self.table_top = table_top
        self.reset()
        # Equal-area polar quadrature of an ordinary six-point star aperture.
        # Weights are exact for this discretisation and normalised once.
        theta = np.arange(24) * 2*math.pi/24
        outer = self.p.nozzle_radius_m*(1 + self.p.star_depth*np.cos(self.p.star_lobes*theta))
        radial = np.sqrt((np.arange(3)+.5)/3)
        self.nozzle_xy = np.array([[r*o*math.cos(t), r*o*math.sin(t)]
                                  for t, o in zip(theta, outer) for r in radial])
        self.weights = np.repeat(outer**2, 3)
        self.weights /= self.weights.sum()
        self.aperture_area_m2 = float(math.pi*np.mean(outer**2))

    def reset(self):
        self.volume = np.zeros_like(self.base)
        self.air_pos = np.empty((0, 3))
        self.air_vel = np.empty((0, 3))
        self.air_volume = np.empty(0)
        self.emitted_m3 = 0.
        self.lost_m3 = 0.
        self.pressure_pa = 0.
        self.last_flow_m3_s = 0.
        self.cake_damage_depth_m = 0.
        self.time_s = 0.
        self.nozzle_position = None
        self.nozzle_rotation = None

    @property
    def height(self):
        return self.volume/self.dx**2

    def reservoir_pressure(self, piston_m):
        if not np.isfinite(piston_m) or not -1e-5 <= piston_m <= self.p.stroke_m+1e-5:
            raise ValueError("Measured piston position outside the physical stroke")
        compression = max(0., self.p.piston_area_m2*float(piston_m)-self.emitted_m3)
        return self.p.bulk_modulus_pa * compression / self.p.initial_volume_m3

    def step(self, dt, *, piston_m, nozzle_pos, nozzle_rotation, nozzle_velocity=(0.,0.,0.)):
        """Advance material using measured dispenser state, never policy commands.

        The nozzle's local +Z is the outward flow axis. Return pressure reaction
        in newtons for the piston and equal/opposite force for its barrel.
        """
        dt = float(dt)
        pos, rot, vel = (np.asarray(v, float) for v in
                         (nozzle_pos, nozzle_rotation, nozzle_velocity))
        if (not np.isfinite(dt) or dt <= 0 or pos.shape != (3,) or rot.shape != (3,3)
                or vel.shape != (3,) or not all(np.isfinite(a).all() for a in (pos,rot,vel))
                or not np.allclose(rot.T@rot, np.eye(3), atol=1e-6)
                or not np.isclose(np.linalg.det(rot), 1., atol=1e-6)):
            raise ValueError("Finite position, proper rotation and positive dt required")
        self.nozzle_position,self.nozzle_rotation=pos.copy(),rot.copy()
        n = max(1, math.ceil(dt/self.p.maximum_substep_s))
        h = dt/n
        total = 0.
        for _ in range(n):
            self.pressure_pa = self.reservoir_pressure(piston_m)
            drive = max(0., self.pressure_pa-self.p.yield_pressure_pa)
            remaining = max(0., self.p.initial_volume_m3-self.emitted_m3)
            v = min(remaining, self.p.conductance_m3_per_pa_s*drive*h)
            if v > 0:
                # Parcels originate inside the physical aperture; all flow is
                # governed by pressure and the remaining reservoir volume.
                local = np.column_stack((self.nozzle_xy, np.zeros(len(self.weights))))
                p = local@rot.T + pos
                exit_speed = v/h/self.aperture_area_m2
                u = np.repeat((vel+rot[:,2]*exit_speed)[None,:], len(p), axis=0)
                self.air_pos = np.vstack((self.air_pos, p))
                self.air_vel = np.vstack((self.air_vel, u))
                self.air_volume = np.r_[self.air_volume, v*self.weights]
                self.emitted_m3 += v
                total += v
            self._fall(h)
            self._relax(h)
            self.time_s += h
        self.last_flow_m3_s = total/dt
        return self.reservoir_pressure(piston_m)*self.p.piston_area_m2

    def _indices(self, xy):
        ij = np.floor((xy - np.array((self.x[0], self.y[0])) + self.dx/2)/self.dx).astype(int)
        valid = ((ij[:,0]>=0)&(ij[:,0]<len(self.x))&(ij[:,1]>=0)&(ij[:,1]<len(self.y)))
        return ij, valid

    def _fall(self, dt):
        if not len(self.air_volume):
            return
        old = self.air_pos.copy()
        self.air_vel[:,2] -= 9.81*dt
        self.air_pos += self.air_vel*dt
        ij, valid = self._indices(self.air_pos[:,:2])
        surface = np.full(len(ij), -np.inf)
        ix = np.flatnonzero(valid)
        surface[ix] = self.base[ij[ix,0],ij[ix,1]]+self.height[ij[ix,0],ij[ix,1]]
        landed = valid & (self.air_pos[:,2] <= surface)
        if landed.any():
            # Local volume accumulation, independent of intended decoration.
            # Star-aperture cross sections are preserved by parcel locations.
            np.add.at(self.volume, (ij[landed,0],ij[landed,1]), self.air_volume[landed])
        escaped = (~valid & (self.air_pos[:,2]<self.table_top)) | (self.air_pos[:,2]<self.table_top-.2)
        self.lost_m3 += float(self.air_volume[escaped & ~landed].sum())
        keep = ~(landed|escaped)
        self.air_pos, self.air_vel, self.air_volume = (a[keep] for a in
                                                      (self.air_pos,self.air_vel,self.air_volume))

    def _pressure_head(self):
        """Pressure-driven spreading only beneath the measured star aperture.

        When deposited cream submerges the outlet, its upstream surface receives
        reservoir pressure over the declared 2 mm transfer depth. This is a
        local constitutive approximation, independent of targets or shapes.
        """
        if self.nozzle_position is None or self.pressure_pa<=0:return 0.
        displacement=np.stack((self.X-self.nozzle_position[0],self.Y-self.nozzle_position[1],
                               self.base+self.height-self.nozzle_position[2]),axis=-1)
        local=displacement@self.nozzle_rotation
        radius=np.hypot(local[:,:,0],local[:,:,1])
        angle=np.arctan2(local[:,:,1],local[:,:,0])
        aperture=self.p.nozzle_radius_m*(1+self.p.star_depth*np.cos(self.p.star_lobes*angle))
        submerged=np.clip(-local[:,:,2]/self.p.pressure_transfer_depth_m,0.,1.)*(radius<aperture)
        return self.pressure_pa*submerged/(self.p.density_kg_m3*9.81)

    def _relax(self, dt):
        """Conservative nearest-cell viscoplastic flow with a yield slope.

        A donor sends at most one quarter of its current volume per face. The
        cap enforces positivity without adding/removing material. Flux uses
        actual gravity/pressure head, including cake-edge spill. No material is
        generated by spreading, even when the surface touches an idle nozzle.
        """
        if not np.any(self.volume):return
        pressure_head=self._pressure_head()
        for axis in (0, 1):
            left = (slice(None,-1),slice(None)) if axis == 0 else (slice(None),slice(None,-1))
            right = (slice(1,None),slice(None)) if axis == 0 else (slice(None),slice(1,None))
            surface = self.base+self.height+pressure_head
            gradient = (surface[left]-surface[right])/self.dx
            excess = np.maximum(np.abs(gradient)-self.p.yield_slope, 0.)
            donor = np.where(gradient>0, self.volume[left], self.volume[right])
            flux = self.p.surface_mobility_m_per_s*dt*self.dx**2*excess
            flux = np.minimum(flux, donor*.24)*np.sign(gradient)
            self.volume[left] -= flux
            self.volume[right] += flux
        if self.volume.min(initial=0.) < -1e-18:
            raise ArithmeticError("Material solver produced negative volume")

    def tool_contact(self, points, velocities, dt, *, stiffness_n_m=1500., damping_ns_m=1.):
        """Penalty contact with the measured nozzle surface; returns reaction N.

        Points are samples on the real metal tip, not its centre or TCP. Cake
        penetration over 1 mm is irreversible damage for judging. Cream is
        displaced conservatively away from an intruding tip. This is an
        experimental sampled contact approximation, not a full collision mesh.
        """
        p, v = np.asarray(points,float), np.asarray(velocities,float)
        if p.ndim!=2 or p.shape[1]!=3 or v.shape!=p.shape or not np.isfinite(p).all() or not np.isfinite(v).all():
            raise ValueError("Contact points/velocities must be finite N by 3 arrays")
        ij, valid = self._indices(p[:,:2])
        reactions = np.zeros_like(p)
        for k in np.flatnonzero(valid):
            i,j=ij[k]
            top=self.base[i,j]+self.volume[i,j]/self.dx**2
            depth=top-p[k,2]
            if depth<=0:
                continue
            reactions[k,2]=max(0.,stiffness_n_m*depth-damping_ns_m*v[k,2])
            if self.on_cake[i,j]:
                self.cake_damage_depth_m=max(self.cake_damage_depth_m,self.base[i,j]-p[k,2])
            moved=min(self.volume[i,j],depth*self.dx**2)
            neighbours=[(a,b) for a,b in ((i-1,j),(i+1,j),(i,j-1),(i,j+1))
                        if 0<=a<len(self.x) and 0<=b<len(self.y)]
            self.volume[i,j]-=moved
            for a,b in neighbours:
                self.volume[a,b]+=moved/len(neighbours)
        return reactions

    def balance(self):
        retained=float(self.volume.sum())
        airborne=float(self.air_volume.sum())
        return {"initial_m3":self.p.initial_volume_m3,
                "reservoir_m3":self.p.initial_volume_m3-self.emitted_m3,
                "deposited_m3":retained,"airborne_m3":airborne,"lost_m3":self.lost_m3,
                "error_m3":self.emitted_m3-retained-airborne-self.lost_m3}

    def save(self, path):
        np.savez_compressed(path,x=self.x,y=self.y,base=self.base,volume=self.volume,
                            on_cake=self.on_cake,dx=self.dx,emitted_m3=self.emitted_m3,
                            lost_m3=self.lost_m3,airborne_m3=float(self.air_volume.sum()),
                            damage_depth_m=self.cake_damage_depth_m,time_s=self.time_s)
