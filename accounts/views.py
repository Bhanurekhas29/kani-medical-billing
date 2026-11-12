# accounts/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from django.db import transaction
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.urls import reverse
import calendar
from collections import OrderedDict
from datetime import datetime, timedelta
from django.utils.timezone import now

from .models import Product, Invoice, InvoiceItem
from .forms import ProductForm
from django.template.loader import render_to_string


# ---------------- Auth ----------------

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    msg = ''
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('dashboard')
        else:
            msg = "Invalid Credentials or not Superuser"
    return render(request, 'login.html', {'msg': msg})

def logout_view(request):
    logout(request)
    return redirect('login')


# ---------------- Dashboard ----------------

@login_required
def dashboard(request):
    today = timezone.now().date()

    total_revenue = Invoice.objects.aggregate(total=Sum('total'))['total'] or 0
    total_stock   = Product.objects.aggregate(total=Sum('piece_stock'))['total'] or 0
    out_of_stock  = Product.objects.filter(piece_stock=0).count()
    expired_count = Product.objects.filter(expiry_date__lt=today).count()
    total_products_sold = InvoiceItem.objects.aggregate(total=Sum('quantity'))['total'] or 0

    monthly_data = OrderedDict((month, 0) for month in range(1, 13))
    invoices = (
        Invoice.objects
        .annotate(month=TruncMonth('invoice_date'))
        .values('month')
        .annotate(monthly_total=Sum('total'))
        .order_by('month')
    )
    for entry in invoices:
        month_num = entry['month'].month
        monthly_data[month_num] = float(entry['monthly_total'])

    chart_labels = [calendar.month_abbr[m] for m in monthly_data.keys()]
    chart_data = list(monthly_data.values())

    dashboard_boxes = [
        {
            'label': 'Total Revenue',
            'value': f"₹{round(total_revenue, 2)}",
            'url': reverse('invoice_list'),
            'image': 'Total Revenue.png'
        },
        {
            'label': 'Total Stock (Pieces)',
            'value': total_stock,
            'url': reverse('products'),
            'image': 'Stock.png'
        },
        {
            'label': 'Out of Stock',
            'value': out_of_stock,
            'url': reverse('out_of_stock_products'),
            'image': 'Out of Stock.png'
        },
        {
            'label': 'Expired',
            'value': expired_count,
            'url': reverse('expired_products'),
            'image': 'Experied.png'
        }
    ]

    context = {
        'dashboard_boxes': dashboard_boxes,
        'total_revenue': round(total_revenue, 2),
        'total_stock': total_stock,
        'out_of_stock': out_of_stock,
        'expired_count': expired_count,
        'total_products_sold': total_products_sold,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }
    return render(request, 'dashboard.html', context)


# ---------------- Products (list + create) ----------------

@login_required
def products(request):
    products_qs = Product.objects.all().order_by('-id')
    form = ProductForm()

    if request.method == 'POST' and 'create_product' in request.POST:
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('products')

    return render(request, 'products.html', {
        'products': products_qs,
        'form': form,
    })


# ---------------- Cart ----------------

@login_required
def add_to_cart(request):
    if request.method != 'POST':
        return redirect('products')

    product_id = str(request.POST.get('product_id')).strip()
    quantity   = int(request.POST.get('quantity') or 0)
    unit_type  = (request.POST.get('unit_type') or 'piece').lower()

    if quantity <= 0:
        return redirect('products')

    product = get_object_or_404(Product, id=product_id)

    # only check availability; don't deduct here (we deduct on invoice)
    available = product.available_for(unit_type)
    if quantity > available:
        messages.error(request, f"Only {available} available for {product.name} ({unit_type}).")
        return redirect('products')

    base_price = product.price_for(unit_type)
    mrp        = product.mrp_for(unit_type)

    cart_key = f"{product.id}:{unit_type}"   # composite key
    cart = request.session.get('cart', {})

    if cart_key in cart:
        cart[cart_key]['quantity'] += quantity
    else:
        cart[cart_key] = {
            'id': product.id,
            'name': product.name,
            'batch': product.batch_no,
            'unit_type': unit_type,      # 'piece' | 'strip' | 'box'
            'price': float(base_price),  # base/unit
            'mrp': float(mrp),           # price with GST
            'quantity': quantity,
        }

    request.session['cart'] = cart
    request.session.modified = True
    return redirect('products')


