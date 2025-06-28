# Create this file at: farm2market_backend/coreF2M/management/commands/fix_db_indexes.py

import os
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Fix duplicate database indexes before migration'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                # Check if index exists and drop it
                cursor.execute("SHOW INDEX FROM coreF2M_category WHERE Key_name = 'category_name_idx'")
                if cursor.fetchone():
                    self.stdout.write(self.style.WARNING('Dropping existing category_name_idx...'))
                    cursor.execute("DROP INDEX category_name_idx ON coreF2M_category")
                    self.stdout.write(self.style.SUCCESS('Index dropped successfully'))
                else:
                    self.stdout.write(self.style.SUCCESS('Index does not exist, safe to proceed'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not check/drop index: {e}'))
                
        self.stdout.write(self.style.SUCCESS('Database index check completed'))
