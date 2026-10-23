from django.urls import path
from .views import login_view, logout_view, user_management

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('users/', user_management, name='user_management'),
]
