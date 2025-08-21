from rest_framework import serializers
from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    name = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'password', 'name', 'role']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["email"],   # fallback, set username = email
            email=validated_data["email"],
            password=validated_data["password"],
            role=validated_data["role"],
            first_name=validated_data["name"]
        )
        return user
