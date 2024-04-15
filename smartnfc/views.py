from django.shortcuts import render, redirect
from django.contrib.auth import login as logvn, authenticate
# from.forms import CustomAuthenticationForm
from django.contrib.auth.models import Group
import time
from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as log_in
from django.contrib.auth import logout as log_out
from paynow import Paynow
from django.shortcuts import render, redirect
from .models import *
from django.contrib.auth.decorators import login_required
import uuid
from decimal import Decimal
from django.conf import settings
from django.shortcuts import get_object_or_404

from django.http import HttpResponse


from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import *
from rest_framework import status

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from django.http import JsonResponse 

@method_decorator(csrf_exempt, name='dispatch')
class PaymentAPIView(APIView):
    def post(self, request, username, *args, **kwargs):
        user = User.objects.get(username=username)
        user_transactions = Deposit.objects.filter(user=user)
        context = {
            'transactions': user_transactions,
        }

        amounts = request.data.get('amount')
        amount = Decimal(request.data.get('amount'))
        account = request.data.get('account')
        currency = request.data.get('currency')
        paying_services = request.data.get('paying_services')

        # Generate a unique transaction ID for deposit
        deposit_trans_id = f"PAY-{uuid.uuid4().hex[:3]}".upper()

        # Generate a unique transaction ID for overall transaction record
        overall_trans_id = f"TRANS-{uuid.uuid4().hex[:3]}".upper()

        # Retrieve the wallet associated with the user
        wallet = Wallet.objects.filter(user=user).first()

        # Update the wallet balance based on currency type
        if currency.lower() == 'zig':
            wallet.amount_zig += amount
        elif currency.lower() == 'usd':
            wallet.amount_usd += amount

        # Save the updated wallet
        wallet.save()

        # Create and save the Deposit object
        deposit = Payment.objects.create(
            trans_id=deposit_trans_id,
            amount_deposit=amount,
            currency=currency,
            receiver=paying_services,
            user=user,
            wallet=wallet
        )

        # Create and save the Transaction object
        transaction = Transaction.objects.create(
            trans_id=overall_trans_id,
            amount=amount,
            currency=currency,
            user=user,
            transaction_type='payment',
            status='completed'  # Assuming the default status is 'completed'
        )
        return Response({'messagex': 'Payment successful'}, status=status.HTTP_201_CREATED)
        # Now integrate Paynow payment gateway


