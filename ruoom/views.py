import base64
import re
from io import BytesIO
from django.http import (
    HttpResponse, HttpResponseNotAllowed, HttpResponseBadRequest
)
from django.shortcuts import render
from django.core.files.uploadedfile import InMemoryUploadedFile
from administration.models import Business
from django.views.generic import View
from django.contrib.auth.views import PasswordResetView
from django.shortcuts import render, redirect
from registration.models import Profile
from registration.controller import return_business_id_for_domain

def success(request):
    return HttpResponse("Successful Operation.")

def unsuccess(request):
    return HttpResponse("Unsuccessful Operation.")

def handler400(request, exception, template_name="error.html"):
    print(f"Rendering template: {template_name}")
    response = render(request, template_name)
    response.status_code = 400
    return response

def handler403(request, exception, template_name="error.html"):
    print(f"Rendering template: {template_name}")
    return render(request, template_name, status=403)

def handler404(request, exception, template_name="error.html"):
    print(f"Rendering template: {template_name}")
    response = render(request, template_name)
    response.status_code = 404
    return response

def handler500(request, template_name="error.html", *args, **argv):
    print(f"Rendering template: {template_name}")
    return render(request, template_name, status=500)

class SavePictureView(View):
    """Save different kind of image."""

    image_field_name = "image_field_name"
    image_upload_name = "image_upload_name"

    def get_instance(self, request):
        pass

    def post(self, request, *args, **kwargs):
        # Load instance
        instance, response = self.get_instance(request)
        if response is not None:
            return response

        # Load base64 file into request files
        try:
            file = BytesIO(
                base64.b64decode(
                    re.sub(
                        "data:image/jpeg;base64", "", 
                        request.POST.get("file")
                    )
                )
            )
            image = InMemoryUploadedFile(
                file,
                field_name=self.image_field_name,
                name=f"{self.image_field_name}_{instance.pk}.jpg",
                content_type="image/jpeg",
                size=len(file.getvalue()),
                charset=None
            )
        except Exception as err_msg:
            return HttpResponseBadRequest(
                f"Fail upload {self.image_upload_name}, detail: %s" % err_msg
            )

        # Load form with files
        try:
            instance.__dict__[self.image_field_name] = image
            instance.save()
        except Exception as err_msg:
            return HttpResponseBadRequest(
                f"Fail upload {self.image_upload_name}, detail: %s" % err_msg
            )

        return HttpResponse("Success.", status=200)


class SaveStudioPictureView(SavePictureView):
    """Save studio image."""

    image_field_name = "studio_image"
    image_upload_name = "studio image"

    def get_instance(self, request):
        # Load profile instance
        profile = getattr(request.user, "profile", None)
        if not profile:
            return None, HttpResponseBadRequest("User profile not found.")

        studio = Business.objects.filter(
            business_id=profile.business_id
        ).first()
        if not studio:
            return HttpResponseBadRequest("Studio settings not found.")

        return studio, None


class SaveProfilePictureView(SavePictureView):
    """Save staff image."""

    image_field_name = "profile_image"
    image_upload_name = "profile image"

    def get_instance(self, request):
        # Load profile instance
        profile = getattr(request.user, "profile", None)
        if not profile:
            return None, HttpResponseBadRequest("User profile not found.")

        return profile, None


def save_picture(request, **kwargs):
    """Save different kind of image."""
    # Handle other request than post
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    # Load instance
    #instance = get_instance

    # Load profile instance
    profile = getattr(request.user, "profile", None)
    if not profile:
        return HttpResponseBadRequest("User profile not found.")

    studio = Business.objects.filter(
        business_id=profile.business_id
    ).first()
    if not studio:
        return HttpResponseBadRequest("Studio settings not found.")

    # Load base64 file into request files
    try:
        file = BytesIO(
            base64.b64decode(
                re.sub(
                    "data:image/jpeg;base64", "", 
                    request.POST.get("file")
                )
            )
        )
        image = InMemoryUploadedFile(
            file,
            field_name="studio_image",
            name=f"studio_image_{studio.pk}.jpg",
            content_type="image/jpeg",
            size=len(file.getvalue()),
            charset=None
        )
    except Exception as err_msg:
        return HttpResponseBadRequest(
            "Fail upload studio image, detail: %s" % err_msg
        )

    # Load form with files
    try:
        studio.studio_image = image
        studio.save()
    except Exception as err_msg:
        return HttpResponseBadRequest(
            "Fail upload profile image, detail: %s" % err_msg
        )

    return HttpResponse("Success.", status=200)


class PasswordResetViewRuoom(PasswordResetView):

    def post(self, request, *args, **kwargs):
        """Customize post method."""
        # Load params
        email = request.POST.get('email')
        business_id = return_business_id_for_domain(request.META.get('HTTP_HOST', ''))
        profile = Profile.objects.filter(email=email, business_id=business_id).first()
        user = super(Profile,profile)
        biz = Business.objects.get(business_id=business_id)

        # Assign extra context
        self.extra_email_context = {
            "Customer": user,
            "business_name":biz.name,
            "business_email":biz.contact_email,
            "business_website":biz.business_website,
            "customer_logo":biz.studio_image
        }

        # Only reset if user exist       
        if profile:
            print("Sending password reset email to %s" % email)
            return super(PasswordResetViewRuoom, self).post(request, *args, **kwargs)
        else:
            print("No matching account for business_id: %s and email: %s" % (business_id, email))
            return redirect('/accounts/password_reset/done/')