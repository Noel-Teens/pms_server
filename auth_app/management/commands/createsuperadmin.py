from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates a superuser with admin role'

    def add_arguments(self, parser):
        parser.add_argument('--username', dest='username', default=None, help='Specifies the username for the superuser.')
        parser.add_argument('--email', dest='email', default=None, help='Specifies the email for the superuser.')
        parser.add_argument('--password', dest='password', default=None, help='Specifies the password for the superuser.')
        parser.add_argument('--noinput', action='store_true', dest='noinput', help='Tells Django to NOT prompt the user for input of any kind.')

    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        password = options['password']
        interactive = not options['noinput']

        # If not provided, prompt for username/email/password
        if interactive:
            if username is None:
                username = input('Username: ')
            if email is None:
                email = input('Email address: ')
            if password is None:
                password = input('Password: ')

        if not username or not email or not password:
            self.stdout.write(self.style.ERROR('Error: username, email, and password are required'))
            return

        try:
            with transaction.atomic():
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    password=password
                )
                # Set the role to ADMIN
                user.role = 'ADMIN'
                user.save()

            self.stdout.write(self.style.SUCCESS(f'Superadmin user {username} created successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating superadmin user: {str(e)}'))