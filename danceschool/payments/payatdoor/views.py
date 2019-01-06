from django.http import JsonResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone

from danceschool.core.constants import getConstant, INVOICE_VALIDATION_STR
from danceschool.core.models import Invoice, TemporaryRegistration, CashPaymentRecord

from .forms import WillPayAtDoorForm, DoorPaymentForm
from .models import PayAtDoorFormModel

import logging
from datetime import timedelta


# Define logger for this file
logger = logging.getLogger(__name__)


def handle_willpayatdoor(request):
    logger.info('Received request for future payment at the door.')
    form = WillPayAtDoorForm(request.POST)

    if form.is_valid():
        tr = form.cleaned_data.get('registration')
        instance = form.cleaned_data.get('instance')

        invoice = Invoice.get_or_create_from_registration(
            tr,
            submissionUser=form.cleaned_data.get('submissionUser'),
        )
        invoice.finalRegistration = tr.finalize()
        invoice.save()
        if instance:
            return HttpResponseRedirect(instance.successPage.get_absolute_url())
    return HttpResponseBadRequest()
    
def handle_payatdoor(request):

    logger.info('Received request for At-the-door payment.')
    form = DoorPaymentForm(request.POST)

    if form.is_valid():
        invoice = form.cleaned_data.get('invoice')
        instance = form.cleaned_data.get('instance')
        amountPaid = form.cleaned_data.get('amountPaid')
        subUser = form.cleaned_data.get('submissionUser')

        payment = CashPaymentRecord.objects.create(
            invoice=invoice,amount=amountPaid,
            status=CashPaymentRecord.PaymentStatus.collected,
            submissionUser=subUser,collectedByUser=subUser,
        )
        invoice.processPayment(
            amount=amountPaid,fees=0,paidOnline=False,methodName='At-the-door payment',
            submissionUser=subUser,collectedByUser=subUser,
        )

        if instance:
            return HttpResponseRedirect(instance.successPage.get_absolute_url())
    return HttpResponseBadRequest()
