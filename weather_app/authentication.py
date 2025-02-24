import keyring


SERVICE_NAME = 'weather_app'
USER_NAME = 'weather_app_user'


class AuthenticationError(Exception):
    pass


class Authenticator:
    """
    Manages the API keys for user.
    """
    @staticmethod
    def store_key(key: str, overwrite: bool = False) -> str:
        """
        Store a key in the system through the use of keyring.

        :param key: string API key.
        :param overwrite: if True, overwrites any previous key present. Default: False.
        :return: a string representing the result of the action.
        """
        current_key = keyring.get_password(SERVICE_NAME, USER_NAME)

        if not current_key:
            keyring.set_password(SERVICE_NAME, USER_NAME, key)
            return 'Stored a new API key.'

        else:
            if overwrite is True:
                keyring.set_password(SERVICE_NAME, USER_NAME, key)
                return 'Overwritten previous API key with new one.'

            else:
                return 'API key already present, use overwrite to update to a new one.'

    @staticmethod
    def authenticate() -> str:
        """
        Retrieves the stored API key (if present) and returns it.

        :return: string representing the API key.
        """
        api_key = keyring.get_password(SERVICE_NAME, USER_NAME)

        if api_key:
            return api_key

        else:
            raise AuthenticationError("Please provide a valid API key through the use of the "
                                      "'main --authenticate' option.")
