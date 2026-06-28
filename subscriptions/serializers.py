from rest_framework import serializers
from .models import Package, Plan, Workshop, WorkshopAttendance

class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = [
            'package_id',
            'nutritionist',
            'name',
            'details',
            'price',
            'num',
            'first_payment_percentage',
            'category',
            'require_consultation',
            'status',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['package_id', 'created_at', 'updated_at']


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = [
            'plan_id',
            'file',
            'description',
            'upload_at',
            'updated_at',
        ]
        read_only_fields = ['plan_id', 'upload_at', 'updated_at']


class WorkshopSerializer(serializers.ModelSerializer):
    is_full = serializers.SerializerMethodField()

    class Meta:
        model = Workshop
        fields = [
            'workshop_id',
            'nutritionist',
            'title',
            'date',
            'time',
            'place',
            'type',
            'overview',
            'img',
            'link',
            'status',
            'num_participants',
            'max_participants',
            'is_full',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['workshop_id', 'created_at', 'updated_at']

    def get_is_full(self, obj):
        return obj.is_full


class WorkshopListSerializer(serializers.ModelSerializer):
    is_full = serializers.SerializerMethodField()

    class Meta:
        model = Workshop
        fields = ['workshop_id', 'title', 'date', 'overview', 'img', 'max_attendees', 'is_full']

    def get_is_full(self, obj):
        return obj.is_full


class WorkshopJoinRequestSerializer(serializers.Serializer):
    workshop = serializers.PrimaryKeyRelatedField(queryset=Workshop.objects.all())


class WorkshopAttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkshopAttendance
        fields = ['id', 'workshop', 'email', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']
