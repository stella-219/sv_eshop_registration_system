
from django.shortcuts import get_object_or_404, render,redirect
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from django.db import transaction
from .models import Products, Rating, GeneralMerchandise, FoodBeverage, User, Admin, Customer
from .forms import ProductForm, SignInForm, SignUpForm

# Product List View (Class-Based)
class ProductListView(ListView):
    model = Products
    template_name = 'HomePage.html'
    context_object_name = 'products'

def get_star_range(rating_score):
    return range(1, rating_score + 1)

# Product Detail View (Class-Based)
class ProductDetailView(DetailView):
    model = Products
    template_name = 'ProductDetail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        # Add product ratings to the context for the product detail page
        context = super().get_context_data(**kwargs)
        product_ratings = Rating.objects.filter(product=self.object)

        # Add pre-calculated star ranges to ratings
        ratings_with_stars = [
            {
                "comments": rating.comments,
                "rate_score": rating.rate_score,
                "stars": range(1, rating.rate_score + 1),
            }
            for rating in product_ratings
        ]

        context['product_ratings'] = ratings_with_stars

        # Dynamically set the quantity range based on quantity_available
        max_purchase_limit = 20  # Maximum limit for purchase
        quantity_available = self.object.quantity_available or 0  # Fallback to 0 if None
        context['quantity_range'] = range(1, min(max_purchase_limit, quantity_available) + 1)

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


# Updated Product Delete View
def Product_Delete(request, product_id):
    if request.method == 'POST':
        # Get the product
        product = get_object_or_404(Products, pk=product_id)

        # Determine product category and delete from the respective table
        if product.category == 'food_beverage':
            FoodBeverage.objects.filter(product=product).delete()
        elif product.category == 'general_merchandise':
            GeneralMerchandise.objects.filter(product=product).delete()

        # Delete the product from the Products table
        product.delete()

        return JsonResponse({'success': True})

    return JsonResponse({'error': 'Invalid request'}, status=400)


def sign_in(request):
    """
    Handles user sign-in functionality. Identifies whether the user is an admin or customer
    and redirects them to the homepage while storing their role in the session.
    """
    if request.method == 'POST':
        form = SignInForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                # Authenticate user by checking username and password
                user = User.objects.get(email_address=email, password=password)

                # Determine the user's role
                if Customer.objects.filter(user=user).exists():
                    user_role = 'customer'
                elif Admin.objects.filter(user=user).exists():
                    user_role = 'admin'
                else:
                    user_role = 'unknown'

                # Store user info in session
                request.session['user_id'] = user.user_id
                request.session['user_role'] = user_role

                # Redirect to the homepage
                return redirect('home')  # Replace with the name of your homepage URL pattern

            except User.DoesNotExist:
                # Invalid username or password
                return render(request, 'SignIn.html', {
                    'form': form,
                    'errorMessage': 'Invalid username or password'
                })

        else:
            # Form validation errors
            return render(request, 'SignIn.html', {
                'form': form,
                'errorMessage': 'Please correct the errors below.'
            })

    else:
        # Handle GET request
        form = SignInForm()

    return render(request, 'SignIn.html', {'form': form})


def sign_up(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user_type = form.cleaned_data['userType']
            user_name = form.cleaned_data['User_Name']
            password = form.cleaned_data['Password']
            email = form.cleaned_data['Email_Address']
            phone = form.cleaned_data.get('Phone_Number', None)

            try:
                with transaction.atomic():  # Wrap the database operations in a transaction
                    # Create a new User
                    user = User.objects.create(
                        user_name=user_name,
                        password=password,
                        email_address=email,
                        phone_number=phone,
                    )

                    # Create Customer or Admin record
                    if user_type == 'customer':
                        bank_account = form.cleaned_data.get('Bank_Account', None)
                        home_address = form.cleaned_data.get('Home_Address', None)
                        Customer.objects.create(
                            user=user,
                            bank_account=bank_account,
                            home_address=home_address,
                        )
                    elif user_type == 'admin':
                        Admin.objects.create(user=user)

                    # Redirect to HomePage after successful sign-up
                    return redirect('home')

            except Exception as e:
                form.add_error(None, f"An error occurred: {str(e)}")
    else:
        form = SignUpForm()

    return render(request, 'SignUp.html', {'form': form})


def edit_product(request, product_id):
    product = get_object_or_404(Products, pk=product_id)
    food_beverage = None
    general_merchandise = None

    if product.category == "FOOD_BEVERAGE":
        food_beverage = FoodBeverage.objects.filter(product=product).first()
    elif product.category == "GENERAL_MERCHANDISE":
        general_merchandise = GeneralMerchandise.objects.filter(product=product).first()

    if request.method == 'POST':
        # Update product attributes
        product.proname = request.POST['proname']
        product.brand = request.POST['brand']
        product.cost = request.POST['cost']
        product.price = request.POST['price']
        product.prodescription = request.POST['prodescription']
        product.category = request.POST['category']
        product.save()

        # Update category-specific fields
        if product.category == "FOOD_BEVERAGE" and food_beverage:
            food_beverage.sell_by = request.POST['sell_by']
            food_beverage.save()
        elif product.category == "GENERAL_MERCHANDISE" and general_merchandise:
            general_merchandise.color = request.POST['color']
            general_merchandise.save()

        return redirect('home')  # Redirect back to the Home page

    return render(request, 'ProductEdit.html', {
        'product': product,
        'food_beverage': food_beverage,
        'general_merchandise': general_merchandise,
    })
