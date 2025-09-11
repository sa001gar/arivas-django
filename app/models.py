from django.db import models
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from django.utils.text import slugify
from django_summernote.fields import SummernoteTextField
from django.utils import timezone
from django.db.models import Count, Sum
# from .fixsummernote import CleanSummernoteTextField as SummernoteTextField

# Create your models here.

class Feature_Blocks(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    icon = models.CharField(max_length=100)  # Assuming you store icon class names or paths
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Feature Block"
        verbose_name_plural = "Feature Blocks"
        ordering = ['title']


class ProductCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=100, blank=True, null=True)  # Assuming you store icon class names or paths
    seo_meta_name = models.CharField(max_length=100, blank=True, null=True)
    seo_meta_description = models.TextField(blank=True, null=True)
    seo_meta_keywords = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Product Category"
        verbose_name_plural = "Product Categories"
        ordering = ['name']


class Product(models.Model):
    """
    Represents a product in the catalog with name, description, rich content, image, category, and status.
    Fields:
        name (CharField): The name of the product.
        slug (SlugField): URL-friendly unique identifier, auto-generated from name if blank.
        description (TextField): Short description of the product.
        content (SummernoteTextField): Rich text content for detailed product information.
        category (ForeignKey): Reference to the product's category.
        image (ImageField): Product image, auto-cropped to square on save.
        status (ForeignKey): Current status of the product (e.g., available, out of stock).
        created_at (DateTimeField): Timestamp when the product was created.
        updated_at (DateTimeField): Timestamp when the product was last updated.
    """
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)  # Allow blank so it can be auto-filled
    description = models.TextField(help_text="Short description for Page Preview")
    content=SummernoteTextField()  # Rich text with Summernote
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products')
    image = models.ImageField(upload_to='products/')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if self.image:
            img = Image.open(self.image)
            min_dim = min(img.size)
            left = (img.width - min_dim) // 2
            top = (img.height - min_dim) // 2
            right = left + min_dim
            bottom = top + min_dim
            img = img.crop((left, top, right, bottom))
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)
            self.image.save(self.image.name, ContentFile(buffer.read()), save=False)
        super().save(*args, **kwargs)

    status = models.ForeignKey('ProductStatus', on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['name']

class ProductStatus(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Product Status"
        verbose_name_plural = "Product Statuses"
        ordering = ['name']

class BlogCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Blog Category"
        verbose_name_plural = "Blog Categories"
        ordering = ['name']

class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    excerpt = models.TextField(max_length=300, help_text="Brief description for preview")
    content = SummernoteTextField()  # Rich text with Summernote
    category = models.ForeignKey(BlogCategory, on_delete=models.CASCADE, related_name='posts')
    featured_image = models.ImageField(upload_to='blog/', blank=True, null=True)
    author = models.CharField(max_length=100)
    published_date = models.DateTimeField()
    is_featured = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ], default='draft')
    tags = models.CharField(max_length=200, blank=True, help_text="Comma-separated tags")
    meta_description = models.CharField(max_length=160, blank=True, help_text="SEO meta description")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_tags_list(self):
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    class Meta:
        verbose_name = "Blog Post"
        verbose_name_plural = "Blog Posts"
        ordering = ['-published_date']

class PriceList(models.Model):
    title = models.CharField(max_length=200, default="Price List")
    pdf_file = models.FileField(upload_to='price_lists/', help_text="Upload price list PDF")
    version = models.CharField(max_length=50, help_text="Version number (e.g., v1.0, 2024-Q1)")
    description = models.TextField(blank=True, help_text="Brief description of this price list")
    is_active = models.BooleanField(default=True, help_text="Only one price list should be active")
    upload_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.is_active:
            # Set all other price lists to inactive
            PriceList.objects.exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.version}"

    class Meta:
        verbose_name = "Price List"
        verbose_name_plural = "Price Lists"
        ordering = ['-upload_date']

class AboutPage(models.Model):
    seo_meta_name = models.CharField(max_length=100, blank=True, null=True)
    seo_meta_description = models.TextField(blank=True, null=True)
    seo_meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Comma-separated SEO keywords"
    )

    content1 = models.TextField(help_text="Main content section 1")
    content2 = models.TextField(help_text="Main content section 2")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "About Page Content"

    def get_seo_keywords_list(self):
        """
        Returns the SEO keywords as a list, split by commas.
        """
        if self.seo_meta_keywords:
            return [kw.strip() for kw in self.seo_meta_keywords.split(',') if kw.strip()]
        return []

    class Meta:
        verbose_name = "About Page"
        verbose_name_plural = "About Page"
        ordering = ['-updated_at']

# Analytics Models
class PageVisit(models.Model):
    page_url = models.CharField(max_length=255)
    page_title = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True, null=True)
    visit_date = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = "Page Visit"
        verbose_name_plural = "Page Visits"
        ordering = ['-visit_date']
    
    def __str__(self):
        return f"{self.page_title} - {self.visit_date.strftime('%Y-%m-%d %H:%M')}"

class ProductView(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='views')
    ip_address = models.GenericIPAddressField()
    view_date = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = "Product View"
        verbose_name_plural = "Product Views"
        ordering = ['-view_date']
    
    def __str__(self):
        return f"{self.product.name} - {self.view_date.strftime('%Y-%m-%d %H:%M')}"

class BlogPostView(models.Model):
    blog_post = models.ForeignKey(BlogPost, on_delete=models.CASCADE, related_name='views')
    ip_address = models.GenericIPAddressField()
    view_date = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = "Blog Post View"
        verbose_name_plural = "Blog Post Views"
        ordering = ['-view_date']
    
    def __str__(self):
        return f"{self.blog_post.title} - {self.view_date.strftime('%Y-%m-%d %H:%M')}"

class ContactFormSubmission(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    ip_address = models.GenericIPAddressField()
    submitted_date = models.DateTimeField(auto_now_add=True)
    is_responded = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Contact Form Submission"
        verbose_name_plural = "Contact Form Submissions"
        ordering = ['-submitted_date']
    
    def __str__(self):
        return f"{self.name} - {self.subject}"
    
class Page(models.Model):
    url = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    content = models.TextField(help_text="Content of the page")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Page"
        verbose_name_plural = "Pages"
        ordering = ['title']