@method_decorator(csrf_exempt, name='dispatch')
class DepositAPIView(APIView):
    def post(self, request, username, *args, **kwargs):
        user = User.objects.get(username=username)
        user_transactions = Deposit.objects.filter(user=user)
        context = {
            'transactions': user_transactions,
        }

        amount = Decimal(request.data.get('amount'))
        account = request.data.get('account')
        currency = request.data.get('currency')
        paying_services = request.data.get('paying_services')

        # Generate a unique transaction ID for deposit
        deposit_trans_id = f"DEP-{uuid.uuid4().hex[:3]}".upper()

        # Generate a unique transaction ID for overall transaction record
        overall_trans_id = f"TRANS-{uuid.uuid4().hex[:3]}".upper()

        # Retrieve the wallet associated with the user
        wallet = Wallet.objects.filter(user=user).first()

        # Update the wallet balance based on currency type
        if currency.lower() == 'zig':
            wallet.amount_zig += amount
        elif currency.lower() == 'usd':
            wallet.amount_usd += amount

        # Save the updated wallet
        wallet.save()

        # Create and save the Deposit object
        deposit = Deposit.objects.create(
            trans_id=deposit_trans_id,
            amount_deposit=amount,
            currency=currency,
            source=paying_services,
            user=user,
            wallet=wallet
        )

        # Create and save the Transaction object
        transaction = Transaction.objects.create(
            trans_id=overall_trans_id,
            amount=amount,
            currency=currency,
            user=user,
            transaction_type='deposit',
            status='completed'  # Assuming the default status is 'completed'
        )

        # Now integrate Paynow payment gateway
        transaction_id = int(generate_transaction_id())

        # Generate Urls to pass to Paynow
        r = reverse('paynows_update', args=(transaction_id,))
        result_url = request.build_absolute_uri(r)
        r = reverse('paynows_return', args=(transaction_id,))
        return_url = request.build_absolute_uri(r)

        # Create an instance of the Paynow class
        paynow = Paynow(settings.PAYNOW_INTEGRATION_ID,
                        settings.PAYNOW_INTEGRATION_KEY,
                        result_url,
                        return_url,
                        )

        # Create a new payment passing in the reference for that payment and the user's email address
        payment = paynow.create_payment(transaction_id, user.email)

        # Add item to the payment
        payment.add('Deposit', amount)

        # Send payment to Paynow
        response = paynow.send(payment)

        if response.success:
            # Get the link to redirect the user to
            redirect_url = response.redirect_url

            # Get the poll url
            poll_url = response.poll_url

            # Save transaction details to database, and record as unpaid
            payment = PaynowPayment(user=user,
                                    status=response.status,
                                    reference=transaction_id,
                                    amount=amount,
                                    details='Deposit',
                                    email=user.email,
                                    init_status=response.status,
                                    poll_url=poll_url,
                                    browser_url=redirect_url,
                                    cellphone=wallet.cell_number
                                )
            payment.save()
            # Redirect browser to Paynow
            return Response({'redirect_url': redirect_url}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Payment failed'}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class LoginAPIView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')

            user = authenticate(request, username=email, password=password)

            if user is not None:
                log_in(request, user)
                response_data = {
                    'messagex': 'Login successful',
                    'user': {
                        'id': user.pk,
                        'username': user.username,
                        # Include other user attributes as needed
                    }
                }
                return JsonResponse(response_data, status=status.HTTP_200_OK)
            else:
                return JsonResponse({'error': 'Invalid email or password'}, status=status.HTTP_400_BAD_REQUEST)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class UserDashboardAPIView(APIView):
    def get(self, request, username):
        current_user = User.objects.get(username=username)
        user_serializer = UserSerializer(current_user)
      
        
       

        # Retrieve wallet information for the current user
        user_wallet = Wallet.objects.filter(user=current_user).first()
        wallet_serializer = WalletSerializer(user_wallet)

        # Retrieve transaction information for the current user
        user_transactions = Transaction.objects.filter(user=current_user).order_by('-id')[:10]
        transaction_serializer = TransactionSerializer(user_transactions, many=True)

        # Retrieve account information for the current user
        user_account = Account.objects.filter(user=current_user).first()
        account_serializer = AccountSerializer(user_account)

        return Response({
            'wallet': wallet_serializer.data,
            'transactions': transaction_serializer.data,
            'account': account_serializer.data,
            'user':user_serializer.data,
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class WithdrawAPIView(APIView):
  
    def get(self, request,username):
        current_user = User.objects.get(username=username)
        withdrawals = Withdraw.objects.filter(user=current_user)
        serializer = WithdrawalSerializer(withdrawals, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    
    def post(self, request,username):
        current_user = User.objects.get(username=username)
        amount = Decimal(request.data.get('amount'))
        account = request.data.get('account')
        currency = request.data.get('currency')
        receiving_services = request.data.get('receiving_services')

        with_trans_id = f"WITH-{uuid.uuid4().hex[:3]}".upper()
        overall_trans_id = f"TRANS-{uuid.uuid4().hex[:3]}".upper()

        user = current_user
        wallet = Wallet.objects.filter(user=user).first()

        if currency.lower() == 'zig':
            wallet.amount_zig += (-amount)
        elif currency.lower() == 'usd':
            wallet.amount_usd += (-amount)

        wallet.save()

        withdraw = Withdraw.objects.create(
            trans_id=with_trans_id,
            amount_deposit=amount,
            currency=currency,
            source=receiving_services,
            user=user,
            wallet=wallet
        )

        transaction = Transaction.objects.create(
            trans_id=overall_trans_id,
            amount=amount,
            currency=currency,
            user=user,
            transaction_type='withdrawal',
            status='completed'
        )

        serializer = WithdrawalSerializer(withdraw)
        return Response({'messagex': 'Login successful'}, status=status.HTTP_201_CREATED)

def generate_transaction_id():
    """
    Generates a unique id which will be used by paynow to refer to the payment
    initiated
    """
    return str(int(time.time() * 1000))




@method_decorator(csrf_exempt, name='dispatch')
class CreditAPIView(APIView):
  
    def get(self, request,username):
        current_user = User.objects.get(username=username)
        withdrawals = Withdraw.objects.filter(user=current_user)
        serializer = WithdrawalSerializer(withdrawals, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    
    def post(self, request,username):
        current_user = User.objects.get(username=username)
        amount = Decimal(request.data.get('amount'))
        account = request.data.get('account')
        currency = request.data.get('currency')
        receiving_services = request.data.get('receiving_services')

        with_trans_id = f"CRD-{uuid.uuid4().hex[:3]}".upper()

        # Generate a unique transaction ID for overall transaction record
        overall_trans_id = f"TRANS-{uuid.uuid4().hex[:3]}".upper()

        user = current_user
        wallet = Wallet.objects.filter(user=user).first()

        if currency.lower() == 'zig':
            wallet.amount_zig += (amount)
        elif currency.lower() == 'usd':
            wallet.amount_usd += (amount)
        
        # Save the updated wallet
        wallet.save()
        
        # Create and save the Withdraw object
        withdraw = Credit.objects.create(
            trans_id=with_trans_id,
            amount_deposit=amount,
            currency=currency,
            source=receiving_services,
            user=user,
            wallet=wallet
        
        )
        
        # Create and save the Transaction object
        transaction = Transaction.objects.create(
            trans_id=overall_trans_id,
            amount=amount,
            currency=currency,
            user=user,
            transaction_type='credit',
            status='completed'  # Assuming the default status is 'completed'
        )

        serializer = WithdrawalSerializer(withdraw)
        return Response({'messagex': 'Login successful'}, status=status.HTTP_201_CREATED)


# Create operations
def create_wallet(request):
    if request.method == 'POST':
        # Extract data from the request
        account_name = request.POST.get('account_name')
        currency = request.POST.get('currency')
        date_added = request.POST.get('date_added')
        # Create a new Wallet object
        wallet = Wallet.objects.create(account_name=account_name, currency=currency, date_added=date_added)
        # Save the new wallet
        wallet.save()
        return redirect('wallet_detail', pk=wallet.pk)
    else:
        return render(request, 'create_wallet.html')

def create_deposit(request):
    if request.method == 'POST':
        # Extract data from the request
        # Similar steps as above for creating a Deposit object
        pass
    else:
        return render(request, 'create_deposit.html')

# Read operations
def wallet_detail(request, pk):
    # Retrieve a specific wallet object
    wallet = Wallet.objects.get(pk=pk)
    return render(request, 'wallet_detail.html', {'wallet': wallet})

def deposit_detail(request, pk):
    # Retrieve a specific deposit object
    deposit = Deposit.objects.get(pk=pk)
    return render(request, 'deposit_detail.html', {'deposit': deposit})

# Update operations
def update_wallet(request, pk):
    if request.method == 'POST':
        # Retrieve the existing wallet object
        wallet = Wallet.objects.get(pk=pk)
        # Update its attributes
        wallet.account_name = request.POST.get('account_name')
        wallet.currency = request.POST.get('currency')
        wallet.date_added = request.POST.get('date_added')
        # Save the changes
        wallet.save()
        return redirect('wallet_detail', pk=wallet.pk)
    else:
        # Retrieve the existing wallet object and display its data in a form for editing
        wallet = Wallet.objects.get(pk=pk)
        return render(request, 'update_wallet.html', {'wallet': wallet})

def update_deposit(request, pk):
    # Similar steps as above for updating a deposit object
    pass

# Delete operations
def delete_wallet(request, pk):
    if request.method == 'POST':
        # Retrieve the wallet object and delete it
        wallet = Wallet.objects.get(pk=pk)
        wallet.delete()
        return redirect('home')
    else:
        # Display a confirmation page before deleting the wallet
        return render(request, 'confirm_delete_wallet.html', {'pk': pk})

def delete_deposit(request, pk):
    # Similar steps as above for deleting a deposit object
    pass


def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            log_in(request, user)
            # Redirect to a success page.
            return redirect('dashboard_user')
        else:
            # Add an error message using Django's messaging framework.
            messages.error(request, 'Invalid email or password.')
            return render(request, 'login.html')
    else:
        # If it's not a POST request, just render the login page.
        return render(request, 'login.html')



def home(request):
    return render(request, 'index.html')

def user_dashboard(request):
    current_user = request.user

    # Retrieve wallet information for the current user
    user_wallet = Wallet.objects.filter(user=current_user).first()

    # Retrieve transaction information for the current user
    user_transactions = Transaction.objects.filter(user=current_user).order_by('-id')[:10]
    user_transactionz = Transaction.objects.filter(user=current_user)

    # Retrieve account information for the current user
    user_account = Account.objects.filter(user=current_user).first()
    payment = Transaction.objects.filter(user=current_user).filter(transaction_type="payment").order_by('-id')[:1]

    for x in payment:
        print(x.amount)


# Filter transactions where transaction_type is "Deposit"
    deposit= user_transactionz.filter(transaction_type="deposit").order_by('-id')[:1]

    for x in deposit:
        print(x.amount)

    # Pass the retrieved data to the template
    context = {
        'wallet': user_wallet,
        'transactions': user_transactions,
        'account': user_account,
        'payment': payment.first(),
        'deposit': deposit.first()
    }
    return render(request, 'dashboard.html',context)

def company_dashboard(request):
    return render(request, 'dashboard.html')

def admin_dashboard(request):
    return render(request, 'dashboard.html')

def transcations(request):
    user_transactions = Transaction.objects.filter(user=request.user)
    context = {
        
        'transactions': user_transactions,
        
    }
    return render(request, 'transactions.html',context)

def wallet(request):
    withdrawals = Credit.objects.filter(user=request.user)
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))  # Convert amount to float
        account = request.POST.get('account')
        currency = request.POST.get('currency')
        receiving_services = request.POST.get('receiving_services')
        
        with_trans_id = f"CRD-{uuid.uuid4().hex[:3]}".upper()
        

        # Generate a unique transaction ID for overall transaction record
        overall_trans_id = f"TRANS-{uuid.uuid4().hex[:3]}".upper()
        # Assuming you have a logged-in user, retrieve it
        user = request.user
        
        # Retrieve the wallet associated with the user
        wallet = Wallet.objects.filter(user=user).first()
        
        # Deduct amount from the wallet based on currency type
        if currency.lower() == 'zig':
            wallet.amount_zig += (amount)
        elif currency.lower() == 'usd':
            wallet.amount_usd += (amount)
        
        # Save the updated wallet
        wallet.save()
        
        # Create and save the Withdraw object
        withdraw = Credit.objects.create(
            trans_id=with_trans_id,
            amount_deposit=amount,
            currency=currency,
            source=receiving_services,
            user=user,
            wallet=wallet
        
        )
        
        # Create and save the Transaction object
        transaction = Transaction.objects.create(
            trans_id=overall_trans_id,
            amount=amount,
            currency=currency,
            user=user,
            transaction_type='credit',
            status='completed'  # Assuming the default status is 'completed'
        )

        return redirect('wallet')  # Re
    return render(request, 'rewards.html',{'withdrawals': withdrawals})

class WalletAPIView(APIView):
    def get(self, request):
        withdrawals = Credit.objects.filter(user=request.user)
        # You may need to serialize withdrawals before returning them in the response
        return Response({'withdrawals': withdrawals})

    def post(self, request):
        amount = Decimal(request.data.get('amount'))  # Convert amount to Decimal
        account = request.data.get('account')
        currency = request.data.get('currency')
        receiving_services = request.data.get('receiving_services')

        with_trans_id = f"CRD-{uuid.uuid4().hex[:3]}".upper()

        # Generate a unique transaction ID for overall transaction record
        overall_trans_id = f"TRANS-{uuid.uuid4().hex[:3]}".upper()

        # Assuming you have a logged-in user, retrieve it
        user = request.user

        # Retrieve the wallet associated with the user
        wallet = Wallet.objects.filter(user=user).first()

        # Deduct amount from the wallet based on currency type
        if currency.lower() == 'zig':
            wallet.amount_zig += amount
        elif currency.lower() == 'usd':
            wallet.amount_usd += amount

        # Save the updated wallet
        wallet.save()

        # Create and save the Credit object
        credit = Credit.objects.create(
            trans_id=with_trans_id,
            amount_deposit=amount,
            currency=currency,
            source=receiving_services,
            user=user,
            wallet=wallet
        )

        # Create and save the Transaction object
        transaction = Transaction.objects.create(
            trans_id=overall_trans_id,
            amount=amount,
            currency=currency,
            user=user,
            transaction_type='credit',
            status='completed'  # Assuming the default status is 'completed'
        )

        return Response({'message': 'Transaction successful'}, status=status.HTTP_201_CREATED)

def deposit(request):
    user_transactions = Deposit.objects.filter(user=request.user)
    context = {
        
        'transactions': user_transactions,
        
    }
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))
        account = request.POST.get('account')
        currency = request.POST.get('currency')
        paying_services = request.POST.get('paying_services')
        
        # Generate a unique transaction ID for deposit
        deposit_trans_id = f"DEP-{uuid.uuid4().hex[:3]}".upper()
        

        # Generate a unique transaction ID for overall transaction record
        overall_trans_id = f"TRANS-{uuid.uuid4().hex[:3]}".upper()

        
        # Assuming you have a logged-in user, retrieve it
        user = request.user
        
        # Retrieve the wallet associated with the user
        wallet = Wallet.objects.filter(user=user).first()
        
        
        
        print(currency)
        # Update the wallet balance based on currency type
        if currency.lower() == 'zig':
            wallet.amount_zig += amount
        elif currency.lower() == 'usd':
            wallet.amount_usd += amount
        
        # Save the updated wallet
        wallet.save()
        
        # Create and save the Deposit object
        deposit = Deposit.objects.create(
            trans_id=deposit_trans_id,
            amount_deposit=amount,
            currency=currency,
            source=paying_services,
            user=user,
            wallet=wallet
        )
        
        # Create and save the Transaction object
        transaction = Transaction.objects.create(
            trans_id=overall_trans_id,
            amount=amount,
            currency=currency,
            user=user,
            transaction_type='deposit',
            status='completed'  # Assuming the default status is 'completed'
        )

        # Now integrate Paynow payment gateway
        transaction_id = int(generate_transaction_id())

        # Generate Urls to pass to Paynow
        r = reverse('paynows_update', args=(transaction_id,))

        result_url = request.build_absolute_uri(r)
        r = reverse('paynows_return', args=(transaction_id,))
        return_url = request.build_absolute_uri(r)

        # Create an instance of the Paynow class
        paynow = Paynow(settings.PAYNOW_INTEGRATION_ID,
                        settings.PAYNOW_INTEGRATION_KEY,
                        result_url,
                        return_url,
                        )

        # Create a new payment passing in the reference for that payment and the user's email address
        payment = paynow.create_payment(transaction_id, request.user.email)

        # Add item to the payment
        payment.add('Deposit', amount)

        # Send payment to Paynow
        response = paynow.send(payment)

        if response.success:
            # Get the link to redirect the user to
            redirect_url = response.redirect_url

            # Get the poll url
            poll_url = response.poll_url

            # Save transaction details to database, and record as unpaid
            payment = PaynowPayment(user=request.user,
                                    status=response.status,
                                    reference=transaction_id,
                                    amount=amount,
                                    details='Deposit',
                                    email=request.user.email,
                                    init_status=response.status,
                                    poll_url=poll_url,
                                    browser_url=redirect_url,
                                    cellphone=wallet.cell_number
                                )
            payment.save()
            # Redirect browser to Paynow
            return redirect(redirect_url)

    return render(request, 'deposit-money-2.html',context)

