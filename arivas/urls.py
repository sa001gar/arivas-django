"""
URL configuration for arivas project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('summernote/', include('django_summernote.urls')),

    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('products/', views.products, name='products'),
    path('products/category/<slug:category_slug>/', views.category_products, name='category_products'),
    # path('products/<slug:product_slug>/', views.individual_product, name='individual_product'),
    path('products/<slug:category_slug>/<slug:product_slug>/', views.product_in_category, name='product_in_category'),
    path('blog/', views.blog, name='blog'),
    path('blog/category/<slug:category_slug>/', views.blog_category, name='blog_category'),
    path('blog/<slug:slug>/', views.individual_blog, name='individual_blog'),
    path('price-list/', views.price_list, name='price_list'),

    # Analytics and Admin APIs
    path('admin/dashboard/analytics/', views.admin_dashboard_data, name='admin_dashboard_data'),

    # Public APIs
    path('api/products/', views.api_products, name='api_products'),
    path('api/categories/', views.api_categories, name='api_categories'),
    path('api/blog-posts/', views.api_blog_posts, name='api_blog_posts'),
    path('api/blog-categories/', views.api_blog_categories, name='api_blog_categories'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
