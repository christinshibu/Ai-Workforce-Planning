from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand

from planner.models import Department, Staff


class Command(BaseCommand):
    help = 'Seed demo departments, staff, and users for AI workforce planning project.'

    def handle(self, *args, **options):
        manager_group, _ = Group.objects.get_or_create(name='WorkforceManager')
        for codename in ['add_workloadrecord', 'add_forecastresult', 'view_alert']:
            permission = Permission.objects.get(codename=codename)
            manager_group.permissions.add(permission)

        manager, created = User.objects.get_or_create(username='manager')
        if created:
            manager.set_password('manager123')
            manager.is_staff = True
            manager.save()
        manager.groups.add(manager_group)

        if not User.objects.filter(username='viewer').exists():
            User.objects.create_user(username='viewer', password='viewer123')

        departments = ['Emergency', 'ICU', 'Pediatrics', 'Cardiology']
        for dept_name in departments:
            dept, _ = Department.objects.get_or_create(name=dept_name, defaults={'min_staff_per_shift': 3})
            for i in range(1, 5):
                Staff.objects.get_or_create(
                    department=dept,
                    full_name=f'{dept_name} Doctor {i}',
                    role='doctor',
                    defaults={'skill_level': 5},
                )
            for i in range(1, 7):
                Staff.objects.get_or_create(
                    department=dept,
                    full_name=f'{dept_name} Nurse {i}',
                    role='nurse',
                    defaults={'skill_level': 4},
                )
            for i in range(1, 4):
                Staff.objects.get_or_create(
                    department=dept,
                    full_name=f'{dept_name} Support {i}',
                    role='support',
                    defaults={'skill_level': 3},
                )

        self.stdout.write(self.style.SUCCESS('Demo data seeded. manager/manager123, viewer/viewer123'))