def withdraw(request):
    withdrawals = Withdraw.objects.filter(user=request.user)
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount'))  # Convert amount to float
        account = request.POST.get('account')
        currency = request.POST.get('currency')
        receiving_services = request.POST.get('receiving_services')
        
        with_trans_id = f"WITH-{uuid.uuid4().hex[:3]}".upper()
        

        # Generate a unique transaction ID for overall transaction record
        overall_trans_id = f"TRANS-{uuid.uuid4().hex[:3]}".upper()
        # Assuming you have a logged-in user, retrieve it
        user = request.user
        
        # Retrieve the wallet associated with the user
        wallet = Wallet.objects.filter(user=user).first()
        
        # Deduct amount from the wallet based on currency type
        if currency.lower() == 'zig':
            wallet.amount_zig += (-amount)
        elif currency.lower() == 'usd':
            wallet.amount_usd += (-amount)
        
        # Save the updated wallet
        wallet.save()
        
        # Create and save the Withdraw object
        withdraw = Withdraw.objects.create(
            trans_id=with_trans_id,
            amount_deposit=amount,
            currency=currency,
            source=receiving_services,
            user=user,
            wallet=wallet
        
        )
        
        # Create and save the Transaction object
        transaction = Transaction.objects.create(
            trans_id=overall_trans_id,
            amount=amount,
            currency=currency,
            user=user,
            transaction_type='withdrawal',
            status='completed'  # Assuming the default status is 'completed'
        )

        return redirect('withdraw')  # Re
    return render(request, 'withdraw-money.html',{'withdrawals': withdrawals})

