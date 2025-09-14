from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core import serializers
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta
from .models import (
    ProductCategory, Product, ProductStatus, BlogPost, BlogCategory, 
    PriceList, AboutPage,
    ContactFormSubmission, PageSEO, Enquiry
)

# Create your views here.

def home(request):
    product_categories = ProductCategory.objects.all()
    page_content = PageSEO.objects.filter(slug='home').first()
    if page_content:
        seo_meta_title = page_content.seo_meta_title
        seo_meta_description = page_content.seo_meta_description
        seo_meta_keywords = ', '.join(page_content.get_seo_keywords_list())
    else:
        seo_meta_title = "Home"
        seo_meta_description = ""
        seo_meta_keywords = ""
        

    new_products = Product.objects.order_by('-created_at')[:12]

    return render(request, 'pages/home.html', {
        'product_categories': product_categories,
        'new_products': new_products,
        'seo_meta_title': seo_meta_title,
        'seo_meta_description': seo_meta_description,
        'seo_meta_keywords': seo_meta_keywords,
        
    })

def about(request):
    product_categories = ProductCategory.objects.all()
    page_content = PageSEO.objects.filter(slug='about').first()
    if page_content:
        seo_meta_title = page_content.seo_meta_title
        seo_meta_description = page_content.seo_meta_description
        seo_meta_keywords = ', '.join(page_content.get_seo_keywords_list())
    else:
        seo_meta_title = "Home"
        seo_meta_description = ""
        seo_meta_keywords = ""
    about_page = AboutPage.objects.first()
    return render(request, 'pages/about.html', {
        'about_page': about_page,
        'product_categories': product_categories,
        'seo_meta_title': seo_meta_title,
        'seo_meta_description': seo_meta_description,
        'seo_meta_keywords': seo_meta_keywords,
    })

def contact(request):
    product_categories = ProductCategory.objects.all()
    return render(request, 'pages/contact.html', {'product_categories': product_categories})

def products(request):
    product_categories = ProductCategory.objects.all()
    products = Product.objects.all()
    return render(request, 'pages/products.html', {'product_categories': product_categories, 'products': products})

def category_products(request, category_slug):
    product_categories = ProductCategory.objects.all()
    category = ProductCategory.objects.get(slug=category_slug)
    products = Product.objects.select_related('category').filter(category=category)
    return render(request, 'pages/category_products.html', {
        'product_categories': product_categories,
        'products': products,
        'category': category,
    })

# def individual_product(request, product_id):
#     product_categories = ProductCategory.objects.all()
#     product = Product.objects.get(id=product_id)
#     return render(request, 'pages/individual_products.html', {'product_categories': product_categories, 'product': product})

def product_in_category(request, category_slug, product_slug):
    product_categories = ProductCategory.objects.all()
    product = Product.objects.get(slug=product_slug, category__slug=category_slug)
    return render(request, 'pages/individual_products.html', {'product_categories': product_categories, 'product': product})

def blog(request):
    product_categories = ProductCategory.objects.all()
    blog_posts = BlogPost.objects.filter(status='published').select_related('category').order_by('-published_date')
    blog_categories = BlogCategory.objects.all()
    return render(request, 'pages/blog.html', {
        'product_categories': product_categories,
        'blog_posts': blog_posts,
        'blog_categories': blog_categories,
    })

def individual_blog(request, slug):
    product_categories = ProductCategory.objects.all()
    post = get_object_or_404(BlogPost, slug=slug, status='published')
    
    # Get related posts from the same category
    related_posts = BlogPost.objects.filter(
        category=post.category, 
        status='published'
    ).exclude(id=post.id).order_by('-published_date')[:3]
    
    return render(request, 'pages/individual_blog.html', {
        'product_categories': product_categories,
        'post': post,
        'related_posts': related_posts,
    })

def blog_category(request, category_slug):
    product_categories = ProductCategory.objects.all()
    blog_category = get_object_or_404(BlogCategory, slug=category_slug)
    blog_posts = BlogPost.objects.filter(
        category=blog_category, 
        status='published'
    ).select_related('category').order_by('-published_date')
    blog_categories = BlogCategory.objects.all()
    
    return render(request, 'pages/blog.html', {
        'product_categories': product_categories,
        'blog_posts': blog_posts,
        'blog_categories': blog_categories,
        'selected_category': blog_category,
    })

def price_list(request):
    product_categories = ProductCategory.objects.all()
    # Get the active price list
    price_list = PriceList.objects.filter(is_active=True).first()
    
    return render(request, 'pages/price_list.html', {
        'product_categories': product_categories,
        'price_list': price_list,
    })

@require_GET
def api_products(request):
    products = Product.objects.select_related('category').all()
    data = []
    for p in products:
        data.append({
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'image': p.image.url if p.image else '',
            'category': {
                'id': p.category.id,
                'name': p.category.name,
            } if p.category else None,
        })
    return JsonResponse(data, safe=False)

@require_GET
def api_categories(request):
    categories = ProductCategory.objects.all()
    data = [{'id': c.id, 'name': c.name} for c in categories]
    return JsonResponse(data, safe=False)

@require_GET
def api_blog_posts(request):
    blog_posts = BlogPost.objects.filter(status='published').select_related('category').order_by('-published_date')
    data = []
    for post in blog_posts:
        data.append({
            'id': post.id,
            'title': post.title,
            'slug': post.slug,
            'excerpt': post.excerpt,
            'author': post.author,
            'published_date': post.published_date.isoformat(),
            'is_featured': post.is_featured,
            'featured_image': post.featured_image.url if post.featured_image else None,
            'category': {
                'id': post.category.id,
                'name': post.category.name,
            } if post.category else None,
            'tags': post.get_tags_list(),
        })
    return JsonResponse(data, safe=False)

@require_GET
def api_blog_categories(request):
    categories = BlogCategory.objects.all()
    data = [{'id': c.id, 'name': c.name, 'slug': c.slug} for c in categories]
    return JsonResponse(data, safe=False)


def enquiry(request):
    product_categories = ProductCategory.objects.all()
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            subject = request.POST.get('subject', '').strip()
            message = request.POST.get('message', '').strip()
            sku = request.POST.get('sku', '').strip()
            
            # Basic validation
            if not name or not email or not subject or not message:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Please fill in all required fields.'
                })
            
            if '@' not in email:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Please enter a valid email address.'
                })
            
            ip_address = request.META.get('REMOTE_ADDR')
            
            # Save the enquiry
            enquiry_obj = Enquiry.objects.create(
                sku=sku,
                name=name,
                email=email,
                phone=phone,
                subject=subject,
                message=message,
                ip_address=ip_address
            )
            
            return JsonResponse({
                'status': 'success', 
                'message': 'Your enquiry has been submitted successfully. We will get back to you within 24 hours.'
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': 'An error occurred while submitting your enquiry. Please try again.'
            })
    
    # Get SKU from URL parameter for prefilling
    sku = request.GET.get('sku', '')
    
    # Get latest products for sidebar
    latest_products = Product.objects.select_related('category').order_by('-created_at')[:6]
    
    context = {
        'product_categories': product_categories,
        'prefilled_sku': sku,
        'latest_products': latest_products
    }
    
    return render(request, 'pages/enquiry.html', context)