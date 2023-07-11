from django.contrib import admin

from .models import Employee, Workplace, Location, Reservation, Floor, Infotext, Settings

class ReservationAdmin(admin.ModelAdmin):
    list_display = ('day', 'workplace', 'employee')

admin.site.register(Reservation, ReservationAdmin)

class FloorInline(admin.TabularInline):
    model = Floor
    extra = 3

class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'isoffice')
    inlines = [FloorInline]

admin.site.register(Location, LocationAdmin)

class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'id', 'isstudent', 'isactive')
    search_fields = ['last_name', 'first_name', 'id']

admin.site.register(Employee, EmployeeAdmin)

class WorkplaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'floor')

admin.site.register(Workplace, WorkplaceAdmin)

class WorkplaceInline(admin.TabularInline):
    model = Workplace
    extra = 3

class FloorAdmin(admin.ModelAdmin):
    inlines = [WorkplaceInline]

admin.site.register(Floor, FloorAdmin)

class InfotextAdmin(admin.ModelAdmin):
    list_display = ('title', 'order')

admin.site.register(Infotext, InfotextAdmin)

admin.site.register(Settings)