from django.test import TestCase
from django.urls import reverse
from django.core.exceptions import ValidationError

from workwhere.models import Workplace, Employee, Location, Reservation
from workwhere.forms import ReservationForm


def create_workplace(name: str, location):
    return Workplace.objects.create(name=name, location=location)


class ReservationModelTest(TestCase):
    def test_same_desk_different_employee_error(self):
        l = Location.objects.create(name='location1', isoffice=True)
        w = Workplace.objects.create(name='A1', location=l)
        e1 = Employee.objects.create(first_name='Dave', last_name='Miller', user_id='dav_mi')
        e2 = Employee.objects.create(first_name='Clare', last_name='Smith', user_id='cla_sm')
        day = "2023-04-22"
        
        Reservation.objects.create(day=day, employee=e1, workplace=w)
        with self.assertRaises(ValidationError):
            Reservation.objects.create(day=day, employee=e2, workplace=w)

    def test_two_reservations_of_employee_on_one_day(self):
        l = Location.objects.create(name='location1', isoffice=True)
        w1 = Workplace.objects.create(name='A1', location=l)
        w2 = Workplace.objects.create(name='A2', location=l)
        e = Employee.objects.create(first_name='Dave', last_name='Miller', user_id='dav_mi')
        day = "2023-04-22"
        
        Reservation.objects.create(day=day, employee=e, workplace=w1)
        with self.assertRaises(ValidationError):
            Reservation.objects.create(day=day, employee=e, workplace=w2)


class ReservationFormTests(TestCase):
    def test_date_in_past(self):
        input_data = {'employee': 1, 'day': "2023-04-21", 'workplace': 1}
        form = ReservationForm(input_data)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['day'], ['Invalid date - date in past'])

    # also add tests for non-working days and days too far in the future.

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
