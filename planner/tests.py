from django.test import TestCase

from .models import Department


class DepartmentModelTest(TestCase):
    def test_department_creation(self):
        dept = Department.objects.create(name='Emergency')
        self.assertEqual(str(dept), 'Emergency')
