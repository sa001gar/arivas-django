from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.core import serializers
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta
from .models import (
    ProductCategory, Product, ProductStatus, BlogPost, BlogCategory, 
    PriceList, ContactFormSubmission, PageSEO, Enquiry
)

from django.template import Template, Context
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django.views.decorators.cache import cache_page
from django.utils.html import strip_tags

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

@cache_page(60 * 15)  # Cache for 15 minutes
def home(request):
    # Prefetch related data to reduce queries
    product_categories = ProductCategory.objects.select_related().prefetch_related('products')
    page_content = PageSEO.objects.filter(slug='home').first()
    
    try:
        # Use select_related to join with category in a single query
        best_selling = ProductStatus.objects.get(slug='best-selling')
        best_selling_products = Product.objects.select_related('category', 'status').filter(
            status=best_selling
        ).order_by('-created_at')[:12]
    except ProductStatus.DoesNotExist:
        best_selling_products = Product.objects.none()

    if page_content:
        seo_meta_title = page_content.seo_meta_title or ""
        seo_meta_description = page_content.seo_meta_description or ""
        seo_meta_keywords = ', '.join(page_content.get_seo_keywords_list())
        content1 = page_content.content1 or ""
        content2 = page_content.content2 or ""
        content3 = page_content.content3 or ""
        content4 = page_content.content4 or ""
        content5 = page_content.content5 or ""
    else:
        seo_meta_title = ""
        seo_meta_description = ""
        seo_meta_keywords = ""
        content1 = content2 = content3 = content4 = content5 = ""

    # Use select_related for category and limit fields if possible
    new_products = Product.objects.select_related('category').only(
        'id', 'name', 'slug', 'description', 'image', 'created_at', 'category__name', 'category__slug'
    ).order_by('-created_at')[:12]

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

@cache_page(60 * 15)  # Cache for 15 minutes
def about(request):
    # Use select_related/prefetch_related to optimize queries
    product_categories = ProductCategory.objects.select_related().prefetch_related('products')
    page_content = PageSEO.objects.filter(slug='about').first()
    
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

@cache_page(60 * 15)  # Cache for 15 minutes
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

    # GET request - show contact page
    # Use select_related/prefetch_related to optimize queries
    product_categories = ProductCategory.objects.select_related().prefetch_related('products')
    page_content = PageSEO.objects.filter(slug='contact').first()
    
    # Initialize variables
    if page_content:
        rendered_page_content = render_dynamic_content(
            page_content.content1 if page_content.content1 else "",
            {
                "product_categories": product_categories,
            }
        )
        seo_meta_title = page_content.seo_meta_title or "Contact Us"
        seo_meta_description = page_content.seo_meta_description or "Get in touch with Arivas Pharma. Contact our pharmaceutical experts for inquiries about our products and services."
        seo_meta_keywords = ', '.join(page_content.get_seo_keywords_list())
    else:
        rendered_page_content = ""
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


@cache_page(60 * 15)  # Cache for 15 minutes
@csrf_exempt
def enquiry(request):
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
            
            ip_address = request.META.get('REMOTE_ADDR', '')
            
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
    
    # GET request - show enquiry page
    # Use select_related/prefetch_related to optimize queries
    product_categories = ProductCategory.objects.select_related().prefetch_related('products')
    page_content = PageSEO.objects.filter(slug='enquiry').first()
    
    # Initialize variables
    if page_content:
        rendered_page_content = render_dynamic_content(
            page_content.content1 if page_content.content1 else "",
            {
                "product_categories": product_categories,
            }
        )
        seo_meta_title = page_content.seo_meta_title or "Enquiry Form"
        seo_meta_description = page_content.seo_meta_description or "Submit your enquiry to Arivas Pharma. Our team is ready to assist you with product information and support."
        seo_meta_keywords = ', '.join(page_content.get_seo_keywords_list())
        content1 = page_content.content1 or ""
        content2 = page_content.content2 or ""
        content3 = page_content.content3 or ""
        content4 = page_content.content4 or ""
        content5 = page_content.content5 or ""
    else:
        rendered_page_content = ""
        seo_meta_title = "Enquiry Form"
        seo_meta_description = "Submit your enquiry to Arivas Pharma. Our team is ready to assist you with product information and support."
        seo_meta_keywords = "enquiry arivas pharma, pharmaceutical enquiry, medicine inquiry form"
        content1 = content2 = content3 = content4 = content5 = ""
    
    # Get SKU from URL parameter for prefilling
    sku = request.GET.get('sku', '')
    
    # Get latest products for sidebar with optimized query
    latest_products = Product.objects.select_related('category').only(
        'id', 'name', 'slug', 'description', 'image', 'created_at', 'category__name', 'category__slug'
    ).order_by('-created_at')[:6]
    
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
        'rendered_page_content': rendered_page_content,
    }
    
    return render(request, 'pages/enquiry.html', context)