def payment(request):
    return render(request, 'sign-up.html')

def register(request):
    if request.method == 'POST':
        # Retrieve form data
        full_name = request.POST.get('full_name')
        username = request.POST.get('username')
        group_type = request.POST.get('group_type')
        password = request.POST.get('password')
        verify_password = request.POST.get('verify_password')
        email = request.POST.get('email')
        cell_number = request.POST.get('cell_number')
        currency = ''
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            message = 'Email already exists.'
            return render(request, 'sign-up.html', {'message': message})
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            message = 'Username already exists.'
            return render(request, 'sign-up.html', {'message': message})
        
        user = User.objects.create_user(username=username, email=email, password=password)
        user.first_name = full_name.split()[0]  # Set first name
        user.last_name = ' '.join(full_name.split()[1:])  # Set last name
        user.save()

        unique_id = "SMF-" + str(uuid.uuid4().hex[:4]) + "-2024-" + str(uuid.uuid4().hex[:3]).upper()
        account = Wallet.objects.create(account_name=unique_id, user=user ,amount_zig=0,amount_usd=0,cell_number=cell_number,created_by=user,currency=currency)
        print(account)

        
        return redirect('login')
    else:
        # If it's not a POST request, render the registration form
        return render(request, 'sign-up.html')



def profile(request):
    acc = Account.objects.filter(user=request.user).first()
    if request.method == 'POST':
    # Retrieve data from the POST request
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        uploaded_file = request.FILES['id_confirmation_documents']

    # Check if an account with the same email already exists
        if Account.objects.filter(user__email=email).exists():
        # Handle the error scenario here, e.g. by displaying an error message
            return render(request, 'account.html', {'acc': acc, 'error': 'An account with this email already exists.'})

    # Create a new Account object if no account with the same email exists
        prof = Account.objects.create(full_name= first_name + " "+ last_name,user=request.user,username = request.user.username,documents=uploaded_file)
    else:
        return render(request, 'account.html',{'acc':acc})

