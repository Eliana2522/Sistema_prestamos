from django.shortcuts import redirect
from django.urls import reverse

class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Solo aplicamos la lógica para usuarios autenticados que no son staff
        if request.user.is_authenticated and not request.user.is_staff:
            # Evitar bucles de redirección infinitos
            allowed_paths = [
                reverse('client_change_password'), 
                reverse('client_logout')
            ]
            if request.path not in allowed_paths:
                try:
                    cliente = request.user.cliente_profile
                    if cliente.debe_cambiar_contrasena:
                        # Si la bandera está activa, redirigir a la página de cambio de contraseña
                        return redirect('client_change_password')
                except AttributeError:
                    # El perfil del cliente no existe o no tiene el campo, no hacer nada.
                    pass

        return response
