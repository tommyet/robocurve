"""Final native judging photographs; never supplied to a policy or controller."""
import numpy as np


def capture_final(base,output):
    import omni.usd
    import omni.replicator.core as rep
    from pxr import Gf,UsdGeom
    from PIL import Image
    stage=omni.usd.get_context().get_stage();metadata=[]
    configs=[('top',(.235,0.,1.15),(.235,0.,.8005),(0.,1.,0.),50.,(1280,960)),
             ('side',(.060,0.,.875),(.235,0.,.804),(0.,0.,1.),28.,(1280,720))]
    for name,eye,target,up,focal,resolution in configs:
        camera=UsdGeom.Camera.Define(stage,f'/World/Judging_{name}')
        camera.CreateFocalLengthAttr(focal);camera.CreateHorizontalApertureAttr(20.955)
        camera.CreateClippingRangeAttr(Gf.Vec2f(.005,10.))
        transform=Gf.Matrix4d().SetLookAt(Gf.Vec3d(*eye),Gf.Vec3d(*target),Gf.Vec3d(*up)).GetInverse()
        camera.AddTransformOp().Set(transform)
        product=rep.create.render_product(str(camera.GetPath()),resolution)
        rgb=rep.AnnotatorRegistry.get_annotator('rgb');rgb.attach([product])
        try:
            # Rendering only. The final physics state and material stay fixed.
            for _ in range(5):base.sim.render()
            value=rgb.get_data();value=value['data'] if isinstance(value,dict) else value
            pixels=np.asarray(value)
            if pixels.shape[:2]!=(resolution[1],resolution[0]) or pixels.ndim!=3:
                raise RuntimeError(f'Missing native judging image: {name}')
            Image.fromarray(pixels[:,:,:3].astype(np.uint8)).save(output/f'judging-{name}.png')
            metadata.append({'name':name,'eye_m':eye,'target_m':target,'resolution':resolution,'policy_input':False})
        finally:
            rgb.detach([product]);product.destroy()
    return metadata