def logout(request):
    log_out(request)
    return redirect('home') 


@login_required
def paynow_payment(request):
    """
    This is the functions that initiates the payment process. This is
    where the magic starts
    """
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data

            # Generate unique Transaction ID
            transaction_id = generate_transaction_id()

            # Generate Urls to pass to Paynow. These are generated dynamicaly
            # and should be absolute
            # result url is used by paynow system to update yo website on the status of a payment
            #r = reverse('payments:paynow_update', args=(transaction_id, ))
            result_url = request.build_absolute_uri('www.google.com')
            # return url is the url paynow will return the payee to your site
            #r = reverse('payments:paynow_return', args=(transaction_id,))
            return_url = request.build_absolute_uri()


            # Create an instance of the Paynow class optionally setting the result and return url(s)
            paynow = Paynow(settings.PAYNOW_INTEGRATION_ID,
                            settings.PAYNOW_INTEGRATION_KEY,
                            result_url,
                            return_url,
                            )

            # Create a new payment passing in the reference for that payment(e.g invoice id, or anything that you can
            # use to identify the transaction and the user's email address.
            payment = paynow.create_payment(transaction_id, form.cleaned_data['email'])


            # You can then start adding items to the payment python passing in the name of the item and the price of the
            # item. This is useful when the site has a shopping cart
            payment.add(form.cleaned_data['details'], form.cleaned_data['amount'])

            # When you are finally ready to send your payment to Paynow, you can use the `send` method
            # in the `paynow` object and save the response from paynow in a variable
            response = paynow.send(payment)

            if response.success:
                # Get the link to redirect the user to, then use it as you see fit
                redirect_url = response.redirect_url

                # Get the poll url (used to check the status of a transaction). You might want to save this in your DB
                poll_url = response.poll_url

                # save transaction details to database, and record as unpaid
                payment = PaynowPayment(user=request.user,
                                        status=response.status,
                                        reference=transaction_id,
                                        amount=cleaned_data['amount'],
                                        details=form.cleaned_data['details'],
                                        email=form.cleaned_data['email'],
                                        cellphone=cleaned_data['cellphone'],
                                        init_status=response.status,
                                        poll_url=poll_url,
                                        browser_url=redirect_url,
                                        )
                payment.save()
                # redirect browser to paynow site for payment
                return redirect(response.redirect_url, permanent=True)
            else:
                msg = 'Error in processing payment. Please try again'
                messages.error(request, msg)
    else:
        form = PaymentForm()
    # if not POST request or error in inputs return input form
    return render(request, 'payments/paynow_payment.html', {'form': form})


