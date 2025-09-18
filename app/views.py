from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.decorators.cache import cache_page, cache_control
from django.views.decorators.vary import vary_on_headers
from django.core import serializers
from django.utils import timezone
from django.db.models import Count, Q, Prefetch
from django.core.cache import cache
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
    
    # Create a template string that loads the custom filters
    template_string = "{% load custom_filters %}" + content
    template = Template(template_string)
    context = Context(context_dict)
    return mark_safe(template.render(context))

def invalidate_cache_keys():
    """
    Utility function to invalidate cache keys when data changes.
    This should be called after admin updates or data modifications.
    """
    cache_keys = [
        'home_page_data_v1',
        'about_page_data_v1',
        'products_page_data_v1',
        'blog_page_data_v1',
        'price_list_page_data_v1',
        'contact_page_data_v1',
        'enquiry_page_data_v1',
        'api_products_v1',
        'api_categories_v1',
        'api_blog_posts_v1',
        'api_blog_categories_v1',
    ]
    
    for key in cache_keys:
        cache.delete(key)
    
    # Delete pattern-based cache keys
    cache.delete_pattern('category_products_*_v1')
    cache.delete_pattern('product_*_*_v1')
    cache.delete_pattern('blog_post_*_v1')
    cache.delete_pattern('blog_category_*_v1')

@cache_control(max_age=3600)  # Cache for 1 hour
@vary_on_headers('User-Agent')
def home(request):
    # Cache key for home page data
    cache_key = 'home_page_data_v1'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        product_categories, page_content, best_selling_products, new_products = cached_data
    else:
        # Optimized queries with select_related and prefetch_related
        product_categories = ProductCategory.objects.select_related().prefetch_related(
            Prefetch('products', queryset=Product.objects.select_related('status'))
        ).all()
        
        page_content = PageSEO.objects.filter(slug='home').first()
        
        try:
            best_selling = ProductStatus.objects.get(slug='best-selling')
            best_selling_products = Product.objects.select_related('category', 'status').filter(
                status=best_selling
            ).order_by('-created_at')[:12]
        except ProductStatus.DoesNotExist:
            best_selling_products = Product.objects.none()

        new_products = Product.objects.select_related('category', 'status').order_by('-created_at')[:12]
        
        # Cache for 30 minutes
        cache.set(cache_key, (product_categories, page_content, best_selling_products, new_products), 1800)

    if page_content:
        seo_meta_title = page_content.seo_meta_title or "Home"
        seo_meta_description = page_content.seo_meta_description or ""
        seo_meta_keywords = ', '.join(page_content.get_seo_keywords_list())
        content1 = page_content.content1 if page_content.content1 else ""
        content2 = page_content.content2 if page_content.content2 else ""
        content3 = page_content.content3 if page_content.content3 else ""
        content4 = page_content.content4 if page_content.content4 else ""
        content5 = page_content.content5 if page_content.content5 else ""
    else:
        seo_meta_title = "Home"
        seo_meta_description = ""
        seo_meta_keywords = ""
        content1 = content2 = content3 = content4 = content5 = ""

    return render(request, 'pages/home.html', {
        'product_categories': product_categories,
        'new_products': new_products,
        'best_selling_products': best_selling_products,
        'seo_meta_title': seo_meta_title,
        'seo_meta_description': seo_meta_description,
        'seo_meta_keywords': seo_meta_keywords,
        'content1': content1,
        'content2': content2,
        'content3': content3,
        'content4': content4,
        'content5': content5,
    })

@cache_control(max_age=1800)  # Cache for 30 minutes
def about(request):
    # Cache key for about page data
    cache_key = 'about_page_data_v1'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        product_categories, page_content = cached_data
    else:
        product_categories = ProductCategory.objects.select_related().all()
        page_content = PageSEO.objects.filter(slug='about').first()
        # Cache for 15 minutes
        cache.set(cache_key, (product_categories, page_content), 900)
    
    if page_content:
        rendered_page_content = render_dynamic_content(
            page_content.content1 if page_content.content1 else "",
            {
                "product_categories": product_categories,
            }
        )
        seo_meta_title = page_content.seo_meta_title or "About"
        seo_meta_description = page_content.seo_meta_description or ""
        seo_meta_keywords = ', '.join(page_content.get_seo_keywords_list())
    else:
        rendered_page_content = ""
        seo_meta_title = "About"
        seo_meta_description = ""
        seo_meta_keywords = ""
        
    return render(request, 'pages/about.html', {
        'product_categories': product_categories,
        'seo_meta_title': seo_meta_title,
        'seo_meta_description': seo_meta_description,
        'seo_meta_keywords': seo_meta_keywords,
        'rendered_page_content': rendered_page_content,
    })

