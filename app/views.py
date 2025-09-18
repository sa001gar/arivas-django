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

def home(request):
    product_categories = ProductCategory.objects.all()
    page_content = PageSEO.objects.filter(slug='home').first()
    
    try:
        best_selling = ProductStatus.objects.get(slug='best-selling')
        best_selling_products = Product.objects.select_related('category').filter(
            status=best_selling
        ).order_by('-created_at')[:12]
    except ProductStatus.DoesNotExist:
        best_selling_products = Product.objects.none()

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

    new_products = Product.objects.select_related('category').order_by('-created_at')[:12]

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

def about(request):
    product_categories = ProductCategory.objects.all()
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
    product_categories = ProductCategory.objects.all()
    page_content = PageSEO.objects.filter(slug='contact').first()
    
    # Initialize variables
    rendered_page_content = render_dynamic_content(
            page_content.content1,   # assuming Summernote HTML is in `content` field
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
    product_categories = ProductCategory.objects.all()
    page_content = PageSEO.objects.filter(slug='enquiry').first()
    # Initialize variables
    
    
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
        'latest_products': latest_products,
        'seo_meta_title': seo_meta_title,
        'seo_meta_description': seo_meta_description,
        'seo_meta_keywords': seo_meta_keywords,
        'content1': content1,
        'content2': content2,
        'content3': content3,
        'content4': content4,
        'content5': content5,

        # 'rendered_page_content': rendered_page_content,
    }
    
    return render(request, 'pages/enquiry.html', context)

def products(request):
    product_categories = ProductCategory.objects.all()
    products = Product.objects.all()
    page_content = PageSEO.objects.filter(slug='products').first()
    
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


def category_products(request, category_slug):
    product_categories = ProductCategory.objects.all()
    category = ProductCategory.objects.get(slug=category_slug)
    products = Product.objects.select_related('category').filter(category=category)
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

def product_in_category(request, category_slug, product_slug):
    product_categories = ProductCategory.objects.all()
    product = Product.objects.get(slug=product_slug, category__slug=category_slug)
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

def blog(request):
    product_categories = ProductCategory.objects.all()
    blog_posts = BlogPost.objects.filter(status='published').select_related('category').order_by('-published_date')
    blog_categories = BlogCategory.objects.all()
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

    

def individual_blog(request, slug):
    product_categories = ProductCategory.objects.all()
    post = get_object_or_404(BlogPost, slug=slug, status='published')
    
    # Get related posts from the same category
    related_posts = BlogPost.objects.filter(
        category=post.category, 
        status='published'
    ).exclude(id=post.id).order_by('-published_date')[:3]

    seo_meta_title = post.seo_meta_title or post.title
    seo_meta_description = post.seo_meta_description or post.excerpt
    seo_meta_keywords = post.seo_meta_keywords or ''.join(post.get_seo_meta_keywords_list())
    
    return render(request, 'pages/individual_blog.html', {
        'product_categories': product_categories,
        'post': post,
        'related_posts': related_posts,
        'seo_meta_title': seo_meta_title,
        'seo_meta_description': seo_meta_description,
        'seo_meta_keywords': seo_meta_keywords,
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
    page_content = PageSEO.objects.filter(slug='price-list').first()
    
    seo_meta_title = page_content.seo_meta_title if page_content else "Price List"
    seo_meta_description = page_content.seo_meta_description if page_content else "Description for Price List"
    seo_meta_keywords = ', '.join(page_content.get_seo_keywords_list()) if page_content else "Price, List"

    return render(request, 'pages/price_list.html', {
        'product_categories': product_categories,
        'price_list': price_list,
        'seo_meta_title': seo_meta_title,
        'seo_meta_description': seo_meta_description,
        'seo_meta_keywords': seo_meta_keywords,
    })

@require_GET
def api_products(request):
    products = Product.objects.select_related('category').all()
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
    return JsonResponse(data, safe=False)

@require_GET
def api_categories(request):
    categories = ProductCategory.objects.all()
    data = [{'id': c.id, 'name': c.name, 'slug': c.slug} for c in categories]
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


