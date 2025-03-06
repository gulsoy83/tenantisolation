from django.contrib import admin

class CoreAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        obj.save(user=request.user)
        # super().save_model(request, obj, form, change)