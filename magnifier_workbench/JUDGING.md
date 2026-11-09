# Checking the optical benefit

This is the proposed judging procedure for the prototype. It does not yet
establish submission readiness or a Dream score.

Watch the complete demo first. The robot must pick up the intact magnifier by
its handle and hold it above the fixed printed target. The left wrist camera
must show a useful enlarged view continuously for three seconds. A pose alone
does not earn optical credit.

Use the original 640×360 camera image and the actual 224×224 policy image. A
pixel viewer may enlarge their display, but measurements refer to original
pixels. No crop, digital zoom or changed camera settings can earn credit.

1. Compare the final held image with a lens-free reference taken at the same
   camera and target pose. In simulation, physics is frozen and only the glass
   is hidden after control ends; the handle and frame remain. In a physical
   trial, hold the camera arm still and move the magnifier aside. The four outer
   black marks must change position by no more than one raw-image pixel.
2. Measure all four sides of the square formed by the coloured dot centres in
   both images. Divide each enlarged pixel length by its reference length.
   Check both the native camera image and the policy image. Use the smallest
   ratio, so one stretched edge cannot stand in for useful enlargement.
3. Count the two groups of five bars in the policy image. A readable group has
   exactly five dark bars and four bright gaps across the central half of the
   bar length. Each bar and gap must contain at least one original pixel.
   The supplied black/white swatches define a brightness midpoint; a counted
   dark pixel must be at most 40% of that range above black, and a bright one
   at least 60%. These margins prevent nearly uniform grey noise from counting.
4. At least one group must become readable when it was unreadable without the
   glass. Partial photo credit is 0.5 for at least 1.25× enlargement. Full photo
   credit is 1.0 for at least 1.5× enlargement with both groups readable.
   Otherwise the photo score is 0. Repeat the check throughout the final
   three-second hold; a single final picture cannot prove the duration.

`inspection_measure.py` implements the photo check. `score_hold.py` applies it
to every saved control frame in the final three seconds and verifies the
camera remains stationary. Missing images or an invalid reference cannot earn
credit. These programs report optical evidence separately from physical pickup
and grasp verification; neither should be presented as a complete task score.

Registration detector V2 measures each outer mark against its local background
and rejects insufficient contrast or a shape inconsistent with the printed
square. This handles different illumination at the outer marks and central
swatches. The allowed one-pixel motion, enlargement and five-bar requirements
are unchanged. The final prototype passes all 61 images in its three-second
hold; the original V1 detector failure remains in the evidence history.

The physical audit also checks tool clearance and stability, plus conservative
robot collision geometry reconstructed from measured joints. Full-video review
remains necessary. The current audit samples at 20 Hz and does not establish
clearance between samples or cover every self-collision pair.
