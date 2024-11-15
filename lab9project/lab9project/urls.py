"""
URL configuration for lab9project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from lab9app import views
from lab9app.views import ProductListView, ProductDetailView,Product_Create

urlpatterns = [
    path("admin/", admin.site.urls),

    path('', ProductListView.as_view(), name='home'),  # Root URL redirects to product list
    path('products/', ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product_detail'),
    path('products/new/', Product_Create, name='Product_Create'),  # New product creation
    #path('list/', views.EmployeeList.as_view(), name='employee_list'),
    #path('list/<int:pk>', views.EmployeeDetail.as_view(),name='employee_detail'),
    #path('create', views.EmployeeCreate.as_view() ),
    #path('update/<int:pk>', views.EmployeeUpdate.as_view(),name='employee_update'),
    #path('delete/<int:pk>', views.EmployeeDelete.as_view(),name='employee_delete'),
]