# @cache_page(60 * 15)  # Cache for 15 minutes
def products(request):
    # Use select_related/prefetch_related to optimize queries
    product_categories = ProductCategory.objects.select_related().prefetch_related('products')
    
    # Optimize products query with select_related and only necessary fields
    products = Product.objects.select_related('category', 'status').only(
        'id', 'name', 'slug', 'description', 'image', 'created_at', 
        'category__name', 'category__slug', 'status__name'
    ).order_by('-created_at')
    
    page_content = PageSEO.objects.filter(slug='products').first()
    
    if page_content:
        seo_meta_title = page_content.seo_meta_title or "Products"
        seo_meta_description = page_content.seo_meta_description or "Explore our wide range of pharmaceutical products at Arivas Pharma. Quality medicines for healthcare professionals and patients."
        seo_meta_keywords = ', '.join(page_content.get_seo_keywords_list())
    else:
        seo_meta_title = "Products"
        seo_meta_description = "Explore our wide range of pharmaceutical products at Arivas Pharma. Quality medicines for healthcare professionals and patients."
        seo_meta_keywords = "Products, Pharmaceuticals, Healthcare"
    
    return render(request, 'pages/products.html', {
        'product_categories': product_categories,
        'products': products,
        'seo_meta_title': seo_meta_title,
        'seo_meta_description': seo_meta_description,
        'seo_meta_keywords': seo_meta_keywords,
    })


@cache_page(60 * 15)  # Cache for 15 minutes
def category_products(request, category_slug):
    # Optimize product_categories query with prefetch_related
    product_categories = ProductCategory.objects.select_related().prefetch_related('products')
    
    # Use get_object_or_404 for better error handling and optimize with select_related
    category = get_object_or_404(ProductCategory.objects.select_related(), slug=category_slug)
    
    # Optimize products query with select_related and only necessary fields
    products = Product.objects.select_related('category', 'status').only(
        'id', 'name', 'slug', 'description', 'image', 'created_at',
        'category__name', 'category__slug', 'status__name'
    ).filter(category=category).order_by('-created_at')
    
    seo_meta_title = category.seo_meta_title or category.name
    seo_meta_description = category.seo_meta_description or category.description
    seo_meta_keywords = ', '.join(category.get_seo_keywords_list()) if category else "Default, Keywords"
    
    return render(request, 'pages/category_products.html', {
        'product_categories': product_categories,
        'products': products,
        'category': category,
        'seo_meta_title': seo_meta_title,
        'seo_meta_description': seo_meta_description,
        'seo_meta_keywords': seo_meta_keywords,
    })

@cache_page(60 * 15)  # Cache for 15 minutes
def product_in_category(request, category_slug, product_slug):
    # Optimize product_categories query with select_related and prefetch_related
    product_categories = ProductCategory.objects.select_related().prefetch_related('products')
    
    # Use get_object_or_404 for better error handling and optimize with select_related
    product = get_object_or_404(
        Product.objects.select_related('category', 'status'),
        slug=product_slug, 
        category__slug=category_slug
    )
    
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

@cache_page(60 * 15)  # Cache for 15 minutes
def blog(request):
    # Optimize product_categories query with select_related and prefetch_related
    product_categories = ProductCategory.objects.select_related().prefetch_related('products')
    
    # Optimize blog_posts query with select_related and only necessary fields
    blog_posts = BlogPost.objects.select_related('category').only(
        'id', 'title', 'slug', 'excerpt', 'author', 'published_date', 
        'is_featured', 'featured_image', 'category__name', 'category__slug'
    ).filter(status='published').order_by('-published_date')
    
    # Only fetch necessary fields for blog_categories
    blog_categories = BlogCategory.objects.only('id', 'name', 'slug').all()
    
    page_content = PageSEO.objects.filter(slug='blog').first()
    
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

@cache_page(60 * 15)  # Cache for 15 minutes
def individual_blog(request, slug):
    # Optimize product_categories query with select_related and prefetch_related
    product_categories = ProductCategory.objects.select_related().prefetch_related('products')
    
    # Use get_object_or_404 with select_related for better performance
    post = get_object_or_404(
        BlogPost.objects.select_related('category'),
        slug=slug, 
        status='published'
    )
    
    # Get related posts from the same category with optimized query
    related_posts = BlogPost.objects.select_related('category').only(
        'id', 'title', 'slug', 'excerpt', 'published_date', 'featured_image',
        'category__name', 'category__slug'
    ).filter(
        category=post.category, 
        status='published'
    ).exclude(id=post.id).order_by('-published_date')[:3]

    seo_meta_title = post.seo_meta_title or post.title
    seo_meta_description = post.seo_meta_description or post.excerpt
    seo_meta_keywords = post.seo_meta_keywords or ', '.join(post.get_tags_list()) if hasattr(post, 'get_tags_list') else ''
    
    return render(request, 'pages/individual_blog.html', {
        'product_categories': product_categories,
        'post': post,
        'related_posts': related_posts,
        'seo_meta_title': seo_meta_title,
        'seo_meta_description': seo_meta_description,
        'seo_meta_keywords': seo_meta_keywords,
    })

