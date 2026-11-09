"""Checks for the HMI longitude grid and source-map interpolation."""
import unittest

import numpy as np

from synoptic_reconstruction import (calculate_coordinates, interpolate_field,
                                     select_source_map)


class CoordinateRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.header = {'CRVAL1': 180.0, 'CRPIX1': 4.5, 'CDELT1': -45.0,
                       'CRVAL2': 0.0, 'CRPIX2': 4.5, 'CDELT2': 0.25}
        self.image = np.arange(64, dtype=float).reshape(8, 8)

    def test_hmi_negative_header_maps_to_increasing_physical_longitude(self):
        longitude, _ = calculate_coordinates(self.image, self.header)
        np.testing.assert_allclose(longitude, np.arange(8) * 45 + 22.5)

    def test_original_sample_positions_reproduce_input(self):
        longitude, latitude = calculate_coordinates(self.image, self.header)
        coordinates = np.broadcast_to(longitude, self.image.shape)
        source = np.ones(self.image.shape, dtype=int)
        result = interpolate_field([self.image] * 3, [self.header] * 3,
                                   latitude, source, coordinates)
        np.testing.assert_allclose(result, self.image, atol=1e-10)

    def test_rotation_boundary_chooses_and_samples_correct_map(self):
        _, latitude = calculate_coordinates(self.image, self.header)
        phi = np.array([[-337.5, 22.5, 382.5]] * 8)
        source, longitude = select_source_map(phi)
        maps = [np.full((8, 8), value, dtype=float) for value in (1, 2, 3)]
        result = interpolate_field(maps, [self.header] * 3, latitude, source, longitude)
        np.testing.assert_allclose(result, np.tile([1, 2, 3], (8, 1)), atol=1e-10)


if __name__ == '__main__':
    unittest.main()
