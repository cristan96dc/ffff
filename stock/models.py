from django.db import models

# Create your models here.
class TipoProducto(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


# ------------------------------
#  MODELO: Producto
# ------------------------------
class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    tipo = models.ForeignKey(TipoProducto, on_delete=models.CASCADE)

    cantidad = models.PositiveIntegerField(default=0)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    
    # 👈 NUEVO CAMPO DE ALERTA
    umbral_alerta = models.PositiveIntegerField(
        default=5, # Valor por defecto que el usuario puede cambiar
        verbose_name="Stock Mínimo de Alerta"
    )
    # -------------------------

    fecha_modificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.nombre} ({self.cantidad} unidades)"



class Ventas(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cliente = models.CharField(max_length=100)
    cantidad = models.PositiveIntegerField()
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)  # 👈 NUEVO
    fecha = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # calcular valor total automáticamente
        self.valor_total = self.producto.valor * self.cantidad
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Venta de {self.cantidad} x {self.producto.nombre} a {self.cliente}"

# ------------------------------
#  MODELO: Cliente
# ------------------------------
class Cliente(models.Model):
    nombre_completo = models.CharField(max_length=200, verbose_name="Nombre y Apellido")
    nombre_local = models.CharField(max_length=200, blank=True, null=True, verbose_name="Nombre del Local")
    email = models.EmailField(unique=True, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nombre_completo']
    
    def __str__(self):
        if self.nombre_local:
            return f"{self.nombre_completo} - {self.nombre_local}"
        return self.nombre_completo
