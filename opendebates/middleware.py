from opendebates.routing import set_thread_readonly_db, set_thread_readwrite_db


class DBRoutingMiddleware(object):
    def process_request(self, request):
        if request.method in ['GET', 'HEAD']:
            set_thread_readonly_db()
        else:
            set_thread_readwrite_db()
        return None

    def process_response(self, request, response):
        set_thread_readwrite_db()
        return response
