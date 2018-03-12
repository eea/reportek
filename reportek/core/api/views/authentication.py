from rest_framework import viewsets, mixins, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.response import Response


class AuthTokenViewSet(mixins.CreateModelMixin,
                       mixins.DestroyModelMixin,
                       viewsets.GenericViewSet):

    """
    Viewset for obtaining and removing DRF authentication tokens.

    Supported methods:

    post:
        For use at login, to get or create a token for the user with
        the provided username/password.
        POST data must contain:
        ```
        {
            "username": <username>,
            "password": <password>
        }
        ```

    delete:
        For use at logout, to delete the token of the current user.
        The current user's token must match the token provided in the URL (auth-token/<token>)
    """

    queryset = Token.objects.all()
    lookup_field = 'key'
    lookup_url_kwarg = 'token'

    def create(self, request, *args, **kwargs):
        serializer = AuthTokenSerializer(data=request.data,
                                         context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        try:
            user_token = Token.objects.get(user=request.user)
        except Token.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if user_token != instance:
            return Response(status=status.HTTP_404_NOT_FOUND)

        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
