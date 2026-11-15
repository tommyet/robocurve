import json
import unittest
import numpy as np
from native_contact_reader import ContactReadError, native_to_numpy, read_native_contacts, read_sensor_native_contacts


class FakeView:
    def __init__(self):
        self.counts = np.zeros((2, 2), dtype=np.int32)
        self.starts = np.zeros((2, 2), dtype=np.int32)
        self.normal = (np.array([[2.], [3.], [4.], [5.], [np.nan]]),
                       np.array([[1., 0., 0.], [2., 0., 0.], [3., 0., 0.], [4., 0., 0.], [np.nan]*3]),
                       np.array([[0., -1., 0.]]*4 + [[np.nan]*3]),
                       np.array([-.001, -.002, -.003, -.004, np.nan]))
        self.friction = (np.array([[.1, -.2, .3], [.4, -.5, .6], [.7, -.8, .9]]),
                         np.array([[9., 8., 7.], [6., 5., 4.], [3., 2., 1.]]))
        self.dts = []

    def get_contact_data(self, *, dt):
        self.dts.append(('normal', dt))
        self.counts[:] = [[1, 2], [0, 1]]
        self.starts[:] = [[0, 1], [99, 3]]
        return (*self.normal, self.counts, self.starts)

    def get_friction_data(self, *, dt):
        self.dts.append(('friction', dt))
        # Same storage, overwritten before normal slices could be consumed.
        self.counts[:] = [[0, 1], [2, 0]]
        self.starts[:] = [[95, 0], [1, -1]]
        return (*self.friction, self.counts, self.starts)


def read(view, **kwargs):
    return read_native_contacts(view, physics_dt=1/960, body_order=['finger_a', 'finger_b'],
                                filter_order=['can', 'button'], **kwargs)


class NativeContactReaderTests(unittest.TestCase):
    def test_shared_count_start_buffers_are_copied_before_friction_getter(self):
        view = FakeView(); result = read(view); pairs = result['pairs']
        self.assertEqual([pair['normal']['count'] for pair in pairs], [1, 2, 0, 1])
        self.assertEqual([pair['friction']['count'] for pair in pairs], [0, 1, 2, 0])
        self.assertEqual(pairs[1]['normal']['contacts'][1]['native_buffer_index'], 2)
        self.assertEqual(pairs[3]['normal']['contacts'][0]['normal_magnitude_raw'], 5.)
        view.normal[0][:] = -999.; view.counts[:] = -1
        self.assertEqual(pairs[3]['normal']['contacts'][0]['normal_magnitude_raw'], 5.)

    def test_raw_normal_product_and_independent_friction_anchors_preserve_sign(self):
        pair = read(FakeView())['pairs'][1]
        self.assertEqual(pair['normal']['contacts'][0]['normal_magnitude_times_normal_raw'], [0., -3., 0.])
        self.assertEqual(pair['normal']['contacts'][0]['world_point_raw'], [2., 0., 0.])
        self.assertEqual(pair['friction']['contacts'][0]['world_friction_point_raw'], [9., 8., 7.])
        self.assertEqual(pair['friction']['contacts'][0]['world_friction_vector_raw'], [.1, -.2, .3])

    def test_exact_physics_dt_metadata_and_strict_json_roundtrip(self):
        view = FakeView(); result = read(view)
        self.assertEqual(view.dts, [('normal', 1/960), ('friction', 1/960)])
        self.assertEqual(json.loads(json.dumps(result, allow_nan=False)), result)
        self.assertEqual(result['body_order'], ['finger_a', 'finger_b'])
        self.assertEqual(result['pairs'][2]['filter'], 'can')
        self.assertEqual(result['pairs'][2]['normal']['contacts'], [])
        self.assertIn('unused_empty_start_outside_buffer', result['pairs'][2]['normal']['flags'])

    def test_unreferenced_nonfinite_tail_is_not_a_contact_but_valid_nonfinite_fails(self):
        self.assertTrue(read(FakeView())['snapshot_valid'])
        view = FakeView(); view.normal[1][0, 0] = np.nan
        with self.assertRaises(ContactReadError) as ctx: read(view)
        self.assertEqual(ctx.exception.code, 'nonfinite_contact')
        self.assertFalse(ctx.exception.as_dict()['snapshot_valid'])

    def test_shape_bounds_integer_and_missing_buffer_errors_are_explicit(self):
        cases = []
        view = FakeView(); view.normal = (view.normal[0], np.zeros((5, 2)), *view.normal[2:]); cases.append((view, 'buffer_shape'))
        view = FakeView(); view.normal = (view.normal[0][:-1], *view.normal[1:]); cases.append((view, 'buffer_capacity'))
        view = FakeView(); view.normal = (None, *view.normal[1:]); cases.append((view, 'unavailable_buffer'))
        class BadIndex(FakeView):
            def get_contact_data(self, *, dt):
                data = super().get_contact_data(dt=dt); self.starts[0, 0] = 5; return data
        cases.append((BadIndex(), 'slice_bounds'))
        class NegativeCount(FakeView):
            def get_contact_data(self, *, dt):
                data = super().get_contact_data(dt=dt); self.counts[0, 0] = -1; return data
        cases.append((NegativeCount(), 'negative_count'))
        class FloatIndex(FakeView):
            def get_contact_data(self, *, dt):
                data = super().get_contact_data(dt=dt); return (*data[:-2], data[-2].astype(float), data[-1])
        cases.append((FloatIndex(), 'index_dtype'))
        for view, code in cases:
            with self.subTest(code=code):
                with self.assertRaises(ContactReadError) as ctx: read(view)
                self.assertEqual(ctx.exception.code, code)
        with self.assertRaisesRegex(ContactReadError, 'pair_shape'):
            read_native_contacts(FakeView(), physics_dt=1/960, body_order=['one'], filter_order=['can'])

    def test_injected_converter_and_proxy_torch_warp_style_conversion(self):
        class Warp:
            def __init__(self, value): self.value = value
            def numpy(self): return self.value
        class Proxy:
            def __init__(self, value): self.torch = Warp(value)
        self.assertEqual(native_to_numpy(Proxy(np.array([1, 2]))).tolist(), [1, 2])
        calls = []
        def helper(value): calls.append(value); return value
        read(FakeView(), to_numpy=helper)
        self.assertEqual(len(calls), 10)

    def test_empty_real_buffers_remain_empty_and_never_manufacture_zero_points(self):
        class Empty:
            def get_contact_data(self, *, dt): return (np.empty(0), np.empty((0, 3)), np.empty((0, 3)), np.empty(0), np.zeros((1, 1), dtype=int), np.zeros((1, 1), dtype=int))
            def get_friction_data(self, *, dt): return (np.empty((0, 3)), np.empty((0, 3)), np.zeros((1, 1), dtype=int), np.zeros((1, 1), dtype=int))
        result = read_native_contacts(Empty(), physics_dt=1/960, body_order=['finger'], filter_order=['can'])
        self.assertEqual(result['pairs'][0]['normal']['contacts'], [])
        self.assertEqual(result['pairs'][0]['friction']['contacts'], [])
        for dt in (0., -.1, float('nan'), True, np.bool_(True), None, '0.05'):
            with self.assertRaisesRegex(ContactReadError, 'physics_dt'):
                read_native_contacts(Empty(), physics_dt=dt, body_order=['finger'], filter_order=['can'])

    def test_getter_and_metadata_failures_are_invalid_snapshots_not_empty_contacts(self):
        class Failing(FakeView):
            def get_friction_data(self, *, dt): raise RuntimeError('tracking unavailable')
        with self.assertRaisesRegex(ContactReadError, 'getter_failed'): read(Failing())
        with self.assertRaisesRegex(ContactReadError, 'getter_missing'): read(object())
        with self.assertRaisesRegex(ContactReadError, 'ordering_metadata'):
            read_native_contacts(FakeView(), physics_dt=1/960, body_order='finger', filter_order=['can'])


