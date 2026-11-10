"""Independent trajectory, boundary, preservation and result-consistency tests."""
import csv
import json
from pathlib import Path
import unittest
import numpy as np
from astropy.io import fits
from astropy.time import Time

from audit_core import (ROOT, Sampler, VARIANTS, existing, rotation_rate, sample_longitudes,
                        select_sources, score, area_weights, original_source_run,
                        original_grid_vectorized, run_variant)
from synthetic import mock_header, make_case
from inventory import sha256

OUT=Path(__file__).resolve().parent


class PhysicsTests(unittest.TestCase):
    def test_latitude_colatitude_equivalence(self):
        lat=np.array([-90,-60,-30,0,30,60,90.])
        theta=np.deg2rad(90-lat)
        expected=.18-2.3*np.cos(theta)**2-1.62*np.cos(theta)**4
        np.testing.assert_allclose(rotation_rate(lat,True),expected,atol=1e-14)

    def test_tabulated_rates(self):
        np.testing.assert_allclose(rotation_rate(np.array([0,30,60,90,-90]),False),
                                   [-3.74,-2.45625,-.49625,.18,.18],atol=1e-13)
        np.testing.assert_allclose(rotation_rate(np.array([0,30,60,90,-90]),True),
                                   [.18,-.49625,-2.45625,-3.74,-3.74],atol=1e-13)

    def test_known_feature_trajectory_positive_and_negative_rates(self):
        # At t0 feature is at phi. It is observed when its trajectory intersects
        # L_CM(t)=180-13.2*t. Solve intersection in time independently.
        for phi in (0.,1.,170.,180.,250.,359.,360.):
            for w in (-3.74,-.5,0.,.18,2.):
                t=(180-phi)/(13.2+w)
                feature_at_observation=phi+w*t
                sample=sample_longitudes([phi],[w],True,True).item()
                self.assertAlmostEqual(sample,feature_at_observation,places=11)
                self.assertAlmostEqual(sample,180-13.2*t,places=11)

    def test_first_order_error_is_second_order(self):
        # Analytic error = -(phi-180)*a^2/(1+a), with a=w/13.2.
        phi=np.array([1.,80.,180.,280.,359.])
        rate=np.array([-.5,.18])
        a=rate[:,None]/13.2
        approximate=sample_longitudes(phi,rate,True)
        exact=sample_longitudes(phi,rate,True,True)
        np.testing.assert_allclose(approximate-exact,-(phi[None,:]-180)*a*a/(1+a),atol=1e-13)

    def test_time_tagged_seam_selects_chronological_neighbor(self):
        h=mock_header(ny=9,nx=720)
        lon,lat=existing.calculate_coordinates(np.empty((9,720)),h)
        times=[np.tile((180-lon)/13.2+k*360/13.2,(9,1)) for k in (-1,0,1)]
        shifted=np.tile([-.25,.25,359.75,360.25],(9,1))
        src,wrap=select_sources(shifted,True)
        sampled=Sampler(times,[h]*3).sample(lat,src,wrap)
        np.testing.assert_allclose(sampled,(180-shifted)/13.2,atol=1e-11)
        wrongsrc,wrap=select_sources(shifted,False)
        wrong=Sampler(times,[h]*3).sample(lat,wrongsrc,wrap)
        np.testing.assert_allclose(abs(wrong[:,[0,3]]-sampled[:,[0,3]]),2*360/13.2,atol=1e-11)

    def test_boundaries_are_current_and_no_unsupported_extrapolation(self):
        for reverse in (False,True):
            src,wrapped=select_sources(np.array([[0.,360.]]),reverse)
            np.testing.assert_array_equal(src,1)
            np.testing.assert_array_equal(wrapped,[[0,360]])
        with self.assertRaises(ValueError):
            select_sources(np.array([[1081.]]),True)

    def test_stationary_oracle_has_no_shift(self):
        phi=np.arange(0,361,10.)
        np.testing.assert_allclose(sample_longitudes(phi,[0.],True,True),phi[None,:])

    def test_north_south_symmetry(self):
        for fixed in (False,True):
            np.testing.assert_allclose(rotation_rate(np.arange(0,91.),fixed),rotation_rate(-np.arange(0,91.),fixed))

    def test_degenerate_inverse_fails(self):
        with self.assertRaises(ValueError):
            sample_longitudes([0,180],[-13.2],True,True)


