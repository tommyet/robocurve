"""Read-only native contact-buffer snapshots; no resultant/COP/torque estimate.

Caller must enable point/friction tracking before constructing its sensor.
This module has no Isaac/PhysX dependency and does not configure a sensor.
"""
import json
import math
import numbers
import numpy as np


SENSOR_CONSTRUCTION_REQUIREMENTS = {
    'track_contact_points': True,
    'track_friction_forces': True,
    'max_contact_data_count_per_prim': 64,
}


class ContactReadError(ValueError):
    """An unavailable/invalid snapshot, never an invented zero-contact result."""
    def __init__(self, code, detail):
        self.code = code
        self.detail = detail
        super().__init__(f'{code}: {detail}')

    def as_dict(self):
        return {'error': self.code, 'detail': self.detail, 'snapshot_valid': False}


def native_to_numpy(value):
    """Default Warp/ProxyArray/.torch/Torch/NumPy conversion, without mutation.

    Conversion can be injected for another backend. The reader always makes
    its own copy, even when this function or the injected helper returns a view.
    """
    if value is None:
        raise ContactReadError('unavailable_buffer', 'native getter returned None; verify sensor construction flags')
    if hasattr(value, 'torch'):
        value = value.torch
    if hasattr(value, 'detach'):
        value = value.detach()
    if hasattr(value, 'cpu'):
        value = value.cpu()
    if hasattr(value, 'numpy'):
        value = value.numpy()
    return np.asarray(value)


def _copy_buffers(getter, dt, names, convert):
    try:
        raw = getter(dt=dt)
    except Exception as error:
        raise ContactReadError('getter_failed', f'{getattr(getter, "__name__", type(getter).__name__)}: {error}') from error
    if not isinstance(raw, (tuple, list)) or len(raw) != len(names):
        raise ContactReadError('getter_contract', f'expected {len(names)} buffers: {names}')
    result = {}
    for name, value in zip(names, raw):
        if value is None:
            raise ContactReadError('unavailable_buffer', f'{name} is None; verify sensor construction flags')
        try:
            result[name] = np.array(convert(value), copy=True)
        except ContactReadError:
            raise
        except Exception as error:
            raise ContactReadError('buffer_conversion', f'{name}: {error}') from error
    return result


def _numeric_shape(array, name, vector=False):
    if array.dtype.kind not in 'fiu':
        raise ContactReadError('buffer_dtype', f'{name} must contain real numeric values, got {array.dtype}')
    if vector:
        if array.ndim != 2 or array.shape[1] != 3:
            raise ContactReadError('buffer_shape', f'{name} must have shape (capacity, 3), got {array.shape}')
        return array
    if array.ndim == 2 and array.shape[1] == 1:
        return array[:, 0]
    if array.ndim != 1:
        raise ContactReadError('buffer_shape', f'{name} must have shape (capacity,) or (capacity, 1), got {array.shape}')
    return array


def _indices(data, pair_shape, capacity, label):
    counts, starts = data['counts'], data['starts']
    if counts.shape != pair_shape or starts.shape != pair_shape:
        raise ContactReadError('pair_shape', f'{label} counts/starts must match caller body/filter shape {pair_shape}, got {counts.shape}/{starts.shape}')
    if counts.dtype.kind not in 'iu' or starts.dtype.kind not in 'iu':
        raise ContactReadError('index_dtype', f'{label} counts/starts must be integer arrays')
    if np.any(counts < 0):
        raise ContactReadError('negative_count', f'{label} contains a negative contact count')
    for index in np.ndindex(pair_shape):
        count, start = int(counts[index]), int(starts[index])
        if count and (start < 0 or start > capacity or count > capacity - start):
            raise ContactReadError('slice_bounds', f'{label}{index} start={start}, count={count}, capacity={capacity}')


def _number(value, label):
    value = float(value)
    if not math.isfinite(value):
        raise ContactReadError('nonfinite_contact', f'{label} is nonfinite')
    return value


def _vector(value, label):
    return [_number(v, label) for v in value]


def _pair(data, index, label):
    count, start = int(data['counts'][index]), int(data['starts'][index])
    capacity = len(data['points'])
    flags = []
    if not count and not 0 <= start <= capacity:
        # Empty pairs have no valid slice; native unused starts may be sentinels.
        flags.append('unused_empty_start_outside_buffer')
    contacts = []
    for k in range(start, start + count) if count else ():
        if label == 'normal':
            magnitude = _number(data['magnitudes'][k], f'normal{index}[{k}].magnitude')
            normal = _vector(data['normals'][k], f'normal{index}[{k}].normal')
            contacts.append({
                'native_buffer_index': k,
                'normal_magnitude_raw': magnitude,
                'world_point_raw': _vector(data['points'][k], f'normal{index}[{k}].point'),
                'world_normal_raw': normal,
                'normal_magnitude_times_normal_raw': [_number(magnitude * v, f'normal{index}[{k}].product') for v in normal],
                'separation_raw': _number(data['separations'][k], f'normal{index}[{k}].separation'),
            })
        else:
            contacts.append({
                'native_buffer_index': k,
                'world_friction_vector_raw': _vector(data['vectors'][k], f'friction{index}[{k}].vector'),
                'world_friction_point_raw': _vector(data['points'][k], f'friction{index}[{k}].point'),
            })
    return {'count': count, 'buffer_start_raw': start, 'start_index_used': bool(count), 'contacts': contacts, 'flags': flags}


