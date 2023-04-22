from django.test import TestCase
from workwhere.models import Workplace, Employee, Location
from django.urls import reverse


def create_workplace(name: str, location):
    return Workplace.objects.create(name=name, location=location)


class ReservationModelTest(TestCase):
    def test_same_desk_different_employee_error(self):
        l = Location.objects.create(name='location1', isoffice=True)
        w = Workplace.objects.create(name='A1', location=l)
        e1 = Employee.objects.create(first_name='Dave', last_name='Miller', user_id='dav_mi')

# class ReserveViewTests(TestCase):
#     def test_

class TodayViewTests(TestCase):
    def test_no_workplaces(self):
        response = self.client.get(reverse('workwhere:today'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No office desks are available.")
        self.assertQuerysetEqual(response.context['desks_today'], [])

class WeekViewTests(TestCase):
    def test_week_redirect(self):
        response = self.client.get(reverse('workwhere:week_redirect'))
        self.assertEqual(response.status_code, 302)

    def test_no_workplaces(self):
        response = self.client.get( \
            reverse('workwhere:week', kwargs={'year':2023, 'week': 15}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Monday")
        self.assertQuerysetEqual(response.context['data'], \
            [['', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']])
