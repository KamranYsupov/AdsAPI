from django import forms
from .models import Ad, ExchangeProposal


class AdForm(forms.ModelForm):
    class Meta:
        model = Ad
        fields = ['title', 'description', 'image_url', 'category', 'condition']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class ExchangeProposalForm(forms.ModelForm):
    class Meta:
        model = ExchangeProposal
        fields = ['ad_sender', 'ad_receiver', 'comment']

    def clean(self):
        cleaned_data = super().clean()
        ad_sender = cleaned_data.get('ad_sender')
        ad_receiver = cleaned_data.get('ad_receiver')

        if ad_sender and ad_receiver:
            if ad_sender.user == ad_receiver.user:
                raise forms.ValidationError(
                    {'ad_receiver': 'Вы не можете предложить обмен на свое же объявление'}
                )

            if not ad_sender.is_active:
                raise forms.ValidationError(
                    {'ad_sender': 'Нельзя использовать неактивное объявление'}
                )

            if not ad_receiver.is_active:
                raise forms.ValidationError(
                    {'ad_receiver': 'Нельзя предлагать обмен на неактивное объявление'}
                )

        return cleaned_data