def read_native_contacts(contact_view, *, physics_dt, body_order, filter_order, to_numpy=native_to_numpy):
    """Copy one raw contact snapshot using the caller's *physics* timestep.

    Required getter contract:
      get_contact_data(dt) -> magnitudes, points, normals, separations, counts, starts
      get_friction_data(dt) -> vectors, points, counts, starts
    Counts/starts shape must be (len(body_order), len(filter_order)). Metadata
    must describe the native view's actual row/column ordering (flattened across
    environments if needed); no ordering is inferred from expressions/names.

    Normal and friction anchors remain independent. No sign flips, sums,
    centre-of-pressure estimate, torque, or native proof is produced here.
    """
    if isinstance(physics_dt, (bool, np.bool_)) or not isinstance(physics_dt, numbers.Real) or not math.isfinite(physics_dt) or physics_dt <= 0:
        raise ContactReadError('physics_dt', 'provide the exact positive native physics timestep, not control dt')
    if isinstance(body_order, (str, bytes)) or isinstance(filter_order, (str, bytes)):
        raise ContactReadError('ordering_metadata', 'body/filter ordering must be sequences of names, not one string')
    try:
        bodies, filters = list(body_order), list(filter_order)
    except TypeError as error:
        raise ContactReadError('ordering_metadata', 'body/filter ordering must be sequences of names') from error
    if not all(isinstance(value, str) for value in [*bodies, *filters]):
        raise ContactReadError('ordering_metadata', 'body/filter ordering entries must be strings')
    if not all(callable(getattr(contact_view, name, None)) for name in ('get_contact_data', 'get_friction_data')):
        raise ContactReadError('getter_missing', 'contact view must expose both raw native getters')
    # CRITICAL: friction getter reuses counts/starts storage. Finish copying
    # ALL normal arrays and indices before invoking that getter.
    normal = _copy_buffers(contact_view.get_contact_data, physics_dt,
                           ('magnitudes', 'points', 'normals', 'separations', 'counts', 'starts'), to_numpy)
    friction = _copy_buffers(contact_view.get_friction_data, physics_dt,
                             ('vectors', 'points', 'counts', 'starts'), to_numpy)
    for name in ('magnitudes', 'separations'):
        normal[name] = _numeric_shape(normal[name], f'normal.{name}')
    for data, names, label in ((normal, ('points', 'normals'), 'normal'), (friction, ('vectors', 'points'), 'friction')):
        for name in names:
            data[name] = _numeric_shape(data[name], f'{label}.{name}', vector=True)
        lengths = {len(value) for name, value in data.items() if name not in ('counts', 'starts')}
        if len(lengths) != 1:
            raise ContactReadError('buffer_capacity', f'{label} value-buffer capacities differ')
        _indices(data, (len(bodies), len(filters)), len(data['points']), label)
    pairs = []
    for i, body in enumerate(bodies):
        for j, contact_filter in enumerate(filters):
            pairs.append({'body_index': i, 'body': body, 'filter_index': j, 'filter': contact_filter,
                          'normal': _pair(normal, (i, j), 'normal'), 'friction': _pair(friction, (i, j), 'friction')})
    result = {'snapshot_valid': True, 'physics_dt_s': float(physics_dt), 'body_order': bodies, 'filter_order': filters,
              'pairs': pairs, 'required_sensor_construction_flags': dict(SENSOR_CONSTRUCTION_REQUIREMENTS),
              'interpretation': 'Raw native values and independent anchors; no sign convention conversion, COP or torque claim',
              'native_validation': 'not established by fake-view CPU tests'}
    # Fail closed if an unsupported value ever escapes conversion.
    try:
        json.dumps(result, allow_nan=False)
    except (ValueError, TypeError) as error:
        raise ContactReadError('strict_json', str(error)) from error
    return result


def read_sensor_native_contacts(sensor,*,physics_dt):
    """Use the view's native row/column paths, never guessed config ordering."""
    try:
        view=sensor.contact_view
        bodies=list(view.sensor_paths);raw_filters=list(view.filter_paths)
        if raw_filters and not isinstance(raw_filters[0],str):
            rows=[list(row) for row in raw_filters]
            if len(rows)!=len(bodies) or any(row!=rows[0] for row in rows):
                raise ContactReadError('ordering_metadata','native per-body filter paths differ or have the wrong row count')
            filters=rows[0]
        else:filters=raw_filters
        if len(bodies)!=view.sensor_count or len(filters)!=view.filter_count:
            raise ContactReadError('ordering_metadata','native path lengths do not match native sensor/filter counts')
    except ContactReadError:raise
    except Exception as error:raise ContactReadError('ordering_metadata',str(error)) from error
    result=read_native_contacts(view,physics_dt=physics_dt,body_order=bodies,filter_order=filters)
    result['ordering_source']='RigidContactView.sensor_paths/filter_paths; repeated per-body filter paths checked equal'
    result['sampling_scope']='one last physics substep sampled at control ticks; not a control-period average'
    return result
