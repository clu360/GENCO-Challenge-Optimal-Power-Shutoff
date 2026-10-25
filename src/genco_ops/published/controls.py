
def _effective_controls(identity, tables, load_ids, gen_ids, requested_delta):
    raw_gen = identity.generators.set_index('canonical_generator_id')
    commanded = tables.gen.set_index('canonical_generator_id')
    for gid, row in raw_gen.iterrows():
        expected = float(row.PG) + float(requested_delta.get(int(gid), 0.0))
        if abs(float(commanded.loc[gid, 'p_mw']) - expected) > 1e-07:
            raise ValueError('OPS generator command differs from raw PG plus allowed redispatch')
    raw_bus = identity.buses.set_index('canonical_bus_index')
    regulated = raw_bus.loc[raw_bus.BUS_TYPE.isin((2, 3))]
    candidate_bus = tables.bus.set_index('bus')
    for index, row in regulated.iterrows():
        if float(candidate_bus.loc[index, 'Vm']) != float(row.VM):
            raise ValueError('raw OPS PV/REF voltage command changed')
        if int(row.BUS_TYPE) == 3 and float(candidate_bus.loc[index, 'Va']) != float(row.VA):
            raise ValueError('raw OPS reference angle changed')
    delta, effective_r = ({}, [])
    for gid in gen_ids:
        row = raw_gen.loc[gid]
        change = float(commanded.loc[gid, 'p_mw']) - float(row.PG)
        headroom = float(row.PMAX - row.PG) if change >= 0 else float(row.PG - row.PMIN)
        if headroom <= 0:
            raise ValueError('selected OPS generator has no directional headroom')
        delta[str(gid)] = change
        effective_r.append(change / headroom)
    return ([float(tables.alpha_effective[i]) for i in load_ids] + effective_r, delta)
