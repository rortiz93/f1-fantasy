from django import forms
from .models import TeamSelection, Driver, PredictionAnswer, PredictionQuestion

class PredictionAnswerForm(forms.ModelForm):
    class Meta:
        model = PredictionAnswer
        fields = ['answer']

    def __init__(self, *args, **kwargs):
        prediction_question = kwargs.pop('prediction_question', None)
        super().__init__(*args, **kwargs)

        if prediction_question:
            if prediction_question.question_type == 'multiple_choice':
                self.fields['answer'] = forms.ChoiceField(
                    choices=[(option, option) for option in prediction_question.options]
                )
            else:
                self.fields['answer'] = forms.CharField(widget=forms.TextInput())
class TeamSelectionForm(forms.ModelForm):
    # Separate fields for Tier 1 and Tier 2 drivers
    tier_1_driver = forms.ModelChoiceField(
        queryset=Driver.objects.filter(tier=1),
        label="Select a Tier 1 Driver",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    tier_2_drivers = forms.ModelMultipleChoiceField(
        queryset=Driver.objects.filter(tier=2),
        label="Select Tier 2 Drivers",
        widget=forms.CheckboxSelectMultiple
    )
    prediction_answer = forms.CharField(
        required=False,
        label="Prediction Answer",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = TeamSelection
        fields = ['tier_1_driver', 'tier_2_drivers']

    def __init__(self, *args, **kwargs):
        # Custom arguments
        self.prediction_question = kwargs.pop('prediction_question', None)
        self.prediction_answer_instance = kwargs.pop('prediction_answer_instance', None)
        super().__init__(*args, **kwargs)

        # Initialize Tier 1 and Tier 2 driver fields
        self.fields['tier_1_driver'].queryset = Driver.objects.filter(tier=1)
        self.fields['tier_1_driver'].label_from_instance = lambda obj: f"{obj.name} - ${obj.price}M"

        self.fields['tier_2_drivers'].queryset = Driver.objects.filter(tier=2)
        self.fields['tier_2_drivers'].label_from_instance = lambda obj: f"{obj.name} - ${obj.price}M"

        # Prepopulate prediction answer if instance exists
        if self.prediction_answer_instance:
            self.initial['prediction_answer'] = self.prediction_answer_instance.answer

        # Customize prediction_answer field based on the prediction question
        if self.prediction_question:
            if self.prediction_question.question_type == 'multiple_choice':
                self.fields['prediction_answer'] = forms.ChoiceField(
                    choices=[(option, option) for option in self.prediction_question.options],
                    label=self.prediction_question.question_text,
                    widget=forms.Select(attrs={'class': 'form-control'})
                )
            else:
                self.fields['prediction_answer'].label = self.prediction_question.question_text

    def clean(self):
        cleaned_data = super().clean()
        tier_1_driver = cleaned_data.get("tier_1_driver")
        tier_2_drivers = cleaned_data.get("tier_2_drivers")

        # Calculate the total cost
        total_cost = tier_1_driver.price if tier_1_driver else 0
        total_cost += sum(driver.price for driver in tier_2_drivers)

        # Validate budget cap
        if total_cost > 20:
            raise forms.ValidationError("Total cost of drivers exceeds the $20M salary cap.")
        if len(tier_2_drivers) > 4:
            raise forms.ValidationError("You can select up to four Tier 2 drivers.")

      

        cleaned_data['total_cost'] = total_cost
        return cleaned_data

    def save(self, commit=True):
        # Save TeamSelection
        team_selection = super().save(commit=False)
        if commit:
            team_selection.save()
            team_selection.drivers.clear()
            if self.cleaned_data['tier_1_driver']:
                team_selection.drivers.add(self.cleaned_data['tier_1_driver'])
            for driver in self.cleaned_data['tier_2_drivers']:
                team_selection.drivers.add(driver)
            self.save_m2m()

        # Save PredictionAnswer
        if self.prediction_question:
            if not self.prediction_answer_instance:
                prediction_answer = PredictionAnswer(
                    prediction_question=self.prediction_question,
                    team=team_selection.team,
                )
            else:
                prediction_answer = self.prediction_answer_instance
            prediction_answer.answer = self.cleaned_data.get('prediction_answer', "")
            if commit:
                prediction_answer.save()

        return team_selection