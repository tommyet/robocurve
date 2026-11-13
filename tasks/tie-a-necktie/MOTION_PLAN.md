# Adult necktie development

This controller is unfinished. No complete knot, wearable fit or released
retention has been demonstrated.

The scene starts with an untied1.45m necktie draped inside-out around a folded
collar form. The target is a simple (Oriental) knot. A scripted demo may read
native cloth geometry to choose ordinary joint and finger actions. Dream gets
its normal camera and joint observations. No controller may reposition cloth,
attach it, change its rest shape or apply hidden forces.

Native155 and160 establish the pickup, tip handoff and right-hand regrasp of
the wide strand. Native160 then approaches the narrow strand, but pushes it
aside and closes beside it. Sampled self, robot and fixture checks are clear;
that does not establish grasp success. A fully open approach passes local
screens and awaits a short native comparison.

Remaining work:

1. Retain the narrow strand with the left hand and prove retention during a
   small ordinary carry. Verify the wide strand remains held.
2. Pass the wide end under the narrow end and back across its front, retaining
   a loose front opening through physical finger contact.
3. Feed the wide tip upward through the neck loop and downward through the
   front opening. Use a physical handoff if necessary.
4. Pull through, dress the knot and slide it toward the collar while holding
   the narrow end. Leave the wide face outward and the narrow tip hidden.
5. Release both hands for five seconds. Check knot structure, collar fit,
   centering, both tip positions and material/contact integrity before scoring.

The proposed400–440mm wide-tip drop is provisional until a complete knot
exists. Earlier child-tie experiments are retained in VALIDATION.json and are
not evidence for this adult task. Dream runs follow a valid full demonstration.

`probe_checkpoint.py` is only a short contact diagnostic. It reconstructs a
recorded native state once, then uses normal robot actions. Missing solver warm
starts and estimated joint velocity can change the continuation. Its output
cannot be presented as a task episode or joined to a submission video.
