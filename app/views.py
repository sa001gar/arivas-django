from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.core import serializers
from django.utils import timezone
from django.db.models import Count, Q, Prefetch
from datetime import datetime, timedelta
from .models import (
    ProductCategory, Product, ProductStatus, BlogPost, BlogCategory, 
    PriceList, ContactFormSubmission, PageSEO, Enquiry
)

# Create your views here.

from django.template import Template, Context
from django.template.loader import get_template
from django.utils.safestring import mark_safe

def render_dynamic_content(content, context_dict=None):
    if not content:
        return ""
    if context_dict is None:
        context_dict = {}
    
    template_string = "{% load custom_filters %}" + content
    template = Template(template_string)
    context = Context(context_dict)
    return mark_safe(template.render(context))

def get_product_categories():
    """Cache product categories for 1 hour"""
    cache_key = 'product_categories'
    categories = cache.get(cache_key)
    if categories is None:
        categories = list(ProductCategory.objects.all())
        cache.set(cache_key, categories, 3600)  # 1 hour
    return categories

def get_page_seo_data(slug, default_title=""):
    """Get page SEO data with caching"""
    cache_key = f'page_seo_{slug}'
    seo_data = cache.get(cache_key)
    
    if seo_data is None:
        page_content = PageSEO.objects.filter(slug=slug).first()
        if page_content:
            seo_data = {
                'seo_meta_title': page_content.seo_meta_title or default_title,
                'seo_meta_description': page_content.seo_meta_description or "",
                'seo_meta_keywords': ', '.join(page_content.get_seo_keywords_list()),
                'content1': page_content.content1 or "",
                'content2': page_content.content2 or "",
                'content3': page_content.content3 or "",
                'content4': page_content.content4 or "",
                'content5': page_content.content5 or "",
            }
        else:
            seo_data = {
                'seo_meta_title': default_title,
                'seo_meta_description': "",
                'seo_meta_keywords': "",
                'content1': "", 'content2': "", 'content3': "", 'content4': "", 'content5': "",
            }
        cache.set(cache_key, seo_data, 1800)  # 30 minutes
    return seo_data

@cache_page(60 * 15)  # Cache for 15 minutes
def home(request):
    product_categories = get_product_categories()
    seo_data = get_page_seo_data('home', 'Home')
    
    # Use select_related and optimize queries
    try:
        best_selling = ProductStatus.objects.get(slug='best-selling')
        best_selling_products = Product.objects.select_related('category').filter(
            status=best_selling
        ).order_by('-created_at')[:12]
    except ProductStatus.DoesNotExist:
        best_selling_products = Product.objects.none()

    new_products = Product.objects.select_related('category').order_by('-created_at')[:12]

    return render(request, 'pages/home.html', {
        'product_categories': product_categories,
        'new_products': new_products,
        'best_selling_products': best_selling_products,
        **seo_data
    })

@cache_page(60 * 10)  # Cache for 10 minutes
def about(request):
    product_categories = get_product_categories()
    seo_data = get_page_seo_data('about', 'About')
    
    rendered_page_content = render_dynamic_content(
        seo_data['content1'],
        {"product_categories": product_categories}
    ) if seo_data['content1'] else ""
        
    return render(request, 'pages/about.html', {
        'product_categories': product_categories,
        'seo_meta_title': seo_data['seo_meta_title'],
        'seo_meta_description': seo_data['seo_meta_description'],
        'seo_meta_keywords': seo_data['seo_meta_keywords'],
        'rendered_page_content': rendered_page_content,
    })

@csrf_exempt
def contact(request):
    if request.method == 'POST':
        return handle_contact_form(request)

    product_categories = get_product_categories()
    seo_data = get_page_seo_data('contact', 'Contact Us')
    
    rendered_page_content = render_dynamic_content(
        seo_data['content1'],
        {"product_categories": product_categories}
    ) if seo_data['content1'] else ""
    
    return render(request, 'pages/contact.html', {
        'product_categories': product_categories,
        'seo_meta_title': seo_data['seo_meta_title'],
        'seo_meta_description': seo_data['seo_meta_description'] or "Get in touch with Arivas Pharma. Contact our pharmaceutical experts for inquiries about our products and services.",
        'seo_meta_keywords': seo_data['seo_meta_keywords'] or "contact arivas pharma, pharmaceutical company contact, healthcare contact, medicine inquiry",
        'rendered_page_content': rendered_page_content,
    })

