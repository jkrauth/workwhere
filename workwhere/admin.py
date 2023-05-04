from django.contrib import admin

from .models import Employee, Workplace, Location, Reservation, Floor

class ReservationAdmin(admin.ModelAdmin):
    list_display = ('day', 'workplace', 'employee')

admin.site.register(Reservation, ReservationAdmin)

class WorkplaceInline(admin.TabularInline):
    model = Workplace
    extra = 3

class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'isoffice')
    inlines = [WorkplaceInline]

admin.site.register(Location, LocationAdmin)

class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'id', 'isactive')
    search_fields = ['last_name', 'first_name', 'id']

admin.site.register(Employee, EmployeeAdmin)

# class WorkplaceAdmin(admin.ModelAdmin):
#     list_display = ('name', 'location')

# admin.site.register(Workplace, WorkplaceAdmin)

admin.site.register(Floor)