class NumericalTests(unittest.TestCase):
    def test_literal_original_matches_independent_vectorization_on_finite_arrays(self):
        rng=np.random.default_rng(20261109)
        maps=[rng.normal(size=(21,41)) for _ in range(3)]
        np.testing.assert_allclose(original_source_run(maps),original_grid_vectorized(maps),atol=1e-12,rtol=1e-12)

    def test_primary_sampler_reproduces_existing_at_native_grid(self):
        h=mock_header(31,72)
        lon,lat=existing.calculate_coordinates(np.empty((31,72)),h)
        data=np.sin(np.deg2rad(lon))[None,:]*np.cos(np.deg2rad(lat))[:,None]
        src=np.ones(data.shape,int); coords=np.broadcast_to(lon,data.shape)
        result=Sampler([data]*3,[h]*3).sample(lat,src,coords)
        np.testing.assert_allclose(result,data,atol=1e-12)

    def test_missing_edge_and_isolated_pixels_are_not_zero_measurements(self):
        h=mock_header(21,72)
        lon,lat=existing.calculate_coordinates(np.empty((21,72)),h)
        data=np.ones((21,72))*7
        data[0]=np.nan; data[-1]=np.nan; data[7,12]=np.nan
        src=np.ones(data.shape,int); coords=np.broadcast_to(lon,data.shape)
        result=Sampler([data]*3,[h]*3).sample(lat,src,coords)
        self.assertTrue(np.isnan(result[[0,-1]]).all())
        # Existing row omission bridges an interior gap with spline interpolation.
        np.testing.assert_allclose(result[1:-1],7,atol=1e-12)
        self.assertFalse(np.any(result==0))

    def test_no_longitude_edge_extrapolation(self):
        h=mock_header(9,72)
        _,lat=existing.calculate_coordinates(np.empty((9,72)),h)
        q=np.tile([0,360],(9,1)); src=np.ones(q.shape,int)
        self.assertTrue(np.isnan(Sampler([np.ones((9,72))]*3,[h]*3).sample(lat,src,q)).all())

    def test_area_weights_cover_sphere_and_polar_cells(self):
        h=mock_header(181,720)
        self.assertAlmostEqual(area_weights(h).sum(),1.,places=12)
        self.assertTrue((area_weights(h)>0).all())

    def test_metric_units_and_bias_direction(self):
        a=np.array([1.,3.,5.]); b=np.array([0.,1.,2.]); mask=np.ones(3,bool)
        m=score(a,b,mask)
        self.assertEqual(m['bias_G'],2)
        self.assertEqual(m['mae_G'],2)
        self.assertAlmostEqual(m['rmse_G'],np.sqrt(14/3))
        self.assertAlmostEqual(m['pearson_r'],1)
        with self.assertRaises(ValueError):
            score(np.array([np.nan,1,2]),b,mask)


class CompletedAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (OUT/'metrics.csv').exists():
            raise unittest.SkipTest('Run run_audit.py before checking persisted results.')

    def test_persisted_scores_and_identical_masks(self):
        rows=list(csv.DictReader((OUT/'metrics.csv').read_text(encoding='utf-8').splitlines()))
        self.assertEqual(len(rows),27)
        for cr in (2120,2122,2124):
            a=np.load(OUT/'arrays'/f'cr{cr}.npz')
            mask=a['mask']; obs=a['reference']
            common=np.isfinite(obs)&(a['mu']>=.8)
            for v in ('central',)+VARIANTS:
                common &= np.isfinite(a['field_'+v])
            np.testing.assert_array_equal(mask,common)
            for r in (r for r in rows if int(r['central_cr'])==cr):
                m=score(a['field_'+r['variant']],obs,mask)
                self.assertEqual(m['count'],int(r['count']))
                self.assertAlmostEqual(m['rmse_G'],float(r['rmse_G']),places=11)

    def test_observations_do_not_sample_seams(self):
        for cr in (2120,2122,2124):
            a=np.load(OUT/'arrays'/f'cr{cr}.npz')
            for v in VARIANTS:
                np.testing.assert_array_equal(a['source_'+v][a['mask']],1)
            for v in ('000','100','010','110'):
                toggled=v[:2]+('1' if v[2]=='0' else '0')
                np.testing.assert_array_equal(a['field_'+v][a['mask']],a['field_'+toggled][a['mask']])

    def test_projection_registration_and_baseline_reproduction(self):
        for cr in (2120,2122,2124):
            ev=json.loads((OUT/'evidence'/f'cr{cr}.json').read_text())
            check=ev['observation']['independent_projection']
            self.assertLess(check['max_abs_Br_difference_G'],1e-4)
            self.assertLess(check['max_abs_mu_difference'],1e-12)
            self.assertTrue(check['same_finite_mask'])
            self.assertTrue(ev['primary_mask_same_as_prior'])
            for c in ev['baseline_reproduction'].values():
                self.assertLess(c['cached_map_max_abs_difference_G'],1e-9)
                self.assertLess(c['existing_pipeline_max_abs_difference_G'],1e-9)

    def test_actual_chronology_is_decreasing_longitude_in_increasing_time(self):
        for cr in (2120,2122,2124):
            e=json.loads((OUT/'evidence'/f'cr{cr}.json').read_text())
            ts=[Time(t['utc']).jd for t in e['chronology_within_rotation']]
            self.assertTrue(np.all(np.diff(ts)>0))
            self.assertTrue(np.all(np.diff(e['L0_deg_at_midrotation_minus_0_01d_0_plus_0_01d'])<0))
            ts=[Time(t['midrotation_utc']).jd for t in e['chronology_midrotations']]
            self.assertTrue(np.all(np.diff(ts)>0))

    def test_all_original_files_unchanged(self):
        manifest=json.loads((OUT/'original_manifest.json').read_text())
        for r in manifest:
            self.assertEqual(sha256(ROOT/r['path']),r['sha256'],r['path'])

    def test_literal_HMI_reference_has_no_finite_results(self):
        for cr in (2120,2122,2124):
            a=np.load(OUT/'arrays'/f'cr{cr}.npz')
            self.assertEqual(np.isfinite(a['literal_original']).sum(),0)

    def test_synthetic_accuracy_and_controls(self):
        rows=list(csv.DictReader((OUT/'synthetic_metrics.csv').read_text().splitlines()))
        rmse={(r['case'],r['variant']):float(r['rmse_G']) for r in rows}
        for case in ('smooth_rotation','seam_features','missing_data'):
            self.assertLess(rmse[case,'111_exact'],1e-4)
            self.assertLess(rmse[case,'111'],rmse[case,'central'])
        self.assertEqual(rmse['stationary_control','central'],0)
        self.assertGreater(rmse['stationary_control','111_exact'],1)
        self.assertLess(rmse['opposite_rotation_control','known_rate_exact'],1e-4)
        self.assertLess(rmse['opposite_rotation_control','100'],rmse['opposite_rotation_control','111'])
        self.assertGreater(rmse['evolving_control','known_rate_exact'],1)

    def test_raw_fits_checksum_avoids_header_normalization_artifact(self):
        records=json.loads((OUT/'evidence'/'raw_fits_checksums.json').read_text())
        self.assertEqual(len(records),221)
        self.assertTrue(all(r['raw_checksum_valid'] for r in records))

    def test_resolution_and_registration_diagnostics_use_common_masks(self):
        if not (OUT/'smoothing_sensitivity.csv').exists():
            self.skipTest('Run discrepancy diagnostics first.')
        smooth=list(csv.DictReader((OUT/'smoothing_sensitivity.csv').read_text().splitlines()))
        offsets=list(csv.DictReader((OUT/'registration_offset_sensitivity.csv').read_text().splitlines()))
        primary=list(csv.DictReader((OUT/'metrics.csv').read_text().splitlines()))
        for cr in (2120,2122,2124):
            selected=[r for r in smooth if int(r['central_cr'])==cr]
            self.assertEqual(len(selected),27)
            self.assertEqual(len({r['count'] for r in selected}),1)
            zero=next(r for r in offsets if int(r['central_cr'])==cr
                      and float(r['source_query_longitude_offset_deg'])==0
                      and float(r['source_query_latitude_offset_deg'])==0)
            base=next(r for r in primary if int(r['central_cr'])==cr and r['variant']=='central')
            self.assertAlmostEqual(float(zero['rmse_G']),float(base['rmse_G']),places=9)


if __name__=='__main__':
    unittest.main(verbosity=2)