@csrf_exempt
def contact(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()
            subject = request.POST.get('subject', '').strip()
            message = request.POST.get('message', '').strip()
            phone = request.POST.get('phone', '').strip()

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

            ip_address = request.META.get('REMOTE_ADDR', '')

            ContactFormSubmission.objects.create(
                name=name,
                email=email,
                phone=phone,
                subject=subject,
                message=message,
                ip_address=ip_address
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

    # GET request - show contact page with caching
    cache_key = 'contact_page_data_v1'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        product_categories, page_content = cached_data
    else:
        product_categories = ProductCategory.objects.select_related().all()
        page_content = PageSEO.objects.filter(slug='contact').first()
        # Cache for 15 minutes
        cache.set(cache_key, (product_categories, page_content), 900)
    
    # Initialize variables
    rendered_page_content = render_dynamic_content(
        page_content.content1 if page_content and page_content.content1 else "",
        {
            "product_categories": product_categories,
        }
    )
    
    if page_content:
        seo_meta_title = page_content.seo_meta_title
        seo_meta_description = page_content.seo_meta_description
        seo_meta_keywords = ', '.join(page_content.get_seo_keywords_list())
    else:
        seo_meta_title = "Contact Us"
        seo_meta_description = "Get in touch with Arivas Pharma. Contact our pharmaceutical experts for inquiries about our products and services."
        seo_meta_keywords = "contact arivas pharma, pharmaceutical company contact, healthcare contact, medicine inquiry"
    
    return render(request, 'pages/contact.html', {
        'product_categories': product_categories,
        'seo_meta_title': seo_meta_title,
        'seo_meta_description': seo_meta_description,
        'seo_meta_keywords': seo_meta_keywords,
        'rendered_page_content': rendered_page_content,
    })
@csrf_exempt
def enquiry(request):
    cache_key = 'enquiry_page_data_v1'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        product_categories, page_content = cached_data
    else:
        product_categories = ProductCategory.objects.select_related().all()
        page_content = PageSEO.objects.filter(slug='enquiry').first()
        # Cache for 15 minutes
        cache.set(cache_key, (product_categories, page_content), 900)
    
    if page_content:
        seo_meta_title = page_content.seo_meta_title
        seo_meta_description = page_content.seo_meta_description
        seo_meta_keywords = ', '.join(page_content.get_seo_keywords_list())
        content1 = page_content.content1 if page_content else ""
        content2 = page_content.content2 if page_content else ""
        content3 = page_content.content3 if page_content else ""
        content4 = page_content.content4 if page_content else ""
        content5 = page_content.content5 if page_content else ""
    else:
        seo_meta_title = "Enquiry Form"
        seo_meta_description = "Submit your enquiry to Arivas Pharma. Our team is ready to assist you with product information and support."
        seo_meta_keywords = "enquiry arivas pharma, pharmaceutical enquiry, medicine inquiry form"
        content1 = content2 = content3 = content4 = content5 = ""
    
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
    
    # Get latest products for sidebar with optimized query
    latest_products = Product.objects.select_related('category', 'status').order_by('-created_at')[:6]
    
    context = {
        'product_categories': product_categories,
        'prefilled_sku': sku,
        'latest_products': latest_products,
        'seo_meta_title': seo_meta_title,
        'seo_meta_description': seo_meta_description,
        'seo_meta_keywords': seo_meta_keywords,
        'content1': content1,
        'content2': content2,
        'content3': content3,
        'content4': content4,
        'content5': content5,
    }
    
    return render(request, 'pages/enquiry.html', context)

@cache_control(max_age=1800)  # Cache for 30 minutes
def products(request):
    cache_key = 'products_page_data_v1'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        product_categories, products, page_content = cached_data
    else:
        product_categories = ProductCategory.objects.select_related().all()
        products = Product.objects.select_related('category', 'status').prefetch_related('category').all()
        page_content = PageSEO.objects.filter(slug='products').first()
        # Cache for 15 minutes
        cache.set(cache_key, (product_categories, products, page_content), 900)
    
    seo_meta_title = page_content.seo_meta_title if page_content else "Products"
    seo_meta_description = page_content.seo_meta_description if page_content else "Explore our wide range of pharmaceutical products at Arivas Pharma. Quality medicines for healthcare professionals and patients."
    seo_meta_keywords = ', '.join(page_content.get_seo_keywords_list()) if page_content else "Products, Pharmaceuticals, Healthcare"
    
    return render(request, 'pages/products.html', {
        'product_categories': product_categories,
        'products': products,
        'seo_meta_title': seo_meta_title,
        'seo_meta_description': seo_meta_description,
        'seo_meta_keywords': seo_meta_keywords,
    })


@cache_control(max_age=1800)  # Cache for 30 minutes
def category_products(request, category_slug):
    cache_key = f'category_products_{category_slug}_v1'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        product_categories, category, products = cached_data
    else:
        product_categories = ProductCategory.objects.select_related().all()
        category = get_object_or_404(ProductCategory, slug=category_slug)
        products = Product.objects.select_related('category', 'status').filter(category=category)
        # Cache for 15 minutes
        cache.set(cache_key, (product_categories, category, products), 900)
    
    seo_meta_title = category.seo_meta_title or category.name
    seo_meta_description = category.seo_meta_description or category.description
    seo_meta_keywords = ', '.join(category.get_seo_keywords_list()) if hasattr(category, 'get_seo_keywords_list') else "Default, Keywords"
    
    return render(request, 'pages/category_products.html', {
        'product_categories': product_categories,
        'products': products,
        'category': category,
        'seo_meta_title': seo_meta_title,
        'seo_meta_description': seo_meta_description,
        'seo_meta_keywords': seo_meta_keywords,
    })

@cache_control(max_age=3600)  # Cache for 1 hour
def product_in_category(request, category_slug, product_slug):
    cache_key = f'product_{category_slug}_{product_slug}_v1'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        product_categories, product = cached_data
    else:
        product_categories = ProductCategory.objects.select_related().all()
        product = get_object_or_404(
            Product.objects.select_related('category', 'status'), 
            slug=product_slug, 
            category__slug=category_slug
        )
        # Cache for 30 minutes
        cache.set(cache_key, (product_categories, product), 1800)
    
    seo_meta_title = product.seo_meta_title or product.name
    seo_meta_description = product.seo_meta_description or product.description
    seo_meta_keywords = product.seo_meta_keywords or ''
    
    return render(request, 'pages/individual_products.html', {
        'product_categories': product_categories,
        'product': product,
        'seo_meta_title': seo_meta_title,
        'seo_meta_description': seo_meta_description,
        'seo_meta_keywords': seo_meta_keywords,
    })

@cache_control(max_age=1800)  # Cache for 30 minutes
def blog(request):
    cache_key = 'blog_page_data_v1'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        product_categories, blog_posts, blog_categories, page_content = cached_data
    else:
        product_categories = ProductCategory.objects.select_related().all()
        blog_posts = BlogPost.objects.filter(status='published').select_related('category').order_by('-published_date')
        blog_categories = BlogCategory.objects.all()
        page_content = PageSEO.objects.filter(slug='blog').first()
        # Cache for 15 minutes
        cache.set(cache_key, (product_categories, blog_posts, blog_categories, page_content), 900)
    
    seo_meta_title = page_content.seo_meta_title if page_content else "Blog"
    seo_meta_description = page_content.seo_meta_description if page_content else "Latest news and articles from Arivas Pharma."
    seo_meta_keywords = ', '.join(page_content.get_seo_keywords_list()) if page_content else "Blog, Articles, News"

    return render(request, 'pages/blog.html', {
        'product_categories': product_categories,
        'blog_posts': blog_posts,
        'blog_categories': blog_categories,
        'seo_meta_title': seo_meta_title,
        'seo_meta_description': seo_meta_description,
        'seo_meta_keywords': seo_meta_keywords,
    })

    

@cache_control(max_age=3600)  # Cache for 1 hour
def individual_blog(request, slug):
    cache_key = f'blog_post_{slug}_v1'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        product_categories, post, related_posts = cached_data
    else:
        product_categories = ProductCategory.objects.select_related().all()
        post = get_object_or_404(BlogPost.objects.select_related('category'), slug=slug, status='published')
        
        # Get related posts from the same category
        related_posts = BlogPost.objects.filter(
            category=post.category, 
            status='published'
        ).exclude(id=post.id).select_related('category').order_by('-published_date')[:3]
        
        # Cache for 30 minutes
        cache.set(cache_key, (product_categories, post, related_posts), 1800)

    seo_meta_title = post.seo_meta_title or post.title
    seo_meta_description = post.seo_meta_description or post.excerpt
    seo_meta_keywords = post.seo_meta_keywords or ''.join(post.get_seo_meta_keywords_list()) if hasattr(post, 'get_seo_meta_keywords_list') else ''
    
    return render(request, 'pages/individual_blog.html', {
        'product_categories': product_categories,
        'post': post,
        'related_posts': related_posts,
        'seo_meta_title': seo_meta_title,
        'seo_meta_description': seo_meta_description,
        'seo_meta_keywords': seo_meta_keywords,
    })

@cache_control(max_age=1800)  # Cache for 30 minutes
def blog_category(request, category_slug):
    cache_key = f'blog_category_{category_slug}_v1'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        product_categories, blog_category, blog_posts, blog_categories = cached_data
    else:
        product_categories = ProductCategory.objects.select_related().all()
        blog_category = get_object_or_404(BlogCategory, slug=category_slug)
        blog_posts = BlogPost.objects.filter(
            category=blog_category, 
            status='published'
        ).select_related('category').order_by('-published_date')
        blog_categories = BlogCategory.objects.all()
        # Cache for 15 minutes
        cache.set(cache_key, (product_categories, blog_category, blog_posts, blog_categories), 900)
    
    return render(request, 'pages/blog.html', {
        'product_categories': product_categories,
        'blog_posts': blog_posts,
        'blog_categories': blog_categories,
        'selected_category': blog_category,
    })

@cache_control(max_age=1800)  # Cache for 30 minutes
def price_list(request):
    cache_key = 'price_list_page_data_v1'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        product_categories, price_list_obj, page_content = cached_data
    else:
        product_categories = ProductCategory.objects.select_related().all()
        # Get the active price list
        price_list_obj = PriceList.objects.filter(is_active=True).first()
        page_content = PageSEO.objects.filter(slug='price-list').first()
        # Cache for 15 minutes
        cache.set(cache_key, (product_categories, price_list_obj, page_content), 900)
    
    seo_meta_title = page_content.seo_meta_title if page_content else "Price List"
    seo_meta_description = page_content.seo_meta_description if page_content else "Description for Price List"
    seo_meta_keywords = ', '.join(page_content.get_seo_keywords_list()) if page_content else "Price, List"

    return render(request, 'pages/price_list.html', {
        'product_categories': product_categories,
        'price_list': price_list_obj,
        'seo_meta_title': seo_meta_title,
        'seo_meta_description': seo_meta_description,
        'seo_meta_keywords': seo_meta_keywords,
    })

@require_GET
@cache_control(max_age=1800)  # Cache for 30 minutes
def api_products(request):
    cache_key = 'api_products_v1'
    data = cache.get(cache_key)
    
    if data is None:
        products = Product.objects.select_related('category', 'status').all()
        data = []
        for p in products:
            data.append({
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
            })
        # Cache for 15 minutes
        cache.set(cache_key, data, 900)
    
    return JsonResponse(data, safe=False)

@require_GET
@cache_control(max_age=3600)  # Cache for 1 hour
def api_categories(request):
    cache_key = 'api_categories_v1'
    data = cache.get(cache_key)
    
    if data is None:
        categories = ProductCategory.objects.all()
        data = [{'id': c.id, 'name': c.name, 'slug': c.slug} for c in categories]
        # Cache for 30 minutes
        cache.set(cache_key, data, 1800)
    
    return JsonResponse(data, safe=False)

@require_GET
@cache_control(max_age=1800)  # Cache for 30 minutes
def api_blog_posts(request):
    cache_key = 'api_blog_posts_v1'
    data = cache.get(cache_key)
    
    if data is None:
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
                'tags': post.get_tags_list() if hasattr(post, 'get_tags_list') else [],
            })
        # Cache for 15 minutes
        cache.set(cache_key, data, 900)
    
    return JsonResponse(data, safe=False)

@require_GET
@cache_control(max_age=3600)  # Cache for 1 hour
def api_blog_categories(request):
    cache_key = 'api_blog_categories_v1'
    data = cache.get(cache_key)
    
    if data is None:
        categories = BlogCategory.objects.all()
        data = [{'id': c.id, 'name': c.name, 'slug': c.slug} for c in categories]
        # Cache for 30 minutes
        cache.set(cache_key, data, 1800)
    
    return JsonResponse(data, safe=False)


