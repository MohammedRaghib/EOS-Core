import unittest

from eos_core.scorecard_engine import (
	aggregate_values,
	compute_achievement,
	compute_health,
	compute_status,
)


class TestScorecardEngine(unittest.TestCase):
	def test_compute_status_greater_than(self):
		self.assertEqual(compute_status(100, 80, ">="), "Off Track")
		self.assertEqual(compute_status(100, 120, ">="), "On Track")
		self.assertEqual(compute_status(100, 100, ">="), "On Track")
		self.assertIsNone(compute_status(100, None, ">="))

	def test_compute_status_less_than(self):
		self.assertEqual(compute_status(100, 120, "<="), "Off Track")
		self.assertEqual(compute_status(100, 80, "<="), "On Track")

	def test_compute_status_equal(self):
		self.assertEqual(compute_status(100, 100, "=="), "On Track")
		self.assertEqual(compute_status(100, 110, "=="), "Off Track")

	def test_compute_achievement_clamps(self):
		self.assertEqual(compute_achievement(100, 40, ">="), 40.0)
		self.assertEqual(compute_achievement(100, 140, ">="), 100.0)
		self.assertEqual(compute_achievement(100, 50, "<="), 100.0)
		self.assertIsNone(compute_achievement(0, 50, ">="))

	def test_compute_health_bands(self):
		self.assertEqual(compute_health(100, 110, ">="), "Green")
		self.assertEqual(compute_health(100, 96, ">="), "Yellow")
		self.assertEqual(compute_health(100, 40, ">="), "Red")
		self.assertEqual(compute_health(100, 90, "<="), "Green")
		self.assertEqual(compute_health(100, 102, "<="), "Yellow")
		self.assertEqual(compute_health(100, 150, "<="), "Red")

	def test_aggregate_values(self):
		self.assertEqual(aggregate_values([1, 2, None, 3], "Total"), 6.0)
		self.assertEqual(aggregate_values([2, 4], "Average"), 3.0)
		self.assertIsNone(aggregate_values([None], "Total"))