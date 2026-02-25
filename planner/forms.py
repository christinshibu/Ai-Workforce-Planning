from django import forms


class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(help_text='Upload hospital workload CSV file.')


class ForecastForm(forms.Form):
    horizon_days = forms.IntegerField(min_value=1, max_value=60, initial=14)
