import keyring


SERVICE_NAME = "weather_app"
USER_NAME = "weather_app_user"


class AuthenticationError(Exception):
    pass


class Authenticator:
    @staticmethod
    def store_key(key: str, overwrite: bool = False) -> str:
        current_key = keyring.get_password(SERVICE_NAME, USER_NAME)

        if not current_key:
            keyring.set_password(SERVICE_NAME, USER_NAME, key)
            return f'Stored a new API key.'

        else:
            if overwrite is True:
                keyring.set_password(SERVICE_NAME, USER_NAME, key)
                return f'Overwritten previous API key with new one.'

            else:
                return f'API key already present, use overwrite to update to a new one.'

    @staticmethod
    def authenticate() -> str:
        api_key = keyring.get_password(SERVICE_NAME, USER_NAME)

        if api_key:
            return api_key

        else:
            raise AuthenticationError("Please provide a valid API key through the use of the "
                                      "'main --authenticate' option.")
