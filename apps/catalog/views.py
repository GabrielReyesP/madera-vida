"""
apps/catalog/views.py
Vistas publicas: home, listado de productos con filtro, detalle.
(RF-01, RF-02, RF-03)
"""

from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from apps.core.models import CompanyInfo

from .models import Category, Product


def home(request):
    company = CompanyInfo.get_solo()
    featured_products = Product.objects.filter(
        is_active=True, stock__gt=0
    ).select_related('category').order_by('-created_at')[:8]
    categories = Category.objects.all()

    context = {
        'company': company,
        'featured_products': featured_products,
        'categories': categories,
    }
    return render(request, 'catalog/home.html', context)


def product_list(request):
    products = Product.objects.filter(is_active=True).select_related('category')
    categories = Category.objects.all()

    category_slug = request.GET.get('categoria')
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=selected_category)

    query = request.GET.get('q', '').strip()
    if query:
        products = products.filter(name__icontains=query)

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': selected_category,
        'query': query,
    }
    return render(request, 'catalog/product_list.html', context)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related('category'), slug=slug, is_active=True,
    )
    related_products = Product.objects.filter(
        category=product.category, is_active=True,
    ).exclude(pk=product.pk)[:4]

    context = {
        'product': product,
        'related_products': related_products,
    }
    return render(request, 'catalog/product_detail.html', context)
