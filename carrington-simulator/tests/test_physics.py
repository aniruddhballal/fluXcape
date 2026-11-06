import numpy as np
import pytest

from solar_sim.physics import (
    CARRINGTON_RATE, LATITUDES, LONGITUDES, SYNODIC_PERIOD, accumulated_map,
    area_weighted_rmse, displacement, field_at, instantaneous_map, observation_time,
    periodic_remap, reconstruct, rotation_rate, synoptic_map, wrap_longitude,
)


@pytest.mark.parametrize("longitude, expected", [(0, 0), (1, -0.07575), (90, -6.8175),
                                                  (180, -13.635), (270, -20.4525), (359, -27.19425)])
def test_observation_times(longitude, expected):
    assert observation_time(longitude) == pytest.approx(expected)


def test_time_boundary_is_not_spatial_wrapping():
    assert observation_time(360) == pytest.approx(-SYNODIC_PERIOD)
    assert observation_time(0) == 0
    np.testing.assert_array_equal(wrap_longitude([-1, 0, 359, 360, 721]), [359, 0, 359, 0, 1])


def test_rigid_rotation_has_zero_carrington_drift():
    np.testing.assert_array_equal(rotation_rate(LATITUDES), np.full(LATITUDES.shape, CARRINGTON_RATE))
    np.testing.assert_array_equal(displacement(LATITUDES, 27.27), np.zeros_like(LATITUDES))
    np.testing.assert_array_equal(instantaneous_map(-27), instantaneous_map(0))


def test_documented_howard_rate_and_direction():
    # Independent reference: SunPy documents 27.36432679 deg over 2 days at 30°.
    assert rotation_rate(30, True) * 2 == pytest.approx(27.36432679, abs=1e-8)
    shifts = displacement(np.array([0, 30, 60]), 20, True)
    assert shifts[0] > 0 > shifts[1] > shifts[2]
    np.testing.assert_allclose(rotation_rate(LATITUDES, True), rotation_rate(-LATITUDES, True))


@pytest.mark.parametrize("differential", [False, True])
def test_synoptic_columns_sample_actual_time(differential):
    sampled = synoptic_map(differential)
    for column in [0, 1, 90, 180, 270, 359]:
        instant = instantaneous_map(observation_time(column), differential)
        np.testing.assert_array_equal(sampled[:, column], instant[:, column])


def test_chronological_accumulation():
    sampled = synoptic_map(True)
    assert np.isnan(accumulated_map(sampled, -SYNODIC_PERIOD)).all()
    first = accumulated_map(sampled, observation_time(359))
    assert np.isnan(first[:, :359]).all()
    np.testing.assert_array_equal(first[:, 359], sampled[:, 359])
    middle = accumulated_map(sampled, observation_time(180))
    assert np.isnan(middle[:, :180]).all()
    np.testing.assert_array_equal(middle[:, 180:], sampled[:, 180:])
    np.testing.assert_array_equal(accumulated_map(sampled, 0), sampled)


@pytest.mark.parametrize("reference", [0, 180, 359])
def test_rigid_reconstruction_is_exact(reference):
    source = synoptic_map(False)
    result = reconstruct(source, observation_time(reference), False)
    np.testing.assert_array_equal(result.field, instantaneous_map(observation_time(reference), False))
    np.testing.assert_array_equal(result.weight, np.ones_like(source))


@pytest.mark.parametrize("reference", [0, 180, 359])
def test_transport_paths_agree_with_analytic_truth(reference):
    source = synoptic_map(True)
    target = observation_time(reference)
    for progress in [0.0, 0.37, 1.0]:
        remap = reconstruct(source, target, True, progress)
        sample_times = observation_time(LONGITUDES)
        effective_times = sample_times + progress * (target - sample_times)
        transported_truth = field_at(remap.positions, LATITUDES[:, None], effective_times, True)
        np.testing.assert_allclose(source, transported_truth, atol=3e-12)


@pytest.mark.parametrize("reference", [0, 180, 359])
def test_reconstruction_improves_known_truth(reference):
    target = observation_time(reference)
    source = synoptic_map(True)
    truth = instantaneous_map(target, True)
    final = reconstruct(source, target, True)
    initial_error = area_weighted_rmse(source, truth)
    final_error = area_weighted_rmse(final.field, truth)
    assert final_error < initial_error * 0.6
    assert area_weighted_rmse(final.field, truth, final.supported) < 0.5


def test_periodic_deposition_and_overlaps_retain_all_contributions():
    values = np.array([[2.0, 6.0, -4.0]])
    positions = np.array([[359.5, 359.5, 0.0]])
    result = periodic_remap(values, positions, fill_gaps=False)
    assert result.weight[0, 359] == 1
    assert result.weight[0, 0] == 2
    assert result.field[0, 359] == 4
    assert result.field[0, 0] == 0
    assert result.numerator.sum() == values.sum()
    assert result.weight.sum() == values.size
    assert np.isnan(result.field[0, 1:359]).all()


def test_gaps_are_explicit_and_optional_filling_does_not_change_support():
    source = synoptic_map(True)
    unfilled = reconstruct(source, 0, True, fill_gaps=False)
    filled = reconstruct(source, 0, True, fill_gaps=True)
    assert (~unfilled.supported).any()
    np.testing.assert_array_equal(np.isnan(unfilled.field), ~unfilled.supported)
    assert np.isfinite(filled.field).all()
    np.testing.assert_array_equal(filled.weight, unfilled.weight)
    np.testing.assert_array_equal(filled.field[filled.supported], unfilled.field[unfilled.supported])
    np.testing.assert_allclose(filled.numerator.sum(axis=1), source.sum(axis=1), atol=1e-10)
    np.testing.assert_allclose(filled.weight.sum(axis=1), 360)


def test_empty_observations_are_not_invented():
    result = reconstruct(np.full((len(LATITUDES), 360), np.nan), differential=True)
    assert np.isnan(result.field).all()
    assert not result.supported.any()


def test_initial_transport_frame_is_original_map():
    source = synoptic_map(True)
    np.testing.assert_array_equal(reconstruct(source, differential=True, progress=0).field, source)


def test_neighbor_rotation_times_and_fields():
    for offset in [-1, 0, 1]:
        times = observation_time(LONGITUDES, offset)
        np.testing.assert_allclose(times - observation_time(LONGITUDES), offset * SYNODIC_PERIOD)
        for column in [0, 180, 359]:
            np.testing.assert_array_equal(synoptic_map(True, offset)[:, column],
                                          instantaneous_map(times[column], True)[:, column])


def test_newer_measurements_transport_backward():
    target = observation_time(180)
    assert target - observation_time(0) < 0
    assert target - observation_time(359) > 0
    assert displacement(60, target - observation_time(0), True) > 0


def test_signed_flux_of_instantaneous_truth_is_balanced():
    # Paired longitude lobes and odd axial dipole give zero global net flux.
    weights = np.cos(np.deg2rad(LATITUDES))[:, None]
    for time in [-27.27, -13.635, 0]:
        assert abs(np.sum(instantaneous_map(time, True) * weights)) < 1e-8
