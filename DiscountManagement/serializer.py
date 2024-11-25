from rest_framework import serializers
from oscar.core.loading import get_model

Category = get_model("catalogue", "Category")


class CategorySerilaizer(serializers.ModelSerializer):
    category_bread_crump = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "category_bread_crump"]

    def get_category_bread_crump(self, obj):
        return obj.full_name
