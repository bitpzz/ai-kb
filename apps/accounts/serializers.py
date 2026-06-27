from rest_framework import serializers
from django.contrib.auth.models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")

    def validate_username(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("用户名至少 3 个字符")
        if len(value) > 30:
            raise serializers.ValidationError("用户名最多 30 个字符")
        if not value.replace("_", "").replace("-", "").isalnum():
            raise serializers.ValidationError("用户名只能包含字母、数字、下划线和横线")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("用户名已被注册")
        return value

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("密码至少 8 位")
        if value.isdigit() or value.isalpha():
            raise serializers.ValidationError("密码需包含字母和数字")
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
