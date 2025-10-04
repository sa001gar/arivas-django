from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import RangeDateFilter, RangeNumericFilter, ChoicesDropdownFilter
from unfold.decorators import display, action
from django_summernote.admin import SummernoteModelAdmin
from .models import (
    ProductCategory, Product, ProductStatus, 
    BlogPost, BlogCategory, PriceList, ContactFormSubmission, PageSEO, Enquiry
)

# Custom admin filters
class ResponseStatusFilter(admin.SimpleListFilter):
    title = 'Response Status'
    parameter_name = 'response_status'

    def lookups(self, request, model_admin):
        return (
            ('pending', 'Pending Response'),
            ('responded', 'Responded'),
            ('urgent', 'Urgent (>24h)'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'pending':
            return queryset.filter(is_responded=False)
        if self.value() == 'responded':
            return queryset.filter(is_responded=True)
        if self.value() == 'urgent':
            urgent_time = timezone.now() - timedelta(hours=24)
            return queryset.filter(is_responded=False, submitted_date__lt=urgent_time)

class SKUFilter(admin.SimpleListFilter):
    title = 'Enquiry Type'
    parameter_name = 'sku_type'

    def lookups(self, request, model_admin):
        return (
            ('with_sku', 'Product Specific'),
            ('without_sku', 'General Enquiry'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'with_sku':
            return queryset.exclude(sku__isnull=True).exclude(sku__exact='')
        if self.value() == 'without_sku':
            return queryset.filter(Q(sku__isnull=True) | Q(sku__exact=''))

@admin.register(ProductCategory)
class ProductCategoryAdmin(ModelAdmin):
    list_display = ['name', 'slug', 'product_count', 'created_at']
    list_filter = [('created_at', RangeDateFilter)]
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    
    @display(description="Products")
    def product_count(self, obj):
        count = obj.products.count()
        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">{}</span>',
            count
        )


@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ['name','sku', 'category', 'status_badge', 'image_preview', 'created_at']
    list_filter = [
        ('category', ChoicesDropdownFilter),
        ('status', ChoicesDropdownFilter),
        ('created_at', RangeDateFilter)
    ]
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    
    @display(description="Status")
    def status_badge(self, obj):
        if obj.status:
            return format_html(
                '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">{}</span>',
                obj.status.name
            )
        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">No Status</span>'
        )
    
    @display(description="Image")
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="40" height="40" style="border-radius: 4px; object-fit: cover;" />',
                obj.image.url
            )
        return format_html('<span class="text-gray-400">No image</span>')

@admin.register(ProductStatus)
class ProductStatusAdmin(ModelAdmin):
    list_display = ['name', 'product_count']
    
    @display(description="Products")
    def product_count(self, obj):
        count = obj.products.count()
        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">{}</span>',
            count
        )

@admin.register(BlogCategory)
class BlogCategoryAdmin(ModelAdmin):
    list_display = ['name', 'slug', 'post_count', 'created_at']
    list_filter = [('created_at', RangeDateFilter)]
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    
    @display(description="Posts")
    def post_count(self, obj):
        count = obj.posts.count()
        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">{}</span>',
            count
        )

