"""Native RGB evidence for bounded physics diagnostics; no geometry animation."""
from pathlib import Path
import numpy as np


class ProbeCapture:
    def __init__(self, stage, output, eye, target, fps=10):
        from pxr import Gf, UsdGeom, UsdLux
        import omni.replicator.core as rep
        import imageio.v2 as imageio
        self.output = Path(output)
        self.fps = fps
        self.frames = 0
        self.nonblank_frames = 0
        self.writer = None
        dome = UsdLux.DomeLight.Define(stage, '/World/DiagnosticLight')
        dome.CreateIntensityAttr(900.)
        camera = UsdGeom.Camera.Define(stage, '/World/DiagnosticCamera')
        camera.CreateFocalLengthAttr(28.)
        camera.CreateHorizontalApertureAttr(36.)
        camera.CreateClippingRangeAttr(Gf.Vec2f(.01, 20.))
        transform = Gf.Matrix4d().SetLookAt(Gf.Vec3d(*eye), Gf.Vec3d(*target), Gf.Vec3d(0.,0.,1.)).GetInverse()
        camera.AddTransformOp().Set(transform)
        self.product = rep.create.render_product(str(camera.GetPath()), (640,480))
        self.rgb = rep.AnnotatorRegistry.get_annotator('rgb')
        self.rgb.attach([self.product])
        self.writer = imageio.get_writer(self.output/'diagnostic.mp4', fps=fps,
            codec='libx264', pixelformat='yuv420p', macro_block_size=1,
            ffmpeg_params=['-movflags','+faststart'])

    def capture(self, label=None):
        from PIL import Image
        value = self.rgb.get_data()
        if isinstance(value, dict):
            value = value['data']
        rgb = np.asarray(value)
        if rgb.ndim != 3 or rgb.shape[:2] != (480,640) or rgb.shape[-1] not in (3,4):
            raise RuntimeError(f'Native diagnostic camera returned {rgb.shape}')
        rgb = np.asarray(rgb[:,:,:3], dtype=np.uint8)
        if not np.isfinite(rgb).all():
            raise RuntimeError('Nonfinite native diagnostic image')
        self.frames += 1
        self.nonblank_frames += int(np.std(rgb.astype(float)) > 2.)
        self.writer.append_data(rgb)
        if label:
            Image.fromarray(rgb).save(self.output/f'{label}.png')

    def close(self):
        if self.writer is not None:
            self.writer.close()
            self.writer = None
        self.rgb.detach([self.product])
        self.product.destroy()
        return dict(frames=self.frames, nonblank_frames=self.nonblank_frames,
                    resolution=[640,480], fps=self.fps)
