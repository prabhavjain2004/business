from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Profile, Outlet, NFCCard, NFCLog

# Register your models here.
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'

class OutletInline(admin.StackedInline):
    model = Outlet
    can_delete = False
    verbose_name_plural = 'Outlet Details'
    fk_name = 'user'

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_user_type')
    list_select_related = ('profile',)

    def get_user_type(self, instance):
        try:
            return instance.profile.user_type
        except Profile.DoesNotExist:
            return ''
    get_user_type.short_description = 'User Type'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        
        inline_instances = []
        for inline_class in self.inlines:
            if inline_class == OutletInline and hasattr(obj, 'profile') and obj.profile.user_type != 'outlet':
                continue
            inline = inline_class(self.model, self.admin_site)
            inline_instances.append(inline)
        return inline_instances

    def get_inlines(self, request, obj=None):
        if not obj:
            return []
        
        inlines = []
        if hasattr(obj, 'profile') and obj.profile.user_type == 'outlet':
            inlines = [ProfileInline, OutletInline]
        else:
            inlines = [ProfileInline]
        return inlines

class OutletAdmin(admin.ModelAdmin):
    list_display = ('outlet_name', 'contact_person', 'phone_number', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('outlet_name', 'contact_person', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')

class NFCCardAdmin(admin.ModelAdmin):
    list_display = ('card_id', 'name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('card_id', 'name')
    readonly_fields = ('created_at', 'updated_at')

class NFCLogAdmin(admin.ModelAdmin):
    list_display = ('card_identifier', 'outlet', 'user', 'timestamp', 'action', 'success')
    list_filter = ('success', 'action', 'outlet')
    search_fields = ('card_identifier', 'notes')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'

# Unregister the default UserAdmin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
admin.site.register(Outlet, OutletAdmin)
admin.site.register(NFCCard, NFCCardAdmin)
admin.site.register(NFCLog, NFCLogAdmin)