@admin.register(BlogPost)
class BlogPostAdmin(ModelAdmin, SummernoteModelAdmin):
    summernote_fields = ('content',)
    list_display = ['title', 'category', 'author', 'status_badge', 'featured_badge', 'image_preview', 'published_date']
    list_filter = [
        ('category', ChoicesDropdownFilter),
        ('status', ChoicesDropdownFilter),
        'is_featured',
        ('published_date', RangeDateFilter),
        ('created_at', RangeDateFilter)
    ]
    search_fields = ['title', 'content', 'author', 'seo_meta_keywords']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'category', 'author', 'status'),
            'classes': ('unfold-fieldset',)
        }),
        ('Content', {
            'fields': ('excerpt', 'content', 'featured_image'),
            'classes': ('unfold-fieldset',)
        }),
        ('Publishing', {
            'fields': ('published_date', 'is_featured'),
            'classes': ('unfold-fieldset',)
        }),
        ('SEO & Meta', {
            'fields': ('seo_meta_title', 'seo_meta_description', 'seo_meta_keywords'),
            'classes': ('collapse', 'unfold-fieldset')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse', 'unfold-fieldset')
        }),
    )
    
    @display(description="Status")
    def status_badge(self, obj):
        status_colors = {
            'draft': 'bg-gray-100 text-gray-800',
            'published': 'bg-green-100 text-green-800',
            'archived': 'bg-red-100 text-red-800'
        }
        color = status_colors.get(obj.status, 'bg-gray-100 text-gray-800')
        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {}">{}</span>',
            color,
            obj.get_status_display()
        )
    
    @display(description="Featured")
    def featured_badge(self, obj):
        if obj.is_featured:
            return format_html(
                '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">⭐ Featured</span>'
            )
        return format_html('<span class="text-gray-400">—</span>')
    
    @display(description="Image")
    def image_preview(self, obj):
        if obj.featured_image:
            return format_html(
                '<img src="{}" width="40" height="40" style="border-radius: 4px; object-fit: cover;" />',
                obj.featured_image.url
            )
        return format_html('<span class="text-gray-400">No image</span>')

@admin.register(PriceList)
class PriceListAdmin(ModelAdmin):
    list_display = ['title', 'version', 'status_badge', 'file_preview', 'upload_date', 'updated_date']
    list_filter = [
        'is_active',
        ('upload_date', RangeDateFilter),
        ('updated_date', RangeDateFilter)
    ]
    search_fields = ['title', 'version', 'description']
    readonly_fields = ['upload_date', 'updated_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'version', 'description'),
            'classes': ('unfold-fieldset',)
        }),
        ('File Upload', {
            'fields': ('pdf_file', 'is_active'),
            'classes': ('unfold-fieldset',)
        }),
        ('Timestamps', {
            'fields': ('upload_date', 'updated_date'),
            'classes': ('collapse', 'unfold-fieldset')
        }),
    )
    
    @display(description="Status")
    def status_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">✓ Active</span>'
            )
        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">✗ Inactive</span>'
        )
    
    @display(description="File")
    def file_preview(self, obj):
        if obj.pdf_file:
            return format_html(
                '<a href="{}" target="_blank" class="inline-flex items-center px-2.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 hover:bg-blue-200">📄 View PDF</a>',
                obj.pdf_file.url
            )
        return format_html('<span class="text-gray-400">No file</span>')

@admin.register(PageSEO)
class PageSEOAdmin(ModelAdmin, SummernoteModelAdmin):
    summernote_fields = ('content1', 'content2', 'content3', 'content4', 'content5')
    list_display = ['title', 'slug', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ['title', 'seo_meta_title', 'seo_meta_description', 'seo_meta_keywords']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug'),
            'classes': ('unfold-fieldset',)
        }),
        ('SEO Settings', {
            'fields': ('seo_meta_title', 'seo_meta_description', 'seo_meta_keywords'),
            'classes': ('collapse', 'unfold-fieldset')
        }),
        ('Content Sections', {
            'fields': ('content1', 'content2', 'content3', 'content4', 'content5'),
            'classes': ('unfold-fieldset',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse', 'unfold-fieldset')
        }),
    )

