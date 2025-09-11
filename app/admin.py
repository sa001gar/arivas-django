from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import RangeDateFilter, RangeNumericFilter, ChoicesDropdownFilter
from unfold.decorators import display, action
from unfold.admin import ModelAdmin
from .models import (
    ProductCategory, Feature_Blocks, Product, ProductStatus, 
    BlogPost, BlogCategory, PriceList, AboutPage,
    PageVisit, ProductView, BlogPostView, ContactFormSubmission, Page
)
from django_summernote.admin import SummernoteModelAdmin

# Register your models here.

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

@admin.register(Feature_Blocks)
class FeatureBlocksAdmin(ModelAdmin):
    list_display = ['title', 'is_active_display', 'created_at']
    list_filter = [('created_at', RangeDateFilter)]
    search_fields = ['title', 'description']
    
    @display(description="Status")
    def is_active_display(self, obj):
        return format_html(
            '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Active</span>'
        )

@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ['name', 'category', 'status_badge', 'image_preview', 'created_at']
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
    search_fields = ['title', 'content', 'author', 'tags']
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
        ('SEO & Tags', {
            'fields': ('meta_description', 'tags'),
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

@admin.register(AboutPage)
class AboutPageAdmin(ModelAdmin, SummernoteModelAdmin):
    summernote_fields = ('content1', 'content2')
    list_display = ['id', 'seo_meta_name', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']
    search_fields = ['seo_meta_name', 'seo_meta_description', 'seo_meta_keywords']
    
    fieldsets = (
        ('SEO Meta Information', {
            'fields': ('seo_meta_name', 'seo_meta_description', 'seo_meta_keywords'),
            'description': 'Manage SEO-related meta tags for the About page.',
            'classes': ('collapse', 'unfold-fieldset')
        }),
        ('Content Sections', {
            'fields': ('content1', 'content2'),
            'description': 'Main content blocks for the About page.',
            'classes': ('unfold-fieldset',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse', 'unfold-fieldset')
        }),
    )

@admin.register(Page)
class PageAdmin(ModelAdmin, SummernoteModelAdmin):
    summernote_fields = ('content',)
    list_display = ['title', 'url', 'created_at', 'updated_at']
    prepopulated_fields = {'url': ('title',)}
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'url'),
            'classes': ('unfold-fieldset',)
        }),
        ('Content', {
            'fields': ('content',),
            'classes': ('unfold-fieldset',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse', 'unfold-fieldset')
        }),
    )
# Analytics Admin Classes
@admin.register(PageVisit)
class PageVisitAdmin(ModelAdmin):
    list_display = ['page_title', 'page_url', 'ip_address', 'visit_date', 'referrer_domain']
    list_filter = [
        ('visit_date', RangeDateFilter),
        'page_url',
    ]
    search_fields = ['page_title', 'page_url', 'ip_address', 'referrer']
    readonly_fields = ['page_url', 'page_title', 'ip_address', 'user_agent', 'referrer', 'visit_date', 'session_id']
    
    @display(description="Referrer")
    def referrer_domain(self, obj):
        if obj.referrer:
            try:
                from urllib.parse import urlparse
                domain = urlparse(obj.referrer).netloc
                return format_html('<span class="text-blue-600">{}</span>', domain)
            except:
                return 'Invalid URL'
        return format_html('<span class="text-gray-400">Direct</span>')

@admin.register(ProductView)
class ProductViewAdmin(ModelAdmin):
    list_display = ['product', 'ip_address', 'view_date']
    list_filter = [
        ('view_date', RangeDateFilter),
        ('product__category', ChoicesDropdownFilter),
    ]
    search_fields = ['product__name', 'ip_address']
    readonly_fields = ['product', 'ip_address', 'view_date', 'session_id']

@admin.register(BlogPostView)
class BlogPostViewAdmin(ModelAdmin):
    list_display = ['blog_post', 'ip_address', 'view_date']
    list_filter = [
        ('view_date', RangeDateFilter),
        ('blog_post__category', ChoicesDropdownFilter),
    ]
    search_fields = ['blog_post__title', 'ip_address']
    readonly_fields = ['blog_post', 'ip_address', 'view_date', 'session_id']

@admin.register(ContactFormSubmission)
class ContactFormSubmissionAdmin(ModelAdmin):
    list_display = ['name', 'email', 'subject', 'submitted_date', 'response_status']
    list_filter = [
        'is_responded',
        ('submitted_date', RangeDateFilter),
    ]
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['name', 'email', 'phone', 'subject', 'message', 'ip_address', 'submitted_date']
    
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
    
    @action(description="Mark as responded")
    def mark_responded(self, request, queryset):
        queryset.update(is_responded=True)
    
    @action(description="Mark as pending")
    def mark_pending(self, request, queryset):
        queryset.update(is_responded=False)
    
    actions = ['mark_responded', 'mark_pending']

# Customize Admin Site
admin.site.site_header = "Arivas Pharmaceuticals Admin"
admin.site.site_title = "Arivas Admin"
admin.site.index_title = "Welcome to Arivas Pharmaceuticals Administration"