@login_required
def remove_from_cart(request):
    if request.method != "POST":
        return redirect("billing")

    cart_key = str(request.POST.get("product_id", "")).strip()  # expect "<id>:<unit>"
    cart = request.session.get("cart", {})

    if cart_key in cart:
        del cart[cart_key]
        request.session["cart"] = cart
        request.session.modified = True
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"success": True, "message": "Product removed"})
        messages.success(request, "Product removed from cart.")
    else:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({"success": False, "message": "Not found"}, status=404)
        messages.error(request, "Product not found in cart.")

    return redirect("billing")


# ---------------- Billing page (cart review) ----------------

@login_required
def billing(request):
    # Next invoice number
    last_invoice = Invoice.objects.order_by('-id').first()
    next_invoice_number = f"INV-{(last_invoice.id + 1) if last_invoice else 1:03d}"

    cart = request.session.get('cart', {})
    cart = {str(k).strip(): v for k, v in cart.items()}

    total = 0
    total_quantity = 0

    for key, item in cart.items():
        item['subtotal'] = round(item['quantity'] * item['mrp'], 2)
        total += item['subtotal']
        total_quantity += item['quantity']

    request.session['cart'] = cart

    today = timezone.now().date()

    return render(request, 'billing.html', {
        'cart': cart,
        'total': round(total, 2),
        'total_quantity': total_quantity,
        'today': today,
        'next_invoice_number': next_invoice_number
    })


# ---------------- Invoice CRUD ----------------

@csrf_exempt
@login_required
def generate_invoice(request):
    if request.method != "POST":
        return redirect("billing")

    cart = request.session.get("cart", {})
    if not cart:
        messages.error(request, "Cart is empty.")
        return redirect("billing")

    total = 0

    with transaction.atomic():
        invoice = Invoice.objects.create(
            invoice_number=request.POST.get('invoice_number'),
            invoice_date=request.POST.get('invoice_date'),
            from_name=request.POST.get('from_name'),
            from_phone=request.POST.get('from_phone'),
            from_address=request.POST.get('from_address'),
            to_name=request.POST.get('to_name'),
            to_phone=request.POST.get('to_phone'),
            to_address=request.POST.get('to_address'),
            dl_no=request.POST.get('dl_no'),
            total=0
        )

        # Validate availability again and deduct correctly per unit_type
        for _, item in cart.items():
            product   = Product.objects.select_for_update().get(id=item['id'])
            unit_type = item.get('unit_type', 'piece')
            qty       = int(item['quantity'])

            # availability check
            if qty > product.available_for(unit_type):
                messages.error(request, f"Insufficient {unit_type} stock for {product.name}.")
                transaction.set_rollback(True)
                return redirect("billing")

            # deduct stock in all relevant levels
            product.apply_sale(unit_type, qty)
            product.save()

            subtotal = qty * float(item['mrp'])
            total += subtotal

            InvoiceItem.objects.create(
                invoice=invoice,
                product=product,
                batch_no=item['batch'],
                mrp=item['mrp'],
                quantity=qty,
                subtotal=subtotal,
                unit_type=unit_type,     # <-- add this field to InvoiceItem model if not present
            )

        invoice.total = round(total, 2)
        invoice.save()

    # Clear cart after save
    request.session["cart"] = {}
    messages.success(request, "✅ Invoice generated and stock updated.")
    return redirect("billing")


