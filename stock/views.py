from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from .models import Producto, TipoProducto
from django.utils import timezone

def home(request):
    return render(request, 'home.html')
# ----------------------------------
# LISTAR PRODUCTOS
# ----------------------------------
def lista_productos(request):
    productos = Producto.objects.select_related('tipo').all()
    return render(request, 'lista_productos.html', {'productos': productos})


# ----------------------------------
# CREAR TIPO DE PRODUCTO
# ----------------------------------
def crear_tipo(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')

        if nombre:
            TipoProducto.objects.create(nombre=nombre)
            return redirect('lista_productos')

    return render(request, 'crear_tipo.html')


# ----------------------------------
# CREAR PRODUCTO
# ----------------------------------
def crear_producto(request):
    tipos = TipoProducto.objects.all()

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        tipo_id = request.POST.get('tipo')
        cantidad = request.POST.get('cantidad')
        valor = request.POST.get('valor')

        if nombre and tipo_id:
            tipo = TipoProducto.objects.get(id=tipo_id)
            Producto.objects.create(
                nombre=nombre,
                tipo=tipo,
                cantidad=cantidad,
                valor=valor
            )
            return redirect('lista_productos')

    return render(request, 'crear_producto.html', {'tipos': tipos})


# ----------------------------------
# ACTUALIZAR STOCK (SUMAR O RESTAR)
# ----------------------------------
def actualizar_stock(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)

    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad'))
        accion = request.POST.get('accion')  # sumar o restar

        if accion == 'sumar':
            producto.cantidad += cantidad
        elif accion == 'restar':
            producto.cantidad -= cantidad
            if producto.cantidad < 0:
                producto.cantidad = 0

        producto.fecha_modificacion = timezone.now()
        producto.save()
        return redirect('lista_productos')

    return render(request, 'actualizar_stock.html', {'producto': producto})

from .models import Producto, TipoProducto, Ventas
from django.contrib import messages

from django.shortcuts import render, redirect
from .models import Producto, TipoProducto, Ventas
from django.contrib import messages

def crear_venta(request):
    productos = Producto.objects.all()

    if request.method == 'POST':
        producto_id = request.POST.get('producto')
        cliente = request.POST.get('cliente')
        cantidad = int(request.POST.get('cantidad'))

        producto = Producto.objects.get(id=producto_id)

        # Validar stock
        if cantidad > producto.cantidad:
            messages.error(request, 'No hay suficiente stock')
            return redirect('crear_venta')

        # Calcular total
        total = producto.valor * cantidad

        # Crear la venta
        Ventas.objects.create(
            producto=producto,
            cliente=cliente,
            cantidad=cantidad,
            valor_total=total
        )

        # Restar stock
        producto.cantidad -= cantidad
        producto.save()

        messages.success(request, 'Venta registrada correctamente')
        return redirect('lista_productos')

    return render(request, 'crear_venta.html', {'productos': productos}) 


from django.db.models import Sum
from django.utils.dateparse import parse_datetime

def consultar_ventas(request):
    ventas = Ventas.objects.all().order_by('-fecha')
    productos = Producto.objects.all()

    fecha_desde = request.GET.get('desde')
    fecha_hasta = request.GET.get('hasta')
    cliente = request.GET.get('cliente')
    producto_id = request.GET.get('producto')

    # Filtros
    if fecha_desde:
        ventas = ventas.filter(fecha__date__gte=fecha_desde)

    if fecha_hasta:
        ventas = ventas.filter(fecha__date__lte=fecha_hasta)

    if cliente:
        ventas = ventas.filter(cliente__icontains=cliente)

    if producto_id:
        ventas = ventas.filter(producto_id=producto_id)

    # Total recaudado
    total_recaudado = ventas.aggregate(Sum('valor_total'))['valor_total__sum'] or 0

    return render(request, 'consultar_ventas.html', {
        'ventas': ventas,
        'productos': productos,
        'total_recaudado': total_recaudado,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'cliente': cliente,
        'producto_id': producto_id,
    })
