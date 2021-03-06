from django.conf import settings
from django.urls import reverse
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.shortcuts import get_current_site
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import (
                            RegisterSerializer,
                            EmailVerificationSerializer,
                            LoginSerializer,
                            ResetPasswordEmailSerializer,
                            SetNewPasswordSerializer
                        )
from .models import User
from .utils import Util
from .renderers import UserRender
import jwt


class RegisterView(generics.GenericAPIView):

    serializer_class = RegisterSerializer
    renderer_classes = (UserRender,)

    def post(self, request):
        user = request.data
        serializer = self.serializer_class(data=user)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        user_data = serializer.data
        user = User.objects.get(email=user_data['email'])

        token = RefreshToken.for_user(user).access_token
        current_site = get_current_site(request).domain
        relative_link = reverse('email-verify')

        absolute_url = 'http://'+current_site+relative_link+"?token="+str(token)
        email_body = 'Olá '+user.username+' Clique no link abaixo para verificar o seu email \n' + absolute_url
        data = {'email_body': email_body,
                'email_subject': 'Virificando email',
                'email_to': user.email}
        Util.send_email(data)

        return Response(user_data, status=status.HTTP_201_CREATED)


class VerifyEmail(views.APIView):
    serializer_class = EmailVerificationSerializer

    token_param_config = openapi.Parameter(
        'token', in_=openapi.IN_QUERY, description='Description', type=openapi.TYPE_STRING)

    @swagger_auto_schema(manual_parameters=[token_param_config])
    def get(self, request):
        token = request.GET.get('token')
        try:
            payload = jwt.decode(token, settings.SECRET_KEY)
            user = User.objects.get(id=payload['user_id'])
            if not user.is_verified:
                user.is_verified = True
                user.save()

            return Response({'email': 'Email successfully activated'},
                            status=status.HTTP_200_OK)
        except jwt.ExpiredSignatureError:
            return Response(
                {'error': 'Your activation link has already been expired'},
                status=status.HTTP_404_NOT_FOUND)
        except jwt.exceptions.DecodeError:
            return Response(
                {'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(generics.GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ResetPasswordEmailAPIView(generics.GenericAPIView):
    serializer_class = ResetPasswordEmailSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        email = request.data['email']

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            current_site = get_current_site(request=request).domain
            relative_link = reverse('password-reset-confirm', kwargs={'uidb64': uidb64, 'token': token})
            absolute_url = 'http://' + current_site + relative_link

            email_body = 'Olá, clique no link abaixo para resetar a sua senha \n' + absolute_url
            data = {'email_body': email_body,
                    'email_subject': 'Reset password',
                    'email_to': user.email}
            Util.send_email(data)
        return Response({'success': 'Enviamos um link para resetar a sua senha'}, status=status.HTTP_200_OK)


class PasswordTokenCheckAPI(generics.GenericAPIView):

    def get(self, request, uidb64, token):

        try:
            id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                return Response(
                    {'error': 'Token is not valid, please request a new one'}, status=status.HTTP_401_UNAUTHORIZED)

            return Response(
                {'succes': True, 'message': 'Credentials valid', 'uidb64': uidb64, 'token': token},
                status=status.HTTP_200_OK)

        except DjangoUnicodeDecodeError:
            return Response(
                {'error': 'Token is not valid, please request a new one'}, status=status.HTTP_401_UNAUTHORIZED)


class SetNewPasswordAPIView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {'success': True, 'message': 'Password reset success'}, status=status.HTTP_200_OK)
