# Continuous-angle integrity repair (in progress)

The historical stateless95-degree-centred branch can report an inward lower-stop overshoot near−85degrees as+275degrees. Historical wrapped-only logs are not proof of opening.

`angle_tracking.py` tracks all four relative hinge orientations atomically at240Hz, starting from a verified authored-zero reset. It uses unchanged native angular-rate caps, body SO3 increments and a projected-column uniqueness bound. Missing samples, resets, singular projections and bound violations invalidate the history permanently. `angle_step_observer.py` calls an original verified native step once, then reads the completed physics state; it requires exactly12substeps per20Hz action.

The scorer now requires versioned, complete, current continuity evidence. All four flaps must meet150degrees in the same sample; the intactness, flattening and released-hold thresholds are unchanged. Old runners that omit evidence fail closed rather than receiving an opening score.

82local CPU/USD tests pass at this checkpoint. Native binding, installed-source verification, controller consumer integration and a fresh native cadence smoke remain pending. This branch is development only and is not submission-ready. Do not label previous captures as evidence under this new scorer.