@cache_page(60 * 15)  # Cache for 15 minutes
def blog_category(request, category_slug):
    # Optimize product_categories query with select_related and prefetch_related
    product_categories = ProductCategory.objects.select_related().prefetch_related('products')
    
    # Use get_object_or_404 with optimized query
    blog_category = get_object_or_404(BlogCategory.objects.only('id', 'name', 'slug'), slug=category_slug)
    
    # Optimize blog_posts query with select_related and only necessary fields
    blog_posts = BlogPost.objects.select_related('category').only(
        'id', 'title', 'slug', 'excerpt', 'author', 'published_date', 
        'is_featured', 'featured_image', 'category__name', 'category__slug'
    ).filter(
        category=blog_category, 
        status='published'
    ).order_by('-published_date')
    
    # Only fetch necessary fields for blog_categories
    blog_categories = BlogCategory.objects.only('id', 'name', 'slug').all()
    
    seo_meta_title = f"{blog_category.name} - Blog"
    seo_meta_description = f"Read articles about {blog_category.name} from Arivas Pharma blog."
    seo_meta_keywords = f"{blog_category.name}, blog, articles"
    
    return render(request, 'pages/blog.html', {
        'product_categories': product_categories,
        'blog_posts': blog_posts,
        'blog_categories': blog_categories,
        'selected_category': blog_category,
        'seo_meta_title': seo_meta_title,
        'seo_meta_description': seo_meta_description,
        'seo_meta_keywords': seo_meta_keywords,
    })

@cache_page(60 * 15)  # Cache for 15 minutes
def price_list(request):
    # Optimize product_categories query with select_related and prefetch_related
    product_categories = ProductCategory.objects.select_related().prefetch_related('products')
    
    # Get the active price list with optimized query
    price_list = PriceList.objects.only(
        'id', 'title', 'description', 'pdf_file', 'is_active'
    ).filter(is_active=True).first()
    
    page_content = PageSEO.objects.filter(slug='price-list').first()
    
    seo_meta_title = page_content.seo_meta_title if page_content else "Price List"
    seo_meta_description = page_content.seo_meta_description if page_content else "Download our comprehensive price list for pharmaceutical products."
    seo_meta_keywords = ', '.join(page_content.get_seo_keywords_list()) if page_content else "price list, pharmaceutical prices, medicine cost"

    return render(request, 'pages/price_list.html', {
        'product_categories': product_categories,
        'price_list': price_list,
        'seo_meta_title': seo_meta_title,
        'seo_meta_description': seo_meta_description,
        'seo_meta_keywords': seo_meta_keywords,
    })

@cache_page(60 * 5)  # Cache for 5 minutes for API
@require_GET
@csrf_exempt
def api_products(request):
    try:
        # Optimize query with select_related and only necessary fields
        products = Product.objects.select_related('category').only(
            'id', 'name', 'slug', 'description', 'image',
            'category__id', 'category__name', 'category__slug'
        ).all()
        
        data = []
        for p in products:
            data.append({
                'id': p.id,
                'name': strip_tags(p.name),
                'slug': p.slug,
                'description': strip_tags(p.description)[:200] + '...' if len(strip_tags(p.description)) > 200 else strip_tags(p.description),
                'image': p.image.url if p.image else '',
                'category': {
                    'id': p.category.id,
                    'name': strip_tags(p.category.name),
                    'slug': p.category.slug,
                } if p.category else None,
            })
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': 'Unable to fetch products'}, status=500)

@cache_page(60 * 10)  # Cache for 10 minutes for API
@require_GET
@csrf_exempt
def api_categories(request):
    try:
        # Only fetch necessary fields
        categories = ProductCategory.objects.only('id', 'name', 'slug').all()
        data = [{'id': c.id, 'name': c.name, 'slug': c.slug} for c in categories]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': 'Unable to fetch categories'}, status=500)

@cache_page(60 * 5)  # Cache for 5 minutes for API
@require_GET
@csrf_exempt
def api_blog_posts(request):
    try:
        # Optimize query with select_related and only necessary fields
        blog_posts = BlogPost.objects.select_related('category').only(
            'id', 'title', 'slug', 'excerpt', 'author', 'published_date', 
            'is_featured', 'featured_image', 'category__id', 'category__name'
        ).filter(status='published').order_by('-published_date')
        
        data = []
        for post in blog_posts:
            data.append({
                'id': post.id,
                'title': post.title,
                'slug': post.slug,
                'excerpt': post.excerpt[:300] + '...' if len(post.excerpt) > 300 else post.excerpt,  # Limit excerpt length
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
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': 'Unable to fetch blog posts'}, status=500)

@cache_page(60 * 10)  # Cache for 10 minutes for API
@require_GET
@csrf_exempt
def api_blog_categories(request):
    try:
        # Only fetch necessary fields
        categories = BlogCategory.objects.only('id', 'name', 'slug').all()
        data = [{'id': c.id, 'name': c.name, 'slug': c.slug} for c in categories]
        return JsonResponse(data, safe=False)
    except Exception as e:
        return JsonResponse({'error': 'Unable to fetch blog categories'}, status=500)


