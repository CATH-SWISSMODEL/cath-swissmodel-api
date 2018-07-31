from django.shortcuts import render

# Create your views here.

from rest_framework import generics
from .serializers import SelectTemplateQuerySerializer, SelectTemplateResultsSerializer
from .models import SelectTemplateTask

class SelectTemplateTaskCreateView(generics.ListCreateAPIView):
    """Search CATH with a protein sequence to identify the best template structure 
    and alignment to use for 3D modelling."""
    queryset = SelectTemplateTask.objects.all()
    serializer_class = SelectTemplateQuerySerializer

    def perform_create(self, serializer):
        """Save the post data when creating a new task."""
        serializer.save()

class SelectTemplateTaskDetailsView(generics.RetrieveDestroyAPIView):
    """Get status and results for previously submitted template search tasks."""

    queryset = SelectTemplateTask.objects.all()
    serializer_class = SelectTemplateResultsSerializer
