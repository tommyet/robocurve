# Remaining coupled-paper solver

This is a precise implementation plan, not completed functionality or a claim
that the physics fits the $3 trial budget. The native steel coupon must pass
before spending on the complete scene.

1. Represent each A5 sheet by a triangular thin shell with 80 g/m² areal mass,
   in-plane stretch/shear energy and bending energy. Preserve the nominal
   100 µm material thickness. A rigid plate, articulated stiff cards or enlarged
   paper thickness cannot substitute for this model. Use approximately 3 mm
   triangle edges away from the fastener and 0.1–0.25 mm edges around the two
   punctures in each layer; refine contact/tear convergence before judging.
2. Construct the four initial holes from the actual installed wire cross-section
   and clinched geometry. Record their boundaries as immutable judging references.
   Do not provide a large extraction slot, suppress wire/sheet collision after a
   grasp, or create an artificial attachment between paper and staple.
3. Use swept wire-capsule / triangle and remover-edge / triangle contacts with
   each sheet's physical half-thickness. Solve normal non-penetration and
   friction with equal/opposite impulses on tool/wire bodies. The native
   millimetre-scale default contact offset is unsuitable here. A contact-scale
   coupon must show both resistance and withdrawal without tunnelling.
4. Replace the current scalar `PaperBond` coupon with calibrated mixed-mode
   cohesive edges. Opening/shear work weakens bonds irreversibly; completely
   failed edges split mesh topology so a crack can extend and the sheets can
   separate. Cohesive failure is caused by stress/work, never tool proximity or
   a task phase. Preserve total mass and audit released elastic/fracture energy
   when splitting vertices. Calibrate along/across fibre directions separately.
5. Couple steel axial/bending elements with the tested plastic-hinge law. A
   complete clinch must remain geometrically engaged through both sheets until
   each leg actually unbends and passes out. Both paper and wire need self-contact.
   Tool gripper forces must come from the normal YAM fingers and remover contacts.
6. Spawn the stapled flat sheets 0.5 mm above the table, with the wire underside
   0.2 mm clear. Let gravity/contact settle the deformable sheets over the clinch;
   record the actual settled reset and match the setup image. Do not start inside
   the tabletop and rely on a large depenetration impulse to rearrange the staple.
7. Local regression cases must include: remover hovering (no extraction), pull
   on a still-clinched staple (load or damage), selective unclinching (leg clears),
   destructive sideways extraction (tear and score zero), tear closure (no
   healing), and successful withdrawal followed by independent sheet separation.
   Check finer mesh/time step and force/work balance before a robot trial.

The retained native rigid-body adapter does not supply this topology-changing
thin-shell solver. A custom bidirectional shell/contact solver or a verified
supported deformable backend is required. Updating a visible mesh is acceptable
only as rendering of that physical state; an animated mesh with rigid collisions
would not establish paper preservation. No complete solver is implemented yet.
