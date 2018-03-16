from tornado.web import RequestHandler, HTTPError
import traceback
import json


class MyAppException(HTTPError):
    pass


class BaseHandler(RequestHandler):
    @property
    def db(self):
        return self.application.db

    def write_error(self, status_code, **kwargs):
        """Overriding tornado error handling."""
        self.set_header('Content-Type', 'application/json')
        if self.settings.get("serve_traceback") and "exc_info" in kwargs:
            # in debug mode, try to send a traceback
            lines = []
            for line in traceback.format_exception(*kwargs["exc_info"]):
                lines.append(line)
            self.set_status(status_code)
            self.finish(json.dumps({
                "status": "error",
                'message': self._reason,
            }))
        else:
            self.set_status(status_code)
            self.finish(json.dumps({
                "status": "error",
                'message': self._reason,
            }))
