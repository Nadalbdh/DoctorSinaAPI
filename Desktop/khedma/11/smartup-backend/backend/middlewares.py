import json
import logging

everything_logger = logging.getLogger("everything_logger")
admin_logger = logging.getLogger("admin_logger")


class LogEverythingMiddleware:
    def __init__(self, next_layer=None):
        """We allow next_layer to be None because old-style middlewares
        won't accept any argument.
        """
        self.get_response = next_layer

    def __call__(self, request):
        """Handle new-style middleware here."""
        body, headers, path = (
            request.body,
            request.headers,
            request.method + ": " + request.path,
        )
        response = self.get_response(request)
        try:
            name = request.user.get_full_name()
        except:
            name = ""
        try:
            if (
                response.content.decode("utf-8").startswith("<!DOCTYPE html>")
                or request.user.is_staff
                or request.path.startswith("/admin")
            ):
                return response

            if path.startswith("POST") and body:
                body_json = json.loads(body)
                if "password" in body_json:
                    body_json["password"] = "******"
                    body = body_json.__str__()

            everything_logger.info("User: %s %s", request.user, name)
            everything_logger.info(
                "Request Header:%s\nRequest Content:%s\nRequest Path:%s",
                headers,
                body[:800],
                path,
            )
            everything_logger.info(
                "Response status code:%s\nResponse Content:%s\n",
                response.status_code,
                response.content[:800],
            )
        except Exception as e:
            everything_logger.exception(e)
        return response


class LogAdminMiddleware:
    def __init__(self, next_layer=None):
        """We allow next_layer to be None because old-style middlewares
        won't accept any argument.
        """
        self.get_response = next_layer

    def __call__(self, request):
        """Handle new-style middleware here."""
        response = self.get_response(request)
        if request.path.startswith("/management/") and response.status_code >= 500:
            try:
                admin_logger.error("Request Path:%s", request.path)
                admin_logger.error(
                    "Response status code:%s\nResponse Content:%s\n",
                    response.status_code,
                    response.content,
                )
            except Exception as e:
                admin_logger.exception(e)
        return response
