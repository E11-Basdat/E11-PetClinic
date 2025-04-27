from django import forms

class TreatmentForm(forms.Form):
    kunjungan = forms.ChoiceField(
        choices=[],  # Will be populated dynamically in the view
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Kunjungan'
    )
    jenis_perawatan = forms.ChoiceField(
        choices=[],  # Will be populated dynamically in the view
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Jenis Perawatan'
    )
    catatan_medis = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Harap isi catatan medis ya!'}),
        label='Catatan Medis'
    )
    
    def __init__(self, *args, **kwargs):
        kunjungan_choices = kwargs.pop('kunjungan_choices', [])
        perawatan_choices = kwargs.pop('perawatan_choices', [])
        super(TreatmentForm, self).__init__(*args, **kwargs)
        
        self.fields['kunjungan'].choices = kunjungan_choices
        self.fields['jenis_perawatan'].choices = perawatan_choices