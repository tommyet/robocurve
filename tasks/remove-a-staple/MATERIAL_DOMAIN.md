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

## Later contact findings and the flexible-facet candidate

Controls 049–055 supersede the initial settling inference above. Finer stepping,
heavier paper and a wider predictive steel contact margin did not validate the
coupled FEM scene. In 051 and 055, steel crosses an intact triangle while membrane
strain remains below 0.6%. Increasing a strain allowance would not repair that
contact failure. The 0.3% and 1% stops are model/diagnostic limits, not observations
of tears.

The separate flexible-facet candidate uses 100µm triangular paper prisms with
native bending hinges. Its bending rigidity is `E h³ / (12(1−ν²))`, using the
same 2 GPa isotropic modulus. Hinges have finite native break force proportional
to shared-edge length. No entire sheet is rigid or attached to the world.

For a conservative strength envelope, one published laboratory characterization
of 78.7 gsm, 102 µm copy paper reports tensile indices 57.43 kNm/kg in the machine
direction and 19.31 kNm/kg across it, with rupture strains 1.51% and 3.60% respectively.
The weaker index gives about 1520 N per metre of width; the candidate uses 1500 N/m
in every direction. This is a declared engineering approximation to a specific
paper grade, not a calibration of crack growth around the staple punctures.
[Laboratory copy-paper characterization](https://crimsonpublishers.com/acsr/fulltext/ACSR.000566.php)

The approximation has limits: each triangle is internally inextensible, bending
is reversible, and native joint breaking can separate facets only along mesh
edges. A separate 25 µm endpoint-gap guard prevents averaging separated facets
back into an apparently intact sheet. Original puncture geometry and all steel
contacts remain active. Full-size bending, deliberate damage controls and
complete staple extraction must be verified before this candidate can become
the task model. The first coupon 058 failed on its first step even without a
staple; its authored dimensions alone are not evidence of valid dynamics.
