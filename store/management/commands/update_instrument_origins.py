from django.core.management.base import BaseCommand
from store.models import Instrumento
from store.external_apis import get_instrument_origin_from_wikipedia


class Command(BaseCommand):
    help = 'Actualiza los orígenes de instrumentos existentes usando Wikipedia API'

    def handle(self, *args, **options):
        instrumentos = Instrumento.objects.filter(origen__isnull=True) | Instrumento.objects.filter(origen='')
        
        self.stdout.write(self.style.SUCCESS(f'📊 Encontrados {instrumentos.count()} instrumentos sin origen\n'))
        
        for instrumento in instrumentos:
            self.stdout.write(f'🔍 Procesando: {instrumento.name}')
            origin = get_instrument_origin_from_wikipedia(instrumento.name)
            
            if origin:
                instrumento.origen = origin
                instrumento.save()
                self.stdout.write(self.style.SUCCESS(f'   ✅ Origen asignado: {origin}\n'))
            else:
                self.stdout.write(self.style.WARNING(f'   ⚠️  No se encontró origen\n'))
        
        self.stdout.write(self.style.SUCCESS('✨ Actualización completada'))
