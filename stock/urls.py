from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('list', views.lista_productos, name='lista_productos'),

    path('tipo/crear/', views.crear_tipo, name='crear_tipo'),
    path('producto/crear/', views.crear_producto, name='crear_producto'),

    path('producto/<int:producto_id>/stock/', views.actualizar_stock, name='actualizar_stock'),

    path('crear_venta', views.crear_venta, name='venta'),
    path('ventas/historico/', views.consultar_ventas, name='consultar_ventas'),
]