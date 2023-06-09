from django.db import models
from django.core.exceptions import ValidationError

from workalendar.registry import registry


class Employee(models.Model):
    id = models.CharField(max_length=20, primary_key=True)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    
    isstudent = models.BooleanField(default=False)
    isactive = models.BooleanField(default=True)

    class Meta:
        # Ordering of the model has an effect on the performance for
        # larger projects, but here it should not be noticeable.
        ordering = ['last_name', 'first_name']    

    def __str__(self):
        return f"{self.last_name}, {self.first_name}"


class Location(models.Model):
    """
    Typically an office building containing several floors 
    with the same address.

    The boolean would only be used for special Locations, which are not 
    counted as office. This allows e.g. to add a Homeoffice workplace.
    Workplaces in non-office locations can be occupied more than once.
    """
    name = models.CharField(max_length=80, unique=True)
    isoffice = models.BooleanField()

    def __str__(self):
        return self.name


class Floor(models.Model):
    """
    One common office space with an individual floor map showing the desks.
    """

    name = models.CharField(max_length=80)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    floormap = models.ImageField(upload_to='floormaps', blank=True)

    def __str__(self):
        return f"{self.location} - {self.name}"


class Workplace(models.Model):
    """
    Each desk has some name or number which is defined here.
    E.g. A1-1, A3-2 or (for non-office locations) also Homeoffice, Travel, NA
    """

    name = models.CharField(max_length=20, unique=True)
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Reservation(models.Model):
    day = models.DateField('date')
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    workplace = models.ForeignKey(Workplace, on_delete=models.CASCADE)

    # class Meta:
    #     constraints = [
    #         models.UniqueConstraint(
    #             fields=['day', 'employee'],
    #             name='unique_employee_per_day',
    #         ),
    #     ]

    def validate_unique_office_place(self, exclude=None):
        """
        Ensure that only workplaces considered as 'isoffice' are 
        unique.
        Such related constraints don't work as a UniqueConstraint. 
        This is therefore a workaround.
        """
        qs1 = Reservation.objects.filter(day=self.day, workplace=self.workplace)
        if qs1.filter(workplace__floor__location__isoffice=True).exclude(employee=self.employee).exists():
            raise ValidationError('Only one reservation per day and office workplace.')

        # Instead of a unique_employee_per_day UniqueConstraint we do 
        # this here. Then it is easier to change existing reservations.
        qs2 = Reservation.objects.exclude(pk=self.pk).filter(employee=self.employee, day=self.day)
        if qs2.exists():
            raise ValidationError('Only one reservation per day and user.')
        #return super().clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.validate_unique_office_place()
        super(Reservation, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.workplace} by {self.employee} ({self.day})"

class Infotext(models.Model):
    """For information shown on the Info page"""
    title = models.CharField(max_length=80, default="HowTo")
    content = models.TextField(default="This is some help text", 
                               help_text="Use html for formatting.")
    order = models.PositiveIntegerField()

class SingletonModel(models.Model):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self.__class__.objects.exclude(id=self.id).delete()
        super(SingletonModel, self).save(*args, **kwargs)

    @classmethod
    def load(cls):
        try:
            return cls.objects.get()
        except cls.DoesNotExist:
            return cls()        

def validate_iso_region(value):
    """
    Using ISO 3166-1 and ISO 3166-2 countries or regions like e.g. "ES-AN"
    to select holidays. See also 
    https://workalendar.github.io/workalendar/iso-registry.html
    """
    if value in registry.get_calendars(include_subregions=True).keys():
        return value
    else:
        raise ValidationError("Only ISO 3166-1 or ISO 3166-2 values.")
    
def validate_min_office_percent(value):
    if value in range(101):
        return value
    else:
        raise ValidationError("Only numbers between 0 and 100.")
    
class Settings(SingletonModel):
    class Meta:
        verbose_name_plural = "settings"

    iso_region = models.CharField(max_length=20, default='ES-AN', 
                                  validators=[validate_iso_region], 
                                  help_text="Set ISO region for correct holidays.")
    # Threshold for the background color of the summary table.
    min_office_percent = models.PositiveIntegerField(default=20, 
                                                     validators=[validate_min_office_percent], 
                                                     help_text="Threshold for background color in summary table.")
