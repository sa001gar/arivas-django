from django.shortcuts import render, get_object_or_404
from .models import ProductCategory, Feature_Blocks, Product, ProductStatus, BlogPost, BlogCategory, PriceList, AboutPage, PageVisit, ProductView, BlogPostView, ContactFormSubmission
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core import serializers
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import user_passes_test

# Create your views here.

def home(request):
    product_categories = ProductCategory.objects.all()
    feature_blocks = Feature_Blocks.objects.all()
    new_products = Product.objects.order_by('-created_at')[:12]
    

    return render(request, 'pages/home.html', { 'product_categories': product_categories, 'feature_blocks': feature_blocks, 'new_products': new_products})

def about(request):
    product_categories = ProductCategory.objects.all()
    about_page= AboutPage.objects.first()
    return render(request, 'pages/about.html', {'about_page': about_page, 'product_categories': product_categories})

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

# Analytics and Dashboard Functions
def get_analytics_data():
    """Get analytics data for dashboard"""
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)
    
    # Basic counts
    total_products = Product.objects.count()
    total_categories = ProductCategory.objects.count()
    total_blog_posts = BlogPost.objects.filter(status='published').count()
    total_page_visits = PageVisit.objects.count()
    
    # Recent activity
    recent_visits_7_days = PageVisit.objects.filter(visit_date__gte=last_7_days).count()
    recent_visits_30_days = PageVisit.objects.filter(visit_date__gte=last_30_days).count()
    
    # Most viewed products
    popular_products = Product.objects.annotate(
        view_count=Count('views')
    ).order_by('-view_count')[:5]
    
    # Most viewed blog posts
    popular_blog_posts = BlogPost.objects.filter(status='published').annotate(
        view_count=Count('views')
    ).order_by('-view_count')[:5]
    
    # Recent contact submissions
    recent_contacts = ContactFormSubmission.objects.filter(
        submitted_date__gte=last_7_days
    ).count()
    
    # Page views by day (last 7 days)
    daily_visits = []
    for i in range(7):
        day = today - timedelta(days=i)
        visits = PageVisit.objects.filter(visit_date__date=day).count()
        daily_visits.append({
            'date': day.strftime('%Y-%m-%d'),
            'visits': visits
        })
    
    daily_visits.reverse()  # Show oldest to newest
    
    # Category performance
    category_stats = ProductCategory.objects.annotate(
        product_count=Count('products'),
        total_views=Count('products__views')
    ).order_by('-total_views')[:5]
    
    return {
        'total_products': total_products,
        'total_categories': total_categories,
        'total_blog_posts': total_blog_posts,
        'total_page_visits': total_page_visits,
        'recent_visits_7_days': recent_visits_7_days,
        'recent_visits_30_days': recent_visits_30_days,
        'popular_products': popular_products,
        'popular_blog_posts': popular_blog_posts,
        'recent_contacts': recent_contacts,
        'daily_visits': daily_visits,
        'category_stats': category_stats,
    }

@staff_member_required
def admin_dashboard_data(request):
    """API endpoint for admin dashboard data"""
    data = get_analytics_data()
    
    # Convert querysets to serializable data
    data['popular_products'] = [
        {
            'id': p.id,
            'name': p.name,
            'view_count': p.view_count,
            'category': p.category.name if p.category else 'No Category'
        }
        for p in data['popular_products']
    ]
    
    data['popular_blog_posts'] = [
        {
            'id': p.id,
            'title': p.title,
            'view_count': p.view_count,
            'category': p.category.name if p.category else 'No Category'
        }
        for p in data['popular_blog_posts']
    ]
    
    data['category_stats'] = [
        {
            'id': c.id,
            'name': c.name,
            'product_count': c.product_count,
            'total_views': c.total_views
        }
        for c in data['category_stats']
    ]
    
    return JsonResponse(data)

def track_page_visit(request, page_title="", page_url=""):
    """Track page visits for analytics"""
    if not page_url:
        page_url = request.path
    
    # Get client IP
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    # Create page visit record
    PageVisit.objects.create(
        page_url=page_url,
        page_title=page_title,
        ip_address=ip,
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        referrer=request.META.get('HTTP_REFERER'),
        session_id=request.session.session_key or ''
    )

def track_product_view(request, product):
    """Track product views for analytics"""
    # Get client IP
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    # Create product view record
    ProductView.objects.create(
        product=product,
        ip_address=ip,
        session_id=request.session.session_key or ''
    )

def track_blog_view(request, blog_post):
    """Track blog post views for analytics"""
    # Get client IP
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    # Create blog view record
    BlogPostView.objects.create(
        blog_post=blog_post,
        ip_address=ip,
        session_id=request.session.session_key or ''
    )