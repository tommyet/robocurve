"""Explicit PhysX lifecycle for native diagnostics under Isaac Sim 6.1.

Avoids deprecated World.reset, which did not attach the PhysX stage on the
verified runtime. Rendering uses the same USD stage; physics always advances
only through the explicit simulate/fetch_results calls below.
"""


class ProbeRuntime:
    def __init__(self, app, dt, render=False):
        from pxr import Gf, Usd, UsdGeom, UsdPhysics, UsdUtils
        from omni.physx import get_physx_interface, get_physx_simulation_interface
        self.app, self.dt, self.time = app, dt, 0.
        self.sim, self.physics = get_physx_simulation_interface(), get_physx_interface()
        self.cache = UsdUtils.StageCache.Get()
        self.fabric = None
        if render:
            import carb.settings
            import omni.usd
            import omni.kit.app
            # NVIDIA's fabric output extension must be enabled before the
            # rendered stage is loaded. It reads PhysX results directly.
            settings=carb.settings.get_settings()
            settings.set_bool('/app/useFabricSceneDelegate',True)
            manager=omni.kit.app.get_app().get_extension_manager()
            manager.set_extension_enabled_immediate('omni.physx.fabric',True)
            import omni.physxfabric
            from omni.physxfabric.bindings import _physxFabric as fabric_settings
            settings.set_bool(fabric_settings.SETTING_FABRIC_ENABLED,True)
            settings.set_bool(fabric_settings.SETTING_FABRIC_UPDATE_POINTS,True)
            settings.set_bool(fabric_settings.SETTING_FABRIC_UPDATE_TRANSFORMATIONS,True)
            for key in ('updateToUsd','updateParticlesToUsd','updateVelocitiesToUsd',
                        'updateForceSensorsToUsd','updateResidualsToUsd'):
                settings.set_bool('/physics/'+key,False)
            self.fabric=omni.physxfabric.get_physx_fabric_interface()
            context = omni.usd.get_context()
            context.new_stage()
            self.stage = context.get_stage()
        else:
            self.stage = Usd.Stage.CreateInMemory()
        self.cache.Insert(self.stage)
        self.stage_id = self.cache.GetId(self.stage).ToLongInt()
        self.attached = False
        UsdGeom.SetStageUpAxis(self.stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(self.stage, 1.)
        scene = UsdPhysics.Scene.Define(self.stage, '/World/PhysicsScene')
        scene.CreateGravityDirectionAttr(Gf.Vec3f(0.,0.,-1.))
        scene.CreateGravityMagnitudeAttr(9.81)

    def start(self):
        import carb.settings
        # GPU dynamics alone does not choose the GPU tensor pipeline. Native
        # surface nodal getters are not implemented by CpuSimulationView.
        settings=carb.settings.get_settings()
        settings.set_bool('/physics/suppressReadback', True)
        settings.set_int('/physics/cudaDevice', 0)
        self.sim.attach_stage(self.stage_id)
        self.attached = True
        if self.fabric is not None:
            self.fabric.attach_stage(self.stage_id)

    def step(self, render=False):
        self.sim.simulate(self.dt, self.time)
        self.sim.fetch_results()
        self.time += self.dt
        if render:
            self.render()

    def render(self):
        if self.fabric is None:
            raise RuntimeError('Rendering was not enabled for this native probe')
        # Same native forced output used by IsaacLab PhysxManager.forward.
        # The timeline is stopped, so ordinary timeline-gated update is not
        # sufficient. This changes no physics state or authored point data.
        self.fabric.force_update(0.0,0.0)
        self.app.update()

    def close(self):
        if self.attached:
            if self.fabric is not None:
                self.fabric.detach_stage()
            self.sim.detach_stage()
            self.attached = False
        self.cache.Erase(self.stage)
