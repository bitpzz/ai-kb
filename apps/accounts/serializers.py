from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email, RegexValidator


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, validators=[validate_password])
    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")

    def validate_username(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("用户名至少 3 个字符")
        if len(value) > 30:
            raise serializers.ValidationError("用户名最多 30 个字符")
        if not value.replace("_", "").isalnum():
            raise serializers.ValidationError("用户名只能包含字母、数字和下划线")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("用户名已被注册")
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")
