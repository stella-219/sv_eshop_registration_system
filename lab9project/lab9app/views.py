
from django.shortcuts import get_object_or_404, render,redirect
from django.views.generic import ListView, DetailView
from .models import Products, Rating, GeneralMerchandise, FoodBeverage
from .forms import ProductForm

# Product List View (Class-Based)
class ProductListView(ListView):
    model = Products
    template_name = 'HomePage.html'
    context_object_name = 'products'

# Product Detail View (Class-Based)
class ProductDetailView(DetailView):
    model = Products
    template_name = 'ProductDetail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        # Add product ratings to the context for the product detail page
        context = super().get_context_data(**kwargs)
        context['product_ratings'] = Rating.objects.filter(product=self.object)
        return context


# Product Create View
def Product_Create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the product to the database
            proname = form.cleaned_data['proname']
            brand = form.cleaned_data['brand']
            cost = form.cleaned_data['cost']
            price = form.cleaned_data['price']
            prodescription = form.cleaned_data['prodescription']
            category = form.cleaned_data['category']
            image = form.cleaned_data['image']
            quantity_available = form.cleaned_data['quantity_available']

            # Create the base product
            product = Products.objects.create(
                proname=proname,
                brand=brand,
                cost=cost,
                price=price,
                prodescription=prodescription,
                category=category,
                image=image,
                quantity_available=quantity_available,
            )

            # Save additional fields based on category
            if category == "GENERAL_MERCHANDISE":
                color = form.cleaned_data['color']
                GeneralMerchandise.objects.create(product=product, color=color)
            elif category == "FOOD_BEVERAGE":
                sell_by = form.cleaned_data['sell_by']
                FoodBeverage.objects.create(product=product, sell_by=sell_by)

            return redirect('product_list')
    else:
        form = ProductForm()

    return render(request, 'ProductCreate.html', {'form': form})
