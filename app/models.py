from django.db import models
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from django.utils.text import slugify
from django_summernote.fields import SummernoteTextField
import os

# Create your models here.
class ProductCategory(models.Model):
    """ Product Category model with name, description, slug, icon, and SEO fields """
    name = models.CharField(max_length=100)
    description = models.TextField()
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=100, blank=True, null=True)  # Assuming you store icon class names or paths
    
    """SEO Fields"""
    seo_meta_title = models.CharField(max_length=100, blank=True, null=True)
    seo_meta_description = models.TextField(blank=True, null=True)
    seo_meta_keywords = models.CharField(max_length=255, blank=True, null=True)

    """Timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_seo_keywords_list(self):
        """
        Returns the SEO keywords as a list, split by commas.
        """
        if self.seo_meta_keywords:
            return [kw.strip() for kw in self.seo_meta_keywords.split(',') if kw.strip()]
        return []
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
        sku (CharField): Stock Keeping Unit, unique identifier for the product.
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
    sku = models.CharField(max_length=100,unique=False, help_text="Stock Keeping Unit - unique product identifier")
    slug = models.SlugField(unique=True, blank=True)  # Allow blank so it can be auto-filled
    description =SummernoteTextField()
    content=SummernoteTextField()  # Rich text with Summernote
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products')
    image = models.ImageField(upload_to='products/')

    """SEO Fields"""
    seo_meta_title = models.CharField(max_length=100, blank=True, null=True)
    seo_meta_description = models.CharField(max_length=255, blank=True, null=True)
    seo_meta_keywords = models.CharField(max_length=255, blank=True, null=True, help_text="Comma-separated SEO tags")

    status = models.ForeignKey('ProductStatus', on_delete=models.SET_NULL, null=True, blank=True, related_name='products')

    """Timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        if self.image:
            # Open and crop image
            img = Image.open(self.image)
            min_dim = min(img.size)
            left = (img.width - min_dim) // 2
            top = (img.height - min_dim) // 2
            right = left + min_dim
            bottom = top + min_dim
            img = img.crop((left, top, right, bottom))

            # Convert to JPEG
            buffer = BytesIO()
            img.save(buffer, format='JPEG', quality=85)
            buffer.seek(0)

            # Extract only the filename (not the path)
            filename = os.path.basename(self.image.name)
            self.image.save(filename, ContentFile(buffer.read()), save=False)

        super().save(*args, **kwargs)
        

    def get_seo_tags_list(self):
        """
        Returns the SEO tags as a list, split by commas.
        """
        if self.seo_meta_keywords:
            return [tag.strip() for tag in self.seo_meta_keywords.split(',') if tag.strip()]
        return []

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['name']

class ProductStatus(models.Model):
    name = models.CharField(max_length=100)
    slug=models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

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

    """SEO Fields"""
    seo_meta_title = models.CharField(max_length=100, blank=True, null=True)
    seo_meta_keywords = models.CharField(max_length=200, blank=True, help_text="Comma-separated tags")
    seo_meta_description = models.CharField(max_length=160, blank=True, help_text="SEO meta description")

    """Timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_seo_meta_keywords_list(self):
        return [tag.strip() for tag in self.seo_meta_keywords.split(',') if tag.strip()]

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

    """SEO Fields"""
    seo_meta_title = models.CharField(max_length=100, blank=True, null=True)
    seo_meta_description = models.CharField(max_length=255, blank=True, null=True)
    seo_meta_keywords = models.CharField(max_length=255, blank=True, null=True, help_text="Comma-separated SEO tags")

    """Timestamps"""
    upload_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def get_seo_meta_keywords_list(self):
        if self.seo_meta_keywords:
            return [tag.strip() for tag in self.seo_meta_keywords.split(',') if tag.strip()]
        return []
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

class ContactFormSubmission(models.Model):
    """Contact form submissions from website visitors"""
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    ip_address = models.GenericIPAddressField()
    submitted_date = models.DateTimeField(auto_now_add=True)
    is_responded = models.BooleanField(default=False, help_text="Mark as True when contact has been responded to")
    def __str__(self):
        return f"{self.name} - {self.subject}"
    class Meta:
        verbose_name = "Contact Form Submission"
        verbose_name_plural = "Contact Form Submissions"
        ordering = ['-submitted_date']


class Enquiry(models.Model):
    sku=models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    ip_address = models.GenericIPAddressField()
    submitted_date = models.DateTimeField(auto_now_add=True)
    is_responded = models.BooleanField(default=False, help_text="Mark as True when enquiry has been responded to")

    class Meta:
        verbose_name = "Enquiry"
        verbose_name_plural = "Enquiries"
        ordering = ['-submitted_date']

    def __str__(self):
        return f"{self.name} - {self.subject}"


class PageSEO(models.Model):
    """Custom pages with SEO optimization"""
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    
    """SEO Fields"""
    seo_meta_title = models.CharField(max_length=100, blank=True, null=True)
    seo_meta_description = models.TextField(blank=True, null=True)
    seo_meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Comma-separated SEO keywords"
    )

    """Content Sections"""
    content1 = models.TextField(help_text="Main content section 1")
    content2 = models.TextField(help_text="Main content section 2", blank=True, null=True)
    content3 = models.TextField(help_text="Main content section 3", blank=True, null=True)
    content4 = models.TextField(help_text="Main content section 4", blank=True, null=True)
    content5 = models.TextField(help_text="Main content section 5", blank=True, null=True)

    """Timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_seo_keywords_list(self):
        """
        Returns the SEO keywords as a list, split by commas.
        """
        if self.seo_meta_keywords:
            return [kw.strip() for kw in self.seo_meta_keywords.split(',') if kw.strip()]
        return []

    class Meta:
        verbose_name = "Page SEO"
        verbose_name_plural = "Pages SEO"
        ordering = ['-updated_at']
