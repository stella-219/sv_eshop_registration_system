
from django.shortcuts import get_object_or_404, render,redirect
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from django.db import transaction
from .models import Products, Rating, GeneralMerchandise, FoodBeverage, User, Admin, Customer, OrderItem, Orders
from .forms import ProductForm, SignInForm, SignUpForm
import openai
import json
import datetime
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

# Configure your OpenAI API key
openai.api_key = 'sk-PBT3YDS6b-ezRLY_ScAe6ffk5FjtAxZV6mU5oKyq7hT3BlbkFJD587NH6VbXDkMXc6_TBnbCe9-xuCsUkNhTM6iAa9EA'


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
                user_role = 'customer' if Customer.objects.filter(user=user).exists() else 'admin'

                # Store user info in session
                request.session['user_id'] = user.user_id
                request.session['user_role'] = user_role
                request.session['user_name'] = user.user_name

                # Redirect to the next URL or home
                next_url = request.GET.get('next', 'home')  # Default to home if no next URL
                return redirect(next_url)

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

def sign_out(request):
    """
    Clears the session data and redirects to the home page.
    """
    request.session.flush()  # Remove all session data
    return redirect('home')  # Redirect to the main page

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


def chatbox(request):
    return render(request, 'chat.html')

#Query in ChatGPT
@csrf_exempt
def chat_with_gpt(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "").lower()

            print(f"Received message: {user_message}")  # Debugging statement

            if "get products" in user_message:
                products = Products.objects.all()
                if products.exists():
                    product_list = "\n".join([
                        f"- {product.proname} (${product.price})" for product in products
                    ])
                    return JsonResponse(
                        {"response": f"Here are the available products:\n{product_list}"},
                        status=200
                    )
                else:
                    return JsonResponse(
                        {"response": "No products are available at the moment."},
                        status=200
                    )

                    # Handle specific product queries
            if "get product" in user_message:
                product_name = user_message.replace("get product", "").strip()
                product = Products.objects.filter(proname__icontains=product_name).first()
                if product:
                    return JsonResponse(
                        {
                            "response": f"Product: {product.proname}\nPrice: ${product.price}\nDescription: {product.prodescription}"},
                        status=200
                    )
                else:
                    return JsonResponse(
                        {"response": f"No product found matching '{product_name}'."},
                        status=200
                    )


            print(f"Received message: {user_message}")  # Debugging statement

            # Handle getting orders for a specific user ID
            if "get order history of user id:" in user_message:
                # Extract the user ID after "user id:"
                try:
                    user_id_str = user_message.split("user id:")[1].strip()
                    user_id = int(user_id_str)
                except (IndexError, ValueError):
                    return JsonResponse(
                        {"response": "Invalid format. Use 'get order of user id: <user_id>' to fetch order history."},
                        status=400
                    )

                # Fetch orders for the user
                orders = Orders.objects.filter(user_id=user_id).prefetch_related('orderitem_set__product')
                if orders.exists():
                    order_history = []
                    for order in orders:
                        items = order.orderitem_set.all()
                        item_details = "\n".join([
                            f"    - {item.product.proname} (Quantity: {item.quantity})"
                            for item in items
                        ])
                        order_history.append(
                            f"Order ID: {order.order_id}\nItems:\n{item_details}"
                        )

                    history = "\n\n".join(order_history)
                    return JsonResponse(
                        {"response": f"Here is the order history for user ID {user_id}:\n\n{history}"},
                        status=200
                    )
                else:
                    return JsonResponse(
                        {"response": f"No orders found for user ID {user_id}."},
                        status=200
                    )

            # Handle "get all products with rating 5"
            if "get all products with rating 5" in user_message:
                # Fetch products with a rating of 5
                products = Products.objects.filter(rating__rate_score=5).distinct()
                if products.exists():
                    product_list = "\n".join([
                        f"- {product.proname} (${product.price})"
                        for product in products
                    ])
                    return JsonResponse(
                        {"response": f"Products with a rating of 5:\n{product_list}"},
                        status=200
                    )
                else:
                    return JsonResponse(
                        {"response": "No products found with a rating of 5."},
                        status=200
                    )

            # Handle "get the user information of user id"
            if "get the user information of user id:" in user_message:
                # Extract the user ID after "user id:"
                try:
                    user_id_str = user_message.split("user id:")[1].strip()
                    user_id = int(user_id_str)
                except (IndexError, ValueError):
                    return JsonResponse(
                        {"response": "Invalid format. Use 'get the user information of user id: <user_id>'."},
                        status=400
                    )

                # Fetch user information
                try:
                    user = User.objects.get(user_id=user_id)
                    user_info = {
                        "User ID": user.user_id,
                        "Name": user.user_name,
                        "Email": user.email_address,
                        "Phone": user.phone_number,
                    }
                    response = "\n".join([f"{key}: {value}" for key, value in user_info.items()])
                    return JsonResponse({"response": f"User Information:\n{response}"}, status=200)
                except User.DoesNotExist:
                    return JsonResponse(
                        {"response": f"No user found with ID {user_id}."},
                        status=200
                    )

            # Handle "get all orders on <date>" or variations
            if "get the all orders on" in user_message or "get all orders on" in user_message:
                # Extract the date from the message
                try:
                    if "get the all orders on" in user_message:
                        date_str = user_message.split("get the all orders on")[1].strip()
                    else:
                        date_str = user_message.split("get all orders on")[1].strip()

                    order_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                except (IndexError, ValueError):
                    return JsonResponse(
                        {"response": "Invalid format. Use 'get all orders on <YYYY-MM-DD>' to fetch orders."},
                        status=400
                    )

                # Fetch orders for the specified date
                orders = Orders.objects.filter(order_date__date=order_date).prefetch_related(
                    'orderitem_set__product')
                if orders.exists():
                    order_list = []
                    for order in orders:
                        items = order.orderitem_set.all()
                        item_details = "\n".join([
                            f"    - {item.product.proname} (Quantity: {item.quantity})"
                            for item in items
                        ])
                        order_list.append(
                            f"Order ID: {order.order_id}\nItems:\n{item_details}"
                        )

                    response = "\n\n".join(order_list)
                    return JsonResponse(
                        {"response": f"Orders on {order_date}:\n\n{response}"},
                        status=200
                    )
                else:
                    return JsonResponse(
                        {"response": f"No orders found on {order_date}."},
                        status=200
                    )

            # Default ChatGPT response
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": user_message},
                ]
            )
            gpt_response = response['choices'][0]['message']['content']
            return JsonResponse({"response": gpt_response}, status=200)
        except Exception as e:
            print(f"Error: {e}")  # Debugging statement
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request method"}, status=400)



