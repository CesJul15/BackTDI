from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os


class Command(BaseCommand):
    help = "Crea un superusuario demo. Usa --username --email --password o variables de entorno DEMO_ADMIN_*"

    def add_arguments(self, parser):
        parser.add_argument("--username", type=str, help="Nombre de usuario del admin")
        parser.add_argument("--email", type=str, help="Email del admin")
        parser.add_argument("--password", type=str, help="Password del admin")

    def handle(self, *args, **options):
        User = get_user_model()
        username = options.get("username") or os.environ.get("DEMO_ADMIN_USERNAME", "demo_admin")
        email = options.get("email") or os.environ.get("DEMO_ADMIN_EMAIL", "demo@example.com")
        password = options.get("password") or os.environ.get("DEMO_ADMIN_PASSWORD", "demo_password")

        if User.objects.filter(username=username).exists():
            self.stdout.write(f"Usuario {username} ya existe")
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(f"Superusuario creado: {username}")
