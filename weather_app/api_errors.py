error_code_dict: dict[int, str] = {
    1002: 'API key not provided.',
    1003: "Parameter 'q' not provided.",
    1005: 'API request url is invalid',
    1006: "No location found matching parameter 'q'",
    2006: 'API key provided is invalid',
    2007: 'API key has exceeded calls per month quota.',
    2008: 'API key has been disabled.',
    2009: 'API key does not have access to the resource. / '
          'Please check pricing page for what is allowed in your API subscription plan.',
    9000: 'Json body passed in bulk request is invalid. Please make sure it is valid json with utf-8 encoding.',
    9001: 'Json body contains too many locations for bulk request. Please keep it below 50 in a single request.',
    9999: 'Internal application error.'
}

status_error_dict: dict[int, int] = {
    1002: 401,
    1003: 400,
    1005: 400,
    1006: 400,
    2006: 401,
    2007: 403,
    2008: 403,
    2009: 403,
    9000: 400,
    9001: 400,
    9999: 400,
}