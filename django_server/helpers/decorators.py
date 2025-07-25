from functools import wraps

from django.http import JsonResponse
from rest_framework.request import Request


def required_query_params(required_params):
    """
    Decorator that checks if all required query parameters are present in the URL.
    Works with both function-based and class-based views.

    Args:
        required_params: List of required query parameter names

    Returns:
        Decorated function or JsonResponse with error message if parameters are missing
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            # First argument is either request (for function views) or self (for class methods)
            # Second argument would be request for class methods
            if len(args) > 1 and hasattr(args[1], "query_params"):
                # Class method: self, request, *args
                request = args[1]
            elif len(args) > 0 and hasattr(args[0], "query_params"):
                # Function view: request, *args
                request = args[0]
            else:
                # No valid request object found
                return JsonResponse(
                    {"error": "No request object found"},
                    status=400,
                )

            missing_params = [
                param for param in required_params if param not in request.query_params
            ]

            if missing_params:
                return JsonResponse(
                    {
                        "error": "Missing required query parameters",
                        "missing_params": missing_params,
                    },
                    status=400,
                )

            return view_func(*args, **kwargs)

        return wrapper

    return decorator


def required_body_params(required_params):
    """
    Decorator that checks if all required body parameters are present in the request body.
    Works with both function-based and class-based views.

    Args:
        required_params: List of required body parameter names

    Returns:
        Decorated function or JsonResponse with error message if parameters are missing
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            # First argument is either request (for function views) or self (for class methods)
            # Second argument would be request for class methods
            if len(args) > 1 and hasattr(args[1], "data"):
                # Class method: self, request, *args
                request = args[1]
            elif len(args) > 0:
                # Function view: request, *args
                request = args[0]
            else:
                # No arguments provided
                return JsonResponse(
                    {"error": "No request object found"},
                    status=400,
                )

            try:
                missing_params = [
                    param for param in required_params if param not in request.data
                ]

                if missing_params:
                    return JsonResponse(
                        {
                            "error": "Missing required body parameters",
                            "missing_params": missing_params,
                        },
                        status=400,
                    )

                return view_func(*args, **kwargs)

            except AttributeError as e:
                print(e)
                return JsonResponse(
                    {"error": "Invalid request body"},
                    status=400,
                )

        return wrapper

    return decorator