@login_required
def invoice_list(request):
    invoices = Invoice.objects.all().order_by('-invoice_date')

    customer = request.GET.get('customer', '').strip()
    date_filter = request.GET.get('date_filter', '').strip()

    if customer:
        invoices = invoices.filter(to_name__icontains=customer)

    today = now().date()

    if date_filter == 'today':
        invoices = invoices.filter(invoice_date=today)
    elif date_filter == 'last7':
        invoices = invoices.filter(invoice_date__gte=today - timedelta(days=7))
    elif date_filter == 'month':
        invoices = invoices.filter(invoice_date__year=today.year, invoice_date__month=today.month)

    return render(request, 'invoice_list.html', {'invoices': invoices})


def view_invoice(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    items = invoice.items.all()
    return render(request, 'view_invoice.html', {'invoice': invoice, 'items': items})


def edit_invoice(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    invoice_items = invoice.items.all()

    if request.method == 'POST':
        invoice.invoice_date  = request.POST.get('invoice_date')
        invoice.invoice_number = request.POST.get('invoice_number')
        invoice.dl_no         = request.POST.get('dl_no')
        invoice.license_no    = request.POST.get('license_no')
        invoice.from_name     = request.POST.get('from_name')
        invoice.from_phone    = request.POST.get('from_phone')
        invoice.from_address  = request.POST.get('from_address')
        invoice.to_name       = request.POST.get('to_name')
        invoice.to_phone      = request.POST.get('to_phone')
        invoice.to_address    = request.POST.get('to_address')
        invoice.save()

        grand_total = 0
        total_qty = 0

        with transaction.atomic():
            for item in invoice_items:
                qty_field = f'quantity_{item.id}'
                new_qty = int(request.POST.get(qty_field, item.quantity))
                old_qty = item.quantity
                diff = new_qty - old_qty
                if diff != 0:
                    product = item.product
                    unit_type = getattr(item, 'unit_type', 'piece')

                    # if increasing quantity, ensure stock exists
                    if diff > 0 and diff > product.available_for(unit_type):
                        messages.error(request, f"❌ Not enough {unit_type} stock for {product.name}. Available: {product.available_for(unit_type)}")
                        return redirect('edit_invoice', pk=invoice.pk)

                    # apply the difference (+ means extra sale; - means return)
                    if diff > 0:
                        product.apply_sale(unit_type, diff)
                    else:
                        # restock on decrease (reverse of sale)
                        add_back = abs(diff)
                        if unit_type == 'piece':
                            product.piece_stock += add_back
                        elif unit_type == 'strip':
                            product.strip_stock += add_back
                            product.piece_stock += add_back * max(1, product.pieces_per_strip)
                        elif unit_type == 'box':
                            product.box_stock += add_back
                            strips = add_back * max(1, product.strips_per_box)
                            product.strip_stock += strips
                            product.piece_stock += strips * max(1, product.pieces_per_strip)
                    product.save()

                    item.quantity = new_qty
                    item.subtotal = round(new_qty * float(item.mrp), 2)
                    item.save()

                grand_total += item.subtotal
                total_qty += item.quantity

        invoice.total = round(grand_total, 2)
        invoice.save()

        messages.success(request, "✅ Invoice updated and stock adjusted.")
        return redirect('view_invoice', pk=invoice.pk)

    total_quantity = sum(item.quantity for item in invoice_items)
    total = sum(item.subtotal for item in invoice_items)
    return render(request, 'edit_invoice.html', {
        'invoice': invoice,
        'invoice_items': invoice_items,
        'total': total,
        'total_quantity': total_quantity,
    })


@login_required
def delete_invoice(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    invoice.delete()
    return redirect('invoice_list')


def out_of_stock_products(request):
    products = Product.objects.filter(piece_stock__lte=0)
    return render(request, 'out_of_stock_products.html', {'products': products})


def expired_products(request):
    today = timezone.now().date()
    products = Product.objects.filter(expiry_date__lt=today)
    return render(request, 'expired_products.html', {'products': products})


def invoice_download(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    items = InvoiceItem.objects.filter(invoice=invoice)
    html_string = render_to_string('invoice_pdf.html', {'invoice': invoice, 'items': items})
    from weasyprint import HTML  # lazy: needs GTK libs
    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf_file = html.write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{invoice.invoice_number}.pdf"'
    return response



@csrf_exempt
@require_POST
def update_product(request):
    try:
        product_id = request.POST.get('product_id')
        if not product_id:
            return JsonResponse({'success': False, 'error': 'Product ID is required'})

        product = get_object_or_404(Product, id=product_id)

        # Basic details
        product.name = request.POST.get('name', product.name)
        product.batch_no = request.POST.get('batch_no', product.batch_no)
        product.description = request.POST.get('description', product.description)

        # Expiry date
        expiry_date = request.POST.get('expiry_date')
        if expiry_date:
            product.expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()

        # Prices
        box_price = request.POST.get('box_price')
        if box_price not in [None, '']:
            product.box_price = float(box_price)

        strip_price = request.POST.get('strip_price')
        if strip_price not in [None, '']:
            product.strip_price = float(strip_price)

        piece_price = request.POST.get('piece_price')
        if piece_price not in [None, '']:
            product.piece_price = float(piece_price)

        mrp = request.POST.get('mrp')
        if mrp not in [None, '']:
            product.mrp = float(mrp)

        # Conversions
        strips_per_box = request.POST.get('strips_per_box')
        if strips_per_box not in [None, '']:
            product.strips_per_box = int(strips_per_box)

        pieces_per_strip = request.POST.get('pieces_per_strip')
        if pieces_per_strip not in [None, '']:
            product.pieces_per_strip = int(pieces_per_strip)

        # Stock
        box_stock = request.POST.get('box_stock')
        if box_stock not in [None, '']:
            product.box_stock = int(box_stock)

        strip_stock = request.POST.get('strip_stock')
        if strip_stock not in [None, '']:
            product.strip_stock = int(strip_stock)

        piece_stock = request.POST.get('piece_stock')
        if piece_stock not in [None, '']:
            product.piece_stock = int(piece_stock)

        # Tax + codes
        gst_percent = request.POST.get('gst_percent')
        if gst_percent not in [None, '']:
            product.gst_percent = int(gst_percent)

        product.hsn = request.POST.get('hsn', product.hsn)
        product.state = request.POST.get('state', product.state)

        # Save final
        product.save()

        return JsonResponse({'success': True, 'message': 'Product updated successfully'})

    except ValueError as ve:
        return JsonResponse({'success': False, 'error': str(ve)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET

@require_GET
def get_product(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        data = {
            "id": product.id,
            "name": product.name,
            "batch_no": product.batch_no,
            "description": product.description,
            "expiry_date": product.expiry_date.strftime("%Y-%m-%d"),

            # Prices
            "box_price": float(product.box_price or 0),
            "strip_price": float(product.strip_price or 0),
            "piece_price": float(product.piece_price or 0),

            # Composition
            "strips_per_box": product.strips_per_box,
            "pieces_per_strip": product.pieces_per_strip,

            # Tax
            "gst_percent": product.gst_percent,
            "hsn": product.hsn,
            "state": product.state,

            # Stock
            "box_stock": product.box_stock,
            "strip_stock": product.strip_stock,
            "piece_stock": product.piece_stock,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})



from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # optional
def update_stock(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == "POST":
        stock_type = request.POST.get("stock_type")  # box / strip / piece
        try:
            stock_value = int(request.POST.get("stock", 0))
        except (ValueError, TypeError):
            stock_value = 0

        if stock_value >= 0:
            if stock_type == "box":
                product.box_stock = stock_value
            elif stock_type == "strip":
                product.strip_stock = stock_value
            elif stock_type == "piece":
                product.piece_stock = stock_value
            product.save()

    return redirect("out_of_stock_products")
