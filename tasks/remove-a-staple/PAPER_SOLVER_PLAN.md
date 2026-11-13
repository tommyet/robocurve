# Paper validity boundary and remaining work

The current native probe uses 100 µm surface-FEM paper, explicit puncture holes,
and a contact-capable steel staple with plastic bending joints. Its two small
sheets are supported only by the staple; a fixed crown is an explicit coupon
fixture, not part of the proposed robot task. The full A5 scene is authored; its native contact gate and remover controller
remain unfinished.

A complete post-fracture animation is not necessary to reject damaged outcomes.
The chosen development route instead ends a trial irreversibly when measured
triangle stretch leaves the declared membrane range, geometry degenerates or
wire crosses an intact triangle. Curvature alone is now a recorded approximation
warning, since a crease is allowed by the task. No later flat pose can restore validity or earn partial credit.
This is a validity boundary, not a claim to predict a crack's exact length.
The proposed0.3% membrane limit is an elastic-domain approximation consistent with
the approximate onset of nonlinearity in published copy-paper tensile curves;
they are not a tear threshold. See [material interpretation](MATERIAL_DOMAIN.md).
A non-damaging extraction trial remains necessary.
A commercial-paper calibration is not claimed.

Published copy-paper tests find directional elastic and plastic behaviour;
matching nominal grammage alone is not full calibration. Useful references are
[Yoshihara and Yoshinobu's tensile tests](https://doi.org/10.1007/s10086-014-1398-y)
and [their practical test method](https://doi.org/10.2472/jsms.64.350).
The native isotropic elasticity and planar wire-hinge coupon are approximations;
neither is presented as a measured commercial product.

The diagnostic sequence is:

1. Completed: native plastic-wire contact, no-contact and half-step controls.
   The coupon has no paper and cannot demonstrate extraction.
2. Free-pair controls pass with a small initial clearance. The unsupported
   stapled coupon crosses the provisional bending-domain boundary. The fixed
   crown and clinched legs must retain the stapled pair by contact alone while
   both sheets remain inside the membrane/contact validity boundary. Inspect the actual
   hole/wire contacts and check a finer time step and mesh before interpreting
   a positive result.
3. Add a release diagnostic that straightens and withdraws the wire through the
   existing holes by tool contact. Pulling a still-clinched leg destructively
   must reach the irreversible invalid state, not pass through intact paper.
4. The A5 scene runs on its actual support but has not passed its validity gate.
   A local puncture mesh removes the original long, thin triangles; the same
   0.5 ms step still reaches 0.429% membrane strain by 0.011 seconds near a leg.
   At0.1ms the full scene fails sooner, after0.002s. Removing the staple
   isolates a second issue: the pair stays nearly flat until it lands on the
   support, then its upper sheet wrinkles locally. Compare native contact
   refinement before interpreting either trace as physical paper damage.
   A supported-edge reset is a separate candidate: lower sheet on the board,
   clinched legs beyond its edge, with no pins or hidden collision filtering.
   Then integrate the free staple and passive remover with ordinary YAM. Allow native
   contact settling before control.
   There must be no paper pins, automatic attachments or collision disabling.
5. Make a successful ordinary joint-command demo, then a Dream trial with the
   same physics. Score both from the saved images/state and independently review
   all sheet surfaces. A guard failure overrides every partial or full score.

The native backend has a fixed mesh topology. A trial that leaves its valid
material range stops; the software does not pretend to render physical tearing
beyond that point. This limitation must be explicit in the eventual submission.
