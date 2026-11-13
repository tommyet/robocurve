# Paper model and the meaning of its limits

The paper is a flexible 100 µm surface mesh with explicit staple punctures.
Native FEM computes its motion and contact. It is an isotropic elastic
approximation; it does not render fibre fracture or permanent creases.

The 0.3% membrane limit is a conservative approximation boundary, **not a tear
detector**. Its breach still invalidates a task trial. The 0.3% outer-fibre
bending estimate is now a recorded warning in the task monitor, because an
ordinary crease can remain intact. It corresponds to a radius of about 17 mm,
much gentler than many harmless folds. Older strict elastic diagnostics retain
their original reported failures; this distinction does not alter their physics.

There is a plausible basis for the elastic boundary. In Yoshihara and
Yoshinobu's copy-paper experiments, the plotted directional modulus is roughly
2–4.3 GPa and the stress at onset of nonlinearity roughly 5–12.5 MPa. Their
ratios are approximately 0.25–0.3% strain. These are readings of published
figures, not measurements of this task's paper. The same paper's tensile curves
continue well beyond that initial elastic region. The study explicitly models
the later response as anisotropic plasticity.
[Study and figures](https://doi.org/10.2488/jwrs.61.74)

A local maximum-strain check also cannot predict crack growth around a puncture
on its own. Experiments on notched copy paper show a dependence on material
direction and notch dimensions; fracture and stress-based models do not give
identical predictions. Our fixed topology therefore stops before claiming an
unsupported destructive outcome, while a separate geometry check rejects wire
crossing intact triangles.
[Notched-paper experiments](https://www.jstage.jst.go.jp/article/jsms/67/8/67_761/_pdf/-char/ja)

For the task, damage means a new tear, a hole enlarged by more than the stated
judging tolerance, or broken hardware. A crease by itself is not a tear.
A successful native trial must stay within its declared membrane approximation,
keep contact topology intact and release the sheets through the original
punctures. Neither a low final strain nor a visually flat final frame repairs
an earlier invalid trial. The final submission must disclose the absence of
post-fracture rendering.

The supported, coarser puncture mesh and bounded native contact correction now
settle an unstapled pair for 0.1 seconds below the membrane limit. Curvature
warnings touch only 0.078% and 0.057% of the sheets' area, near the punctures;
their worst local hinge angles are 4.66° and 3.63°. This supports reporting a
local bending approximation instead of calling it a tear. The simulator does
not preserve permanent crease memory, which must remain disclosed.

The full stapled control still reaches 0.368% local membrane strain at 5.6 ms.
That result remains invalid under the current task monitor. A bounded diagnostic
will establish whether it settles or grows before extraction is attempted.
No final paper-preservation or task-success claim follows from these controls.