def handle_contact_form(request):
    """Extract contact form handling logic"""
    try:
        form_data = {
            'name': request.POST.get('name', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'subject': request.POST.get('subject', '').strip(),
            'message': request.POST.get('message', '').strip(),
            'phone': request.POST.get('phone', '').strip(),
        }

        # Validation
        if not all([form_data['name'], form_data['email'], form_data['subject'], form_data['message']]):
            return JsonResponse({
                'status': 'error',
                'message': 'Please fill in all required fields.'
            })

        if '@' not in form_data['email']:
            return JsonResponse({
                'status': 'error',
                'message': 'Please enter a valid email address.'
            })

        ContactFormSubmission.objects.create(
            **form_data,
            ip_address=request.META.get('REMOTE_ADDR', '')
        )

        return JsonResponse({
            'status': 'success',
            'message': 'Your message has been sent successfully. We will contact you soon.'
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': 'An error occurred while submitting your message. Please try again.'
        })

@csrf_exempt
def enquiry(request):
    if request.method == 'POST':
        return handle_enquiry_form(request)
    
    product_categories = get_product_categories()
    seo_data = get_page_seo_data('enquiry', 'Enquiry Form')
    
    # Get SKU from URL parameter and latest products
    sku = request.GET.get('sku', '')
    latest_products = Product.objects.select_related('category').order_by('-created_at')[:6]
    
    context = {
        'product_categories': product_categories,
        'prefilled_sku': sku,
        'latest_products': latest_products,
        'seo_meta_title': seo_data['seo_meta_title'],
        'seo_meta_description': seo_data['seo_meta_description'] or "Submit your enquiry to Arivas Pharma. Our team is ready to assist you with product information and support.",
        'seo_meta_keywords': seo_data['seo_meta_keywords'] or "enquiry arivas pharma, pharmaceutical enquiry, medicine inquiry form",
        **{k: v for k, v in seo_data.items() if k.startswith('content')}
    }
    
    return render(request, 'pages/enquiry.html', context)

def handle_enquiry_form(request):
    """Extract enquiry form handling logic"""
    try:
        form_data = {
            'name': request.POST.get('name', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'phone': request.POST.get('phone', '').strip(),
            'subject': request.POST.get('subject', '').strip(),
            'message': request.POST.get('message', '').strip(),
            'sku': request.POST.get('sku', '').strip(),
        }
        
        # Validation
        if not all([form_data['name'], form_data['email'], form_data['subject'], form_data['message']]):
            return JsonResponse({
                'status': 'error', 
                'message': 'Please fill in all required fields.'
            })
        
        if '@' not in form_data['email']:
            return JsonResponse({
                'status': 'error', 
                'message': 'Please enter a valid email address.'
            })
        
        Enquiry.objects.create(
            **form_data,
            ip_address=request.META.get('REMOTE_ADDR')
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

@cache_page(60 * 30)  # Cache for 30 minutes
def products(request):
    product_categories = get_product_categories()
    products = Product.objects.select_related('category').all()
    seo_data = get_page_seo_data('products', 'Products')
    
    return render(request, 'pages/products.html', {
        'product_categories': product_categories,
        'products': products,
        'seo_meta_title': seo_data['seo_meta_title'],
        'seo_meta_description': seo_data['seo_meta_description'] or "Explore our wide range of pharmaceutical products at Arivas Pharma. Quality medicines for healthcare professionals and patients.",
        'seo_meta_keywords': seo_data['seo_meta_keywords'] or "Products, Pharmaceuticals, Healthcare",
    })

@cache_page(60 * 20)  # Cache for 20 minutes
def category_products(request, category_slug):
    product_categories = get_product_categories()
    category = get_object_or_404(ProductCategory, slug=category_slug)
    products = Product.objects.select_related('category').filter(category=category)
    
    return render(request, 'pages/category_products.html', {
        'product_categories': product_categories,
        'products': products,
        'category': category,
        'seo_meta_title': category.seo_meta_title or category.name,
        'seo_meta_description': category.seo_meta_description or category.description,
        'seo_meta_keywords': ', '.join(category.get_seo_keywords_list()) if hasattr(category, 'get_seo_keywords_list') else "",
    })

@cache_page(60 * 30)  # Cache for 30 minutes
def product_in_category(request, category_slug, product_slug):
    product_categories = get_product_categories()
    product = get_object_or_404(
        Product.objects.select_related('category'), 
        slug=product_slug, 
        category__slug=category_slug
    )
    
    return render(request, 'pages/individual_products.html', {
        'product_categories': product_categories,
        'product': product,
        'seo_meta_title': product.seo_meta_title or product.name,
        'seo_meta_description': product.seo_meta_description or product.description,
        'seo_meta_keywords': product.seo_meta_keywords or '',
    })

@cache_page(60 * 15)  # Cache for 15 minutes
def blog(request):
    product_categories = get_product_categories()
    blog_posts = BlogPost.objects.filter(status='published').select_related('category').order_by('-published_date')
    blog_categories = BlogCategory.objects.all()
    seo_data = get_page_seo_data('blog', 'Blog')
    
    return render(request, 'pages/blog.html', {
        'product_categories': product_categories,
        'blog_posts': blog_posts,
        'blog_categories': blog_categories,
        'seo_meta_title': seo_data['seo_meta_title'],
        'seo_meta_description': seo_data['seo_meta_description'] or "Latest news and articles from Arivas Pharma.",
        'seo_meta_keywords': seo_data['seo_meta_keywords'] or "Blog, Articles, News",
    })

@cache_page(60 * 30)  # Cache for 30 minutes
def individual_blog(request, slug):
    product_categories = get_product_categories()
    post = get_object_or_404(BlogPost.objects.select_related('category'), slug=slug, status='published')
    
    # Get related posts efficiently
    related_posts = BlogPost.objects.filter(
        category=post.category, 
        status='published'
    ).exclude(id=post.id).select_related('category').order_by('-published_date')[:3]

    return render(request, 'pages/individual_blog.html', {
        'product_categories': product_categories,
        'post': post,
        'related_posts': related_posts,
        'seo_meta_title': post.seo_meta_title or post.title,
        'seo_meta_description': post.seo_meta_description or post.excerpt,
        'seo_meta_keywords': post.seo_meta_keywords or '',
    })

@cache_page(60 * 20)  # Cache for 20 minutes
def blog_category(request, category_slug):
    product_categories = get_product_categories()
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

@cache_page(60 * 60)  # Cache for 1 hour
def price_list(request):
    product_categories = get_product_categories()
    price_list = PriceList.objects.filter(is_active=True).first()
    seo_data = get_page_seo_data('price-list', 'Price List')

    return render(request, 'pages/price_list.html', {
        'product_categories': product_categories,
        'price_list': price_list,
        'seo_meta_title': seo_data['seo_meta_title'],
        'seo_meta_description': seo_data['seo_meta_description'] or "Description for Price List",
        'seo_meta_keywords': seo_data['seo_meta_keywords'] or "Price, List",
    })

@require_GET
@cache_page(60 * 30)  # Cache for 30 minutes
def api_products(request):
    products = Product.objects.select_related('category').all()
    data = [
        {
            'id': p.id,
            'name': p.name,
            'slug': p.slug,
            'description': p.description,
            'image': p.image.url if p.image else '',
            'category': {
                'id': p.category.id,
                'name': p.category.name,
                'slug': p.category.slug,
            } if p.category else None,
        }
        for p in products
    ]
    return JsonResponse(data, safe=False)

@require_GET
@cache_page(60 * 60)  # Cache for 1 hour
def api_categories(request):
    categories = get_product_categories()
    data = [{'id': c.id, 'name': c.name, 'slug': c.slug} for c in categories]
    return JsonResponse(data, safe=False)

@require_GET
@cache_page(60 * 15)  # Cache for 15 minutes
def api_blog_posts(request):
    blog_posts = BlogPost.objects.filter(status='published').select_related('category').order_by('-published_date')
    data = [
        {
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
            'tags': post.get_tags_list() if hasattr(post, 'get_tags_list') else [],
        }
        for post in blog_posts
    ]
    return JsonResponse(data, safe=False)

@require_GET
@cache_page(60 * 60)  # Cache for 1 hour
def api_blog_categories(request):
    categories = BlogCategory.objects.all()
    data = [{'id': c.id, 'name': c.name, 'slug': c.slug} for c in categories]
    return JsonResponse(data, safe=False)
