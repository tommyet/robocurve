# Nail clipping: online evidence, not a validated task

The user requested published evidence instead of a new physical check. No physical measurement is claimed here.

Ruchirabha’s [university thesis](https://nagaokaut.repo.nii.ac.jp/record/894/files/k955.pdf), chapter3, tests1mm-thick,2mm-wide polystyrene. Figure3-16 gives a conventional-clipper peak of approximately14N/mm of engaged width, read from the plot:28N at the blade for that sample. Its reported lever spans34.61/7.42mm imply about6N additional handle input, before the clipper’s spring resistance. The conventional48g clipper is not identified by a retail model. The numerical curve in `cutting_force.py` is a coarse plot estimate.

Available replacement material: [Evergreen9015](https://evergreenscalemodels.com/collections/types?q=PLAIN+SHEETS),0.015inch/0.38mm polystyrene sheet. Available ordinary tool: [Green Bell G-1115](https://greenbell.ne.jp/chnsp/products/g-1115/),75mm long,35g. The manufacturer specifies dimensions and materials, but not cutting force. Neither product is the exact tested combination.

A thinner polystyrene practice tip could use the published force profile with an explicitly estimated thickness scaling. Width, thickness, lever geometry and spring resistance must enter the mechanical model; proximity or spring force alone cannot trigger cutting. Such a model would still be an approximation, not the physical force check requested on elapsed PR2346.

Do not submit this folder: no native clipper, demo, baseline, scoring or media has been validated. No code from the earlier team was copied. A successful robot demo alone would not establish that the estimated cutting resistance matches the real retail tool and tip.