@login_required
def paynow_mobile_payment(request):
    """
    This is the functions that initiates the mobile payment process. Its an alternative way that is only limited to
    ecocash
    """
    instructions = None
    if request.method == 'POST':
        form = MobilePaymentForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data

            # Generate unique Transaction ID
            transaction_id = generate_transaction_id()

            # Generate Urls to pass to Paynow. These are generated dynamicaly
            # and should be absolute
            # result url is used by paynow system to update yo website on the status of a payment
            r = reverse('payments:paynow_update', args=(transaction_id, ))
            result_url = request.build_absolute_uri(r)
            # return url is the url paynow will return the payee to your site
            r = reverse('payments:paynow_return', args=(transaction_id,))
            return_url = request.build_absolute_uri(r)

            print(result_url)
            print(return_url)

            # Create an instance of the Paynow class optionally setting the result and return url(s)
            paynow = Paynow(settings.PAYNOW_INTEGRATION_ID,
                            settings.PAYNOW_INTEGRATION_KEY,
                            result_url,
                            return_url,
                            )

            # Create a new payment passing in the reference for that payment(e.g invoice id, or anything that you can
            # use to identify the transaction and the user's email address.
            payment = paynow.create_payment(transaction_id, request.user.email)


            # You can then start adding items to the payment python passing in the name of the item and the price of the
            # item. This is useful when the site has a shopping cart
            payment.add(form.cleaned_data['details'], form.cleaned_data['amount'])

            # When you are finally ready to send your payment to Paynow, you can use the `send` method
            # in the `paynow` object and save the response from paynow in a variable
            response = paynow.send_mobile(payment, form.cleaned_data['cellphone'], 'ecocash')

            if response.success:
                # Get the link to redirect the user to, then use it as you see fit
                redirect_url = response.redirect_url

                # Get the poll url (used to check the status of a transaction). You might want to save this in your DB
                poll_url = response.poll_url

                # Get instructions to display
                instructions = response.instructions

                # save transaction details to database, and record as unpaid
                payment = PaynowPayment(user=request.user,
                                        status=response.status,
                                        reference=transaction_id,
                                        amount=cleaned_data['amount'],
                                        details=form.cleaned_data['details'],
                                        cellphone=form.cleaned_data['cellphone'],
                                        init_status=response.status,
                                        poll_url=poll_url,
                                        browser_url=redirect_url,
                                        )
                payment.save()
                print(redirect_url)
                print(poll_url)
            else:
                msg = 'Error in processing payment. Please try again'
                messages.error(request, msg)
    else:
        form = MobilePaymentForm()
    # if not POST request or error in inputs return input form
    return render(request, 'payments/paynow_mobile_payment.html', {'form': form, 'instructions': instructions})


