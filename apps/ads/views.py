from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Ad, ExchangeProposal, Category
from .forms import AdForm, ExchangeProposalForm


@login_required
def create_ad(request):
    if request.method == 'POST':
        form = AdForm(request.POST)
        if form.is_valid():
            ad = form.save(commit=False)
            ad.user = request.user
            ad.save()
            return redirect('ad_detail', ad_id=ad.id)
    else:
        form = AdForm()

    return render(
        request,
        'ads/ad_form.html',
        {'form': form}
    )


def ad_detail(request, ad_id):
    ad = get_object_or_404(Ad, id=ad_id)
    return render(request, 'ads/ad_detail.html', {'ad': ad})


@login_required
def edit_ad(request, ad_id):
    ad = get_object_or_404(Ad, id=ad_id)
    if ad.user != request.user:
        return render(
            request,
            'errors/403.html',
            status=403
        )

    if request.method == 'POST':
        form = AdForm(request.POST, instance=ad)
        if form.is_valid():
            form.save()
            return redirect('ad_detail', ad_id=ad.id)
    else:
        form = AdForm(instance=ad)
    return render(
        request,
        'ads/ad_form.html',
        {'form': form}
    )


def ad_list(request):
    query = request.GET.get('q')

    category_id = request.GET.get('category')
    category = None

    condition = request.GET.get('condition')
    condition_value = dict(Ad.Condition.CHOICES).get(condition)

    ads_query_args = tuple()
    ads_query_kwargs = {'is_active': True}

    if query:
        ads_query_args += (
            Q(title__icontains=query) |
            Q(description__icontains=query),
        )
    if category_id:
        ads_query_kwargs['category__id'] = category_id
        category = Category.objects.get(id=category_id)
    if condition_value:
        ads_query_kwargs['condition'] = condition

    ads = Ad.objects.select_related('user', 'category').filter(
        *ads_query_args, **ads_query_kwargs
    )

    paginator = Paginator(ads, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        'ads/ad_list.html',
        {
            'page_obj': page_obj,
            'query': query,
            'current_category': category,
            'current_condition': (condition, condition_value),
            'categories': Category.objects.all(),
            'conditions': Ad.Condition.CHOICES
        }
    )


@login_required
def delete_ad(request, ad_id):
    ad = get_object_or_404(Ad, id=ad_id)
    if ad.user != request.user:
        return render(request, 'errors/403.html', status=403)

    if request.method == 'POST':
        ad.is_active = False
        ad.save()
        return redirect('ad_list')

    return render(
        request,
        'ads/ad_confirm_delete.html',
        {'ad': ad}
    )


@login_required
def create_proposal(request):
    if request.method == 'POST':
        form = ExchangeProposalForm(request.POST)
        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.ad_sender = Ad.objects.get(
                id=request.POST.get('ad_sender_id')
            )
            proposal.save()
            return redirect(
                'proposal_detail',
                proposal_id=proposal.id
            )
    else:
        form = ExchangeProposalForm()
    return render(
        request,
        'ads/proposal_form.html',
        {'form': form}
    )


@login_required
def create_proposal(request):
    user_ads = Ad.objects.filter(user=request.user, is_active=True)

    if request.method == 'POST':
        form = ExchangeProposalForm(request.POST)

        if form.is_valid():
            proposal = form.save(commit=False)
            proposal.save()
            return redirect('proposal_detail', proposal_id=proposal.id)
    else:
        form = ExchangeProposalForm(request.GET)
        form.fields['ad_sender'].queryset = Ad.objects.filter(
            user=request.user,
            is_active=True
        )
        form.fields['ad_receiver'].queryset = (
            Ad.objects
            .filter(is_active=True)
            .exclude(user=request.user)
        )



    return render(request, 'ads/proposal_form.html', {
        'form': form,
        'user_ads': user_ads
    })


@login_required
def exchange_proposal_list(request):
    status = request.GET.get('status')
    sender = request.GET.get('sender')
    receiver = request.GET.get('receiver')

    proposals_query_kwargs = {}

    if status:
        proposals_query_kwargs['status'] = status
    if sender:
        proposals_query_kwargs['ad_sender__user__username'] = sender
    if receiver:
        proposals_query_kwargs['ad_receiver__user__username'] = receiver

    proposals = ExchangeProposal.objects.select_related(
        'ad_sender',
        'ad_sender__user',
        'ad_receiver',
        'ad_receiver__user'
    ).filter(
        Q(ad_sender__user=request.user) |
        Q(ad_receiver__user=request.user),
        **proposals_query_kwargs
    ).order_by('-created_at')

    paginator = Paginator(proposals, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    status_choices = ExchangeProposal.Status.CHOICES

    context = {
        'proposals': page_obj,
        'status_choices': status_choices,
    }

    return render(request, 'ads/proposal_list.html', context)


@login_required
def proposal_detail(request, proposal_id):
    proposal = get_object_or_404(
        ExchangeProposal.objects.select_related(
            'ad_sender',
            'ad_sender__user',
            'ad_receiver',
            'ad_receiver__user'
        ),
        id=proposal_id
    )

    if request.user.id not in [proposal.ad_sender.user_id, proposal.ad_receiver.user_id]:
        return render(request, 'errors/403.html', status=403)

    context = {
        'proposal': proposal,
        'can_respond': (
            request.user.id == proposal.ad_receiver.user_id and
            proposal.status == ExchangeProposal.Status.WAITING
        )
    }
    return render(request, 'ads/proposal_detail.html', context)


@login_required
def update_proposal(request, proposal_id):
    proposal = get_object_or_404(ExchangeProposal, id=proposal_id)

    if request.user != proposal.ad_receiver.user:
        return render(request, 'errors/403.html', status=403)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(ExchangeProposal.Status.CHOICES):

            with transaction.atomic():
                proposal.status = new_status
                proposal.save()

                if new_status == ExchangeProposal.Status.ACCEPTED:
                    proposal.ad_sender.is_active = False
                    proposal.ad_receiver.is_active = False
                    proposal.ad_sender.save()
                    proposal.ad_receiver.save()


                messages.success(request, 'Статус предложения обновлен')
                return redirect('proposal_detail', proposal_id=proposal.id)

    return redirect('proposal_detail', proposal_id=proposal.id)