@admin.register(ContactFormSubmission)
class ContactFormSubmissionAdmin(ModelAdmin):
    list_display = ['name', 'email', 'subject', 'submitted_date', 'response_status', 'priority_badge']
    list_filter = [
        ResponseStatusFilter,
        ('submitted_date', RangeDateFilter),
    ]
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['name', 'email', 'phone', 'subject', 'message', 'ip_address', 'submitted_date']
    list_per_page = 20
    date_hierarchy = 'submitted_date'
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('name', 'email', 'phone'),
            'classes': ('unfold-fieldset',)
        }),
        ('Message Details', {
            'fields': ('subject', 'message'),
            'classes': ('unfold-fieldset',)
        }),
        ('Response Status', {
            'fields': ('is_responded',),
            'classes': ('unfold-fieldset',)
        }),
        ('Metadata', {
            'fields': ('ip_address', 'submitted_date'),
            'classes': ('collapse', 'unfold-fieldset')
        }),
    )
    
    @display(description="Response Status")
    def response_status(self, obj):
        if obj.is_responded:
            return format_html(
                '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">✓ Responded</span>'
            )
        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">⏳ Pending</span>'
        )
    
    @display(description="Priority")
    def priority_badge(self, obj):
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        # Mark as urgent if submitted more than 24 hours ago and not responded
        if not obj.is_responded:
            time_diff = timezone.now() - obj.submitted_date
            if time_diff > timedelta(hours=24):
                return format_html(
                    '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Urgent</span>'
                )
            elif time_diff > timedelta(hours=12):
                return format_html(
                    '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">High</span>'
                )
        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">Normal</span>'
        )
    
    @action(description="Mark as responded")
    def mark_responded(self, request, queryset):
        updated = queryset.update(is_responded=True)
        self.message_user(request, f'{updated} contact submissions marked as responded.')
    
    @action(description="Mark as pending")
    def mark_pending(self, request, queryset):
        updated = queryset.update(is_responded=False)
        self.message_user(request, f'{updated} contact submissions marked as pending.')
    
    actions = ['mark_responded', 'mark_pending']
    
    def changelist_view(self, request, extra_context=None):
        # Add summary statistics to the changelist
        extra_context = extra_context or {}
        
        # Get statistics
        total_contacts = ContactFormSubmission.objects.count()
        pending_contacts = ContactFormSubmission.objects.filter(is_responded=False).count()
        urgent_contacts = ContactFormSubmission.objects.filter(
            is_responded=False,
            submitted_date__lt=timezone.now() - timedelta(hours=24)
        ).count()
        today_contacts = ContactFormSubmission.objects.filter(
            submitted_date__date=timezone.now().date()
        ).count()
        
        extra_context['summary_stats'] = {
            'total': total_contacts,
            'pending': pending_contacts,
            'urgent': urgent_contacts,
            'today': today_contacts,
        }
        
        return super().changelist_view(request, extra_context=extra_context)

