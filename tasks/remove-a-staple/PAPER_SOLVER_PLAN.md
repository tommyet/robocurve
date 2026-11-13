# Paper validity boundary and remaining work

The current native probe uses 100 µm surface-FEM paper, explicit puncture holes,
and a contact-capable steel staple with plastic bending joints. Its two small
sheets are supported only by the staple; a fixed crown is an explicit coupon
fixture, not part of the proposed robot task. The full A5 scene and remover
controller remain unfinished.

A complete post-fracture animation is not necessary to reject damaged outcomes.
The chosen development route instead ends a trial irreversibly when measured
triangle stretch or outer-surface bending strain leaves the paper model's
elastic range. No later flat pose can restore validity or earn partial credit.
This is a validity boundary, not a claim to predict a crack's exact length.
The proposed 0.3% limits are conservative numerical choices and still require
comparison with the selected paper and a non-damaging extraction trial.

Published copy-paper tests find directional elastic and plastic behaviour;
matching nominal grammage alone is not full calibration. Useful references are
[Yoshihara and Yoshinobu's tensile tests](https://doi.org/10.1007/s10086-014-1398-y)
and [their practical test method](https://doi.org/10.2472/jsms.64.350).
The native isotropic elasticity and planar wire-hinge coupon are approximations;
neither is presented as a measured commercial product.

The next checks, in order, are:

1. Compare the native plastic-wire coupon with a jaw passing beside it, then
   halve the time step. Contact must produce permanent bending; hovering must
   not. The coupon has no paper and cannot demonstrate extraction.
2. Compare free and stapled paper coupons. The free pair must fall; the fixed
   crown and clinched legs must retain the stapled pair by contact alone while
   both sheets remain inside the elastic validity boundary. Inspect the actual
   hole/wire contacts and check a finer time step and mesh before interpreting
   a positive result.
3. Add a release diagnostic that straightens and withdraws the wire through the
   existing holes by tool contact. Pulling a still-clinched leg destructively
   must reach the irreversible invalid state, not pass through intact paper.
4. Assemble the A5 sheets, free staple and passive remover in the ordinary YAM
   station. Fix the starting geometry and allow contact settling before control.
   There must be no paper pins, automatic attachments or collision disabling.
5. Make a successful ordinary joint-command demo, then a Dream trial with the
   same physics. Score both from the saved images/state and independently review
   all sheet surfaces. A guard failure overrides every partial or full score.

The native backend has a fixed mesh topology. A trial that leaves its valid
material range stops; the software does not pretend to render physical tearing
beyond that point. This limitation must be explicit in the eventual submission.
