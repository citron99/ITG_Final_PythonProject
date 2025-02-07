from django.test import TestCase

class SimpleTest(TestCase):
    def test_addition(self):
        """Простой тест для проверки 2 + 2 = 4"""
        self.assertEqual(2 + 2, 4)

