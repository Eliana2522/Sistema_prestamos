from django.db.models.signals import post_save
from django.contrib.auth.models import User, Group
from django.dispatch import receiver
from .models import Cliente

@receiver(post_save, sender=Cliente)
def create_client_user(sender, instance, created, **kwargs):
    """
    Este signal se activa después de que se guarda un objeto Cliente.
    Si el cliente es nuevo (created=True), crea un objeto User de Django asociado.
    """
    if created:
        # Comprueba si ya existe un usuario con este número de documento para evitar errores.
        if not User.objects.filter(username=instance.numero_documento).exists():
            # Crea un nuevo usuario.
            user = User.objects.create_user(
                username=instance.numero_documento,
                email=instance.email,
                password=None
            )
            # Asigna una contraseña que no se puede usar hasta que el cliente la establezca.
            user.set_unusable_password()
            user.save()

            # Asignar el usuario al grupo 'Clientes'
            try:
                client_group = Group.objects.get(name='Clientes')
                user.groups.add(client_group)
            except Group.DoesNotExist:
                # Manejar el caso en que el grupo no exista (aunque la migración debería crearlo)
                pass

            # Vincula el usuario recién creado con el perfil del cliente.
            instance.user = user
            instance.save()
