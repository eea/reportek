from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from django.shortcuts import render

from reportek.core.models import (
    Country, Obligation, Instrument,
)


def home(request):
    return render(request, "homepage.html", {
        "countries": Country.objects.all(),
    })

def country(request, country):
    try:
        country = Country.objects.get(iso=country.upper())
    except ObjectDoesNotExist:
        raise Http404('No %s matches the given query.' % "instrument")

    return render(request, "country.html", {
        "country": country,
        "instruments": Instrument.objects.for_country(country),
    })

def instrument(request, country, instrument):
    try:
        country = Country.objects.get(iso=country.upper())
        instrument = (
            Instrument.objects.for_country(country.pk).get(pk=instrument)
        )
    except ObjectDoesNotExist:
        raise Http404('No %s matches the given query.' % "instrument")

    return render(request, "instrument.html", {
        "country": country,
        "instrument": instrument,
        "obligations": instrument.obligation_set.for_country(country),
    })

def obligation(request, country, instrument, obligation):
    try:
        country = Country.objects.get(iso=country.upper())
        instrument = (
            Instrument.objects.for_country(country).get(pk=instrument)
        )
        obligation = (
            Obligation.objects.for_country(country)
            .filter(instrument_id=instrument.pk).get(pk=obligation)
        )
    except ObjectDoesNotExist:
        raise Http404('No %s matches the given query.' % "obligation")

    return render(request, "obligation.html", {
        "country": country,
        "instrument": instrument,
        "obligation": obligation,
    })