def add_to_order(request, product_id):
    if request.method == "POST":
        # Retrieve quantity from the form
        quantity = int(request.POST.get("quantity", 1))  # Default to 1 if no quantity is provided
        user_id = request.session.get('user_id')  # Retrieve user_id from session
        
        print(f"Product ID: {product_id}, Quantity: {quantity}, User ID: {user_id}")

        if not user_id:
            return redirect('/sign-in/?next=' + request.path)  # Redirect to sign-in if user is not authenticated

        # Check if the user has an in-progress order
        order, created = Orders.objects.get_or_create(user_id=user_id, order_status='in_progress')

        # Add or update the product in the order
        order_item, created = OrderItem.objects.get_or_create(
            order_id=order.order_id,
            product_id=product_id,
            defaults={'quantity': quantity}  # Use the selected quantity when creating the item
        )
        if not created:
            # If the item already exists in the order, increment the quantity
            order_item.quantity += quantity
            order_item.save()

        return redirect('order_in_process')  # Redirect to the order-in-process page

    return redirect('home')  # Redirect to home if the method is not POST


def order_in_process(request):
    
    user_id = request.session.get('user_id')  # Retrieve user_id from session
    try:
        order = Orders.objects.get(user_id=user_id, order_status='in_progress')
        items = OrderItem.objects.filter(order_id=order.order_id).select_related('product')
        for item in items:
            item.total_price = item.quantity * item.product.price
    except Orders.DoesNotExist:
        order = None
        items = []

    context = {
        'order': order,
        'items': items,
    }
    return render(request, 'order_in_process.html', context)

def submit_order(request):
    if request.method == "POST":
        user = request.user
        user_id = request.session.get('user_id')  # Retrieve user_id from session
        try:
            # Update the order status to 'completed'
            order = Orders.objects.get(user_id=user_id, order_status='in_progress')
            order.order_status = 'completed'
            order.save()
            return JsonResponse({"success": True})
        except Orders.DoesNotExist:
            return JsonResponse({"success": False, "message": "No in-progress order found!"})

    return JsonResponse({"success": False, "message": "Invalid request!"})