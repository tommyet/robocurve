"""Four fixed task configurations; distances are metres."""

VARIANTS = {
    "join-two-2x2-blocks": dict(title="Join two 2×2 blocks", lower_shape=(2, 2), upper_shape=(2, 2), required_studs=4, target_offset=(0., 0.)),
    "join-two-1x1-blocks": dict(title="Join two 1×1 blocks", lower_shape=(1, 1), upper_shape=(1, 1), required_studs=1, target_offset=(0., 0.)),
    "join-1x1-to-2x2": dict(title="Join a 1×1 block to a 2×2 block", lower_shape=(2, 2), upper_shape=(1, 1), required_studs=1, target_offset=(.008, .008)),
    "join-two-2x2-blocks-offset": dict(title="Join two 2×2 blocks with two studs overlapping", lower_shape=(2, 2), upper_shape=(2, 2), required_studs=2, target_offset=(.016, 0.)),
}

def config(name):
    c = dict(VARIANTS[name], name=name, table_top=.7475, pitch=.016,
             body_height=.0192, stud_height=.0048, lower_xy=(.26, .10),
             upper_xy=(.20, .20), lower_color=(.16, .40, .90), upper_color=(.94, .27, .15))
    for role in ("lower", "upper"):
        # Rounded solid-PLA estimates from Boolean-unioned printable CAD at
        # 1.24 g/cm³; actual prints must be weighed for physical calibration.
        c[role + "_mass"] = .003907 if c[role + "_shape"] == (1, 1) else .012110
    count = c['required_studs']
    match = "all four studs" if count == 4 else "exactly two neighbouring studs" if count == 2 else "one stud"
    c['instruction'] = (
        f"Press the red block onto the blue block, connecting {match}. "
        "Lift the pair by the red block alone so the blue block is at least 2 cm above the table for one second. "
        "Set the joined pair down upright and let go for one second."
    )
    if name == 'join-1x1-to-2x2':
        c['instruction'] += " Any of the blue block's four studs is allowed."
    if name.endswith('offset'):
        c['instruction'] += " Either row or column is allowed; leave the other two blue studs exposed."
    return c
