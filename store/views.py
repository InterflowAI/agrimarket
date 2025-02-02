from django.shortcuts import render, redirect
from django.contrib.auth.models import User, auth
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse,HttpRequest
from django.forms import inlineformset_factory
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import Customer

from django.contrib.auth import authenticate, login, logout

from django.contrib import messages

from django.http import JsonResponse,HttpResponseRedirect
import json
import datetime
from .models import *
from .utils import cookieCart, cartData, guestOrder
from django.views.decorators.csrf import csrf_exempt
from .forms import CreateUserForm

def store(request):

    data = cartData(request)
    cartItems = data['cartItems']

    products = Product.objects.all()
    context = {"products": products}
    return render(request, "store/store.html", context)


@login_required(login_url="/login")
def cart(request):

    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cart': cartItems}
    return render(request, 'store/cart.html', context)

# function to add the item to  the cart.
def add_to_cart(request, item_id):
    cart = request.session.get('cart', {})
    cart[item_id] = cart.get(item_id, 0) + 1
    request.session['cart'] = cart
    return JsonResponse({'success': True})




@csrf_exempt
def checkout(request):
    data = cartData(request)
    cartItems = data['cartItems']

    print(data['items'])
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/checkout.html', context)


def updateItem(request):
    data = json.loads(request.body)
    productId = data["productId"]
    action = data["action"]

    # print("Action:", action)
    # print("productId:", productId)

    customer = Customer.objects.create(name=request.user.username,email=request.user.email,user=request.user)
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)

    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == "add":
        orderItem.quantity = orderItem.quantity + 1
    elif action == "remove":
        orderItem.quantity = orderItem.quantity - 1

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse("Item was added", safe=False)


def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp
    data = json.loads(request.body)


    customer, order = guestOrder(request, data)
       
    total = float(data["form"]["total"])
    order.transaction_id = transaction_id

    if total == float(order.get_cart_total):
        order.complete = True
    order.save()

    print(request.COOKIES.get('cart'))

    if order.shipping == True:
        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=data["shipping"]["address"],
            city=data["shipping"]["city"],
            region=data["shipping"]["region"],
            zipcode=data["shipping"]["zipcode"],
            country=data["shipping"]["country"],
        )

    response = HttpResponseRedirect(redirect_to='/')

    response.delete_cookie('cart')

    return response

def registerPage(request):
    form = CreateUserForm()

    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            user = form.cleaned_data.get('username')
            messages.success(request, 'Account was created for ' + user)

            return redirect('login')
    context = {'form':form}
    return render(request, 'store/register.html', context)

def loginPage(request:HttpRequest):
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            path = request.GET.get('next')

            if path is not None:
                return redirect(path)
            return redirect('store')
            
    context = {}
    return render(request, 'store/login.html', context)



def logout_user(request):
    logout(request)
    return redirect('store')

def order_confirmed(request):
     return render(request, 'order_confirm.html')