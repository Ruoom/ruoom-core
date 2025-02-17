from registration.controller import return_business_id_for_domain

class AssignBusinessIdFromDomainMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            request.user.profile.business_id = return_business_id_for_domain(request.META.get('HTTP_HOST', ''))
            request.user.profile.save()
        response = self.get_response(request)

        return response