# Paper model and the meaning of its limits

The paper is a flexible 100 µm surface mesh with explicit staple punctures.
Native FEM computes its motion and contact. It is an isotropic elastic
approximation; it does not render fibre fracture or permanent creases.

The current 0.3% membrane and outer-fibre bending limits are **model-validity
checks, not tear detectors**. A breach invalidates the diagnostic. It does not
mean that real paper would have torn. In particular, an ordinary crease can
remain intact. At 100 µm thickness, the bending limit corresponds to a radius
of about 17 mm, which is much gentler than many harmless paper folds.

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
A successful native trial must stay within its declared material approximation,
keep contact topology intact and release the sheets through the original
punctures. Neither a low final strain nor a visually flat final frame repairs
an earlier invalid trial. The final submission must disclose the absence of
post-fracture rendering.

The present contact probes are not converged: merely reducing the time step
made the full stapled scene fail sooner, and an unstapled pair also develops a
local contact wrinkle when dropped onto the support. Raising a limit until
that trace passes would not establish valid physics. Native contact refinement
and a supported physical reset are being compared first. If realistic removal
needs permanent bending, the approximation or its stated scope must change;
calling the bend a tear would not resolve the mismatch.
