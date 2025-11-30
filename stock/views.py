from django.shortcuts import render
from django.db.models import F, Sum
# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from .models import Producto, TipoProducto,Cliente
from django.utils import timezone

def home(request):
    # 1. Traer la cantidad de productos que están en alerta
    #    (cantidad es menor que el umbral_alerta)
    productos_bajo_stock = Producto.objects.filter(
        cantidad__lt=F('umbral_alerta')
    ).count()
    
    # 2. Crear un booleano para el condicional en el HTML
    con_alerta = productos_bajo_stock > 0
    
    contexto = {
        'productos_bajo_stock': productos_bajo_stock,
        'con_alerta': con_alerta
    }
    
    return render(request, 'home.html', contexto)
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
        
        # 🚨 NUEVO CAMPO: Capturar el umbral de alerta 🚨
        umbral_alerta = request.POST.get('umbral_alerta', 5) # Usamos 5 como default si el campo no viene
        
        # Aseguramos que umbral_alerta sea un entero, si no, usa el valor por defecto del modelo (5)
        try:
            umbral_alerta = int(umbral_alerta)
        except (ValueError, TypeError):
            umbral_alerta = 5 # Usa el valor seguro si la conversión falla

        if nombre and tipo_id:
            tipo = TipoProducto.objects.get(id=tipo_id)
            Producto.objects.create(
                nombre=nombre,
                tipo=tipo,
                cantidad=cantidad,
                valor=valor,
                # 🚨 PASAR EL NUEVO CAMPO AL CREADOR DEL OBJETO 🚨
                umbral_alerta=umbral_alerta
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

# ----------------------------------
# CREAR VENTA
# ----------------------------------
def crear_venta(request):
    productos = Producto.objects.all()
    clientes = Cliente.objects.all()

    if request.method == 'POST':
        producto_id = request.POST.get('producto')
        cliente_id = request.POST.get('cliente')  # Puede ser None
        cantidad = int(request.POST.get('cantidad'))

        producto = Producto.objects.get(id=producto_id)
        
        # Cliente es OPCIONAL
        cliente = None
        if cliente_id:
            try:
                cliente = Cliente.objects.get(id=cliente_id)
            except Cliente.DoesNotExist:
                pass

        # Validar stock
        if cantidad > producto.cantidad:
            messages.error(request, 'No hay suficiente stock')
            return redirect('crear_venta')

        # Calcular total
        total = producto.valor * cantidad

        # Crear la venta
        Ventas.objects.create(
            producto=producto,
            cliente=cliente,  # Puede ser None
            cantidad=cantidad,
            valor_total=total
        )

        # Restar stock
        producto.cantidad -= cantidad
        producto.save()

        messages.success(request, 'Venta registrada correctamente')
        return redirect('lista_productos')

    return render(request, 'crear_venta.html', {
        'productos': productos,
        'clientes': clientes
    })


# ----------------------------------
# CONSULTAR VENTAS
# ----------------------------------
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

# ----------------------------------
# VISTA: PANEL DE AVISOS DE ALERTA (DEDICADO)
# ----------------------------------
def panel_alertas(request):
    # Trae los detalles completos de los productos que están bajo stock
    productos_con_alerta = Producto.objects.filter(
        cantidad__lt=F('umbral_alerta')
    ).select_related('tipo').order_by('nombre')
    
    contexto = {
        'productos_con_alerta': productos_con_alerta,
        'conteo_alertas': productos_con_alerta.count(),
    }
    
    return render(request, 'panel_alertas.html', contexto)


# ----------------------------------
# EDITAR PRODUCTO Y UMBRAL DE ALERTA (DEBE EXISTIR)
# ----------------------------------
def editar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    tipos = TipoProducto.objects.all() 

    if request.method == 'POST':
        # ... (lógica de guardado)
        nombre = request.POST.get('nombre')
        tipo_id = request.POST.get('tipo')
        valor = request.POST.get('valor')
        umbral_alerta = request.POST.get('umbral_alerta') 
        
        producto.nombre = nombre
        producto.tipo_id = tipo_id 
        producto.valor = valor
        
        try:
            if umbral_alerta is not None:
                producto.umbral_alerta = int(umbral_alerta)
        except ValueError:
            messages.error(request, 'El umbral debe ser un número entero.')
            return redirect('editar_producto', producto_id=producto.id)
            
        producto.save()
        messages.success(request, f'Producto "{producto.nombre}" y umbral de alerta actualizados.')
        return redirect('lista_productos')

    return render(request, 'editar_producto.html', {
        'producto': producto,
        'tipos': tipos
    })

# ----------------------------------
# GESTIÓN DE CLIENTES
# ----------------------------------
def lista_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'lista_clientes.html', {'clientes': clientes})


def crear_cliente(request):
    if request.method == 'POST':
        nombre_completo = request.POST.get('nombre_completo')
        nombre_local = request.POST.get('nombre_local')
        email = request.POST.get('email')
        telefono = request.POST.get('telefono')
        direccion = request.POST.get('direccion')
        
        if nombre_completo:
            Cliente.objects.create(
                nombre_completo=nombre_completo,
                nombre_local=nombre_local if nombre_local else None,
                email=email if email else None,
                telefono=telefono if telefono else None,
                direccion=direccion if direccion else None
            )
            messages.success(request, 'Cliente creado correctamente')
            return redirect('lista_clientes')
    
    return render(request, 'crear_cliente.html')


def editar_cliente(request, cliente_id):
    cliente = get_object_or_404(Cliente, id=cliente_id)
    
    if request.method == 'POST':
        cliente.nombre = request.POST.get('nombre')
        cliente.apellido = request.POST.get('apellido')
        cliente.email = request.POST.get('email') or None
        cliente.telefono = request.POST.get('telefono') or None
        cliente.direccion = request.POST.get('direccion') or None
        cliente.save()
        
        messages.success(request, f'Cliente "{cliente.nombre_completo}" actualizado')
        return redirect('lista_clientes')
    
    return render(request, 'editar_cliente.html', {'cliente': cliente})