class NativeOrderIntegrationTests(unittest.TestCase):
    def test_native_paths_and_nested_identical_filters_define_exact_pair_order(self):
        from types import SimpleNamespace
        view=FakeView();view.sensor_paths=['/World/finger_b','/World/finger_a'];view.filter_paths=[['/World/button','/World/can']]*2
        view.sensor_count=2;view.filter_count=2
        result=read_sensor_native_contacts(SimpleNamespace(contact_view=view),physics_dt=1/960)
        self.assertEqual(result['body_order'],view.sensor_paths);self.assertEqual(result['filter_order'],view.filter_paths[0])
        self.assertEqual(result['pairs'][1]['body'],'/World/finger_b');self.assertEqual(result['pairs'][1]['filter'],'/World/can')
        self.assertIn('last physics substep',result['sampling_scope']);json.dumps(result,allow_nan=False)
        view.filter_paths=['/World/button','/World/can']
        self.assertEqual(read_sensor_native_contacts(SimpleNamespace(contact_view=view),physics_dt=1/960)['filter_order'],view.filter_paths)

    def test_nonidentical_or_unavailable_native_column_order_is_invalid_not_guessed(self):
        from types import SimpleNamespace
        for paths,count in (([['button','can'],['can','button']],2),([['button','can']],2),(['button'],2)):
            view=FakeView();view.sensor_paths=['a','b'];view.filter_paths=paths;view.sensor_count=2;view.filter_count=count
            with self.assertRaisesRegex(ContactReadError,'ordering_metadata'):
                read_sensor_native_contacts(SimpleNamespace(contact_view=view),physics_dt=1/960)
        with self.assertRaisesRegex(ContactReadError,'ordering_metadata'):
            read_sensor_native_contacts(SimpleNamespace(contact_view=object()),physics_dt=1/960)


if __name__ == '__main__': unittest.main()
