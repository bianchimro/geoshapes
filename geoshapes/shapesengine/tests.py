"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import os
from django.test import TestCase
from shapesengine.shapeutils import ShapeChecker


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)



    def test_checker_validation(self):
        current_path = os.path.dirname("__file__")
        zip_path = os.path.abspath(os.path.join(current_path, "shapesengine/testfiles", "TM_WORLD_BORDERS_SIMPL-0.3.zip"))
        a = ShapeChecker()
        valid, msg = a.validate(zip_path)
        self.assertEqual(valid, True)
    
    def test_checker_handle(self):
        current_path = os.path.dirname("__file__")
        zip_path = os.path.abspath(os.path.join(current_path, "shapesengine/testfiles", "TM_WORLD_BORDERS_SIMPL-0.3.zip"))
        a = ShapeChecker()
        
