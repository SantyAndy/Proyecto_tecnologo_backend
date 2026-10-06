from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Perfil


class UsuarioSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source='first_name')
    apellido = serializers.CharField(source='last_name')
    ubicacion = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'nombre', 'apellido', 'ubicacion', 'is_staff', 'is_superuser']
        read_only_fields = ['is_staff', 'is_superuser']

    def get_ubicacion(self, obj):
        perfil = getattr(obj, 'perfil', None)
        return perfil.ubicacion if perfil else ''


class RegistroSerializer(serializers.Serializer):
    email = serializers.EmailField()
    nombre = serializers.CharField(max_length=150)
    apellido = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    ubicacion = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')

    def validate_email(self, value):
        # Se compara sin distinguir mayúsculas: "Ana@x.com" y "ana@x.com" son el mismo correo.
        value = value.strip().lower()
        if User.objects.filter(username__iexact=value).exists() or User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError('Ya existe una cuenta con ese correo.')
        return value

    def validate(self, attrs):
        # Con el usuario de referencia, Django también rechaza contraseñas
        # parecidas al correo o al nombre.
        referencia = User(username=attrs['email'], email=attrs['email'],
                          first_name=attrs['nombre'], last_name=attrs['apellido'])
        try:
            validate_password(attrs['password'], referencia)
        except DjangoValidationError as e:
            raise serializers.ValidationError({'password': list(e.messages)})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['nombre'],
            last_name=validated_data['apellido'],
        )
        Perfil.objects.create(usuario=user, ubicacion=validated_data.get('ubicacion', ''))
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
