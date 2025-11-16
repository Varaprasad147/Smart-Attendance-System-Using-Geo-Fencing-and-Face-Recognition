from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

	dependencies = [
		('attendance', '0002_initial'),
	]

	operations = [
		migrations.CreateModel(
			name='Company',
			fields=[
				('id', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
				('name', models.CharField(max_length=100, unique=True)),
				('lat', models.DecimalField(max_digits=9, decimal_places=6)),
				('lon', models.DecimalField(max_digits=9, decimal_places=6)),
				('radius', models.DecimalField(max_digits=6, decimal_places=2, default=30.0)),
				('created_at', models.DateTimeField(auto_now_add=True)),
				('updated_at', models.DateTimeField(auto_now=True)),
			],
			options={
				'db_table': 'companies',
				'verbose_name': 'Company',
				'verbose_name_plural': 'Companies',
			},
		),
	]