def paynows_return(request, payment_id):
    """This the point where Paynow returns user to our site"""
    # Get payment object
    payment = get_object_or_404(PaynowPayment, reference=payment_id)
    # Init Paynow oject. The urls can now be blank
    paynow = Paynow(settings.PAYNOW_INTEGRATION_ID, settings.PAYNOW_INTEGRATION_KEY, '', '')

    # Check the status of the payment with the paynow server
    payment_result = paynow.check_transaction_status(payment.poll_url)

    save_changes = False

    # check if status has changed
    if payment.status != payment_result.status:
        payment.status = payment_result.status
        save_changes = True

    # Check if paynow reference has changed
    if payment.paynow_reference != payment_result.paynow_reference:
        payment.paynow_reference = payment_result.paynow_reference
        save_changes = True

    # Check if payment is now paid
    print(payment_result.paid)
    if payment_result.paid:
        if not payment.paid:
            payment.paid = True
            payment.confirmed_at = timezone.now()

    if save_changes:
        payment.save()

    msg = "Payment for Transaction " + payment.reference + ' confirmed'
    msg += " Paynow Reference: " + payment.paynow_reference
    messages.success(request, msg)
    msg = "Paynow Payment status => " + payment.status
    messages.success(request, msg)




    return redirect(reverse('deposit'))


def paynows_update(request, payment_reference):
    """This the point which Paynow polls our site with a payment status. I find it best to check with the Paynow Server.
     I also do the check when a payer is returned to the site when user is returned to site"""

    # Get saved paymend details
    payment = get_object_or_404(PaynowPayment, reference=payment_reference)
    # Init paynow object. The URLS can be blank
    paynow = Paynow(settings.PAYNOW_INTEGRATION_ID, settings.PAYNOW_INTEGRATION_KEY, '', '')
    # Check the status of the payment with paynow server
    payment_result = paynow.check_transaction_status(payment.poll_url)

    save_changes = False

    # check if status has changed
    if payment.status != payment_result.status:
        payment.status = payment_result.status
        save_changes = True

    # Check if paynow reference has changed
    if payment.paynow_reference != payment_result.paynow_reference:
        payment.paynow_reference = payment_result.paynow_reference
        save_changes = True

    # Check if payment is now paid
    if payment_result.paid:
        if not payment.paid:
            payment.paid = True
            payment.confirmed_at = timezone.now()

    if save_changes:
        payment.save()

    return redirect('dashboard_user')