@admin.register(Enquiry)
class EnquiryAdmin(ModelAdmin):
    list_display = ['sku_display', 'name', 'email', 'phone', 'subject', 'submitted_date', 'response_status', 'priority_badge']
    list_filter = [
        ResponseStatusFilter,
        SKUFilter,
        ('submitted_date', RangeDateFilter),
    ]
    search_fields = ['sku', 'name', 'email', 'phone', 'subject', 'message']
    readonly_fields = ['sku', 'name', 'email', 'phone', 'subject', 'message', 'ip_address', 'submitted_date']
    list_per_page = 20
    date_hierarchy = 'submitted_date'
    
    fieldsets = (
        ('Enquiry Information', {
            'fields': ('sku', 'name', 'email', 'phone', 'subject', 'message'),
            'classes': ('unfold-fieldset',)
        }),
        ('Response Status', {
            'fields': ('is_responded',),
            'classes': ('unfold-fieldset',)
        }),
        ('Metadata', {
            'fields': ('ip_address', 'submitted_date'),
            'classes': ('collapse', 'unfold-fieldset')
        }),
    )
    
    @display(description="Product SKU")
    def sku_display(self, obj):
        if obj.sku:
            return format_html(
                '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 font-mono">{}</span>',
                obj.sku
            )
        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">General</span>'
        )
    
    @display(description="Response Status")
    def response_status(self, obj):
        if obj.is_responded:
            return format_html(
                '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">✓ Responded</span>'
            )
        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">Pending</span>'
        )
    
    @display(description="Priority")
    def priority_badge(self, obj):
        from datetime import datetime, timedelta
        from django.utils import timezone
        
        # Mark as urgent if submitted more than 24 hours ago and not responded
        if not obj.is_responded:
            time_diff = timezone.now() - obj.submitted_date
            if time_diff > timedelta(hours=24):
                return format_html(
                    '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Urgent</span>'
                )
            elif time_diff > timedelta(hours=12):
                return format_html(
                    '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">High</span>'
                )
        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">Normal</span>'
        )
    
    @action(description="Mark as responded")
    def mark_responded(self, request, queryset):
        updated = queryset.update(is_responded=True)
        self.message_user(request, f'{updated} enquiries marked as responded.')
    
    @action(description="Mark as pending")
    def mark_pending(self, request, queryset):
        updated = queryset.update(is_responded=False)
        self.message_user(request, f'{updated} enquiries marked as pending.')
    
    @action(description="Export selected enquiries")
    def export_enquiries(self, request, queryset):
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="enquiries.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['SKU', 'Name', 'Email', 'Phone', 'Subject', 'Message', 'Submitted Date', 'Responded'])
        
        for enquiry in queryset:
            writer.writerow([
                enquiry.sku or '',
                enquiry.name,
                enquiry.email,
                enquiry.phone or '',
                enquiry.subject,
                enquiry.message,
                enquiry.submitted_date.strftime('%Y-%m-%d %H:%M:%S'),
                'Yes' if enquiry.is_responded else 'No'
            ])
        
        return response
    
    actions = ['mark_responded', 'mark_pending', 'export_enquiries']
    
    def changelist_view(self, request, extra_context=None):
        # Add summary statistics to the changelist
        extra_context = extra_context or {}
        
        # Get statistics
        total_enquiries = Enquiry.objects.count()
        pending_enquiries = Enquiry.objects.filter(is_responded=False).count()
        urgent_enquiries = Enquiry.objects.filter(
            is_responded=False,
            submitted_date__lt=timezone.now() - timedelta(hours=24)
        ).count()
        today_enquiries = Enquiry.objects.filter(
            submitted_date__date=timezone.now().date()
        ).count()
        
        extra_context['summary_stats'] = {
            'total': total_enquiries,
            'pending': pending_enquiries,
            'urgent': urgent_enquiries,
            'today': today_enquiries,
        }
        
        return super().changelist_view(request, extra_context=extra_context)


# Customize Admin Site
admin.site.site_header = "Arivas Pharmaceuticals Admin"
admin.site.site_title = "Arivas Admin"
admin.site.index_title = "Welcome to Arivas Pharmaceuticals Administration"

# Custom admin site configuration for better organization
from django.contrib.admin import AdminSite

class ArivasAdminSite(AdminSite):
    site_header = "Arivas Pharmaceuticals Admin"
    site_title = "Arivas Admin"
    index_title = "Welcome to Arivas Pharmaceuticals Administration"
    
    def get_app_list(self, request, app_label=None):
        """
        Return a sorted list of all the installed apps that have been
        registered in this site.
        """
        app_dict = self._build_app_dict(request, app_label)
        
        # Custom ordering and grouping
        custom_order = {
            'Communications': ['Enquiry', 'ContactFormSubmission'],
            'Products': ['Product', 'ProductCategory', 'ProductStatus'],
            'Content': ['BlogPost', 'BlogCategory', 'PageSEO'],
            'Resources': ['PriceList'],
            'Administration': ['User', 'Group']
        }
        
        # Build new app list with custom grouping
        new_app_list = []
        
        for group_name, model_names in custom_order.items():
            models_for_group = []
            
            for app in app_dict.values():
                for model in app['models']:
                    if model['object_name'] in model_names:
                        models_for_group.append(model)
            
            if models_for_group:
                new_app_list.append({
                    'name': group_name,
                    'app_label': group_name.lower(),
                    'app_url': '',
                    'has_module_perms': True,
                    'models': models_for_group
                })
        
        # Add any remaining models not in custom order
        remaining_models = []
        for app in app_dict.values():
            for model in app['models']:
                found = False
                for model_names in custom_order.values():
                    if model['object_name'] in model_names:
                        found = True
                        break
                if not found:
                    remaining_models.append(model)
        
        if remaining_models:
            new_app_list.append({
                'name': 'Other',
                'app_label': 'other',
                'app_url': '',
                'has_module_perms': True,
                'models': remaining_models
            })
        
        return new_app_list
