from django import forms
from .models import TeamSelection, Driver, PredictionAnswer, PredictionQuestion
import json
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
            elif prediction_question.question_type == 'multi_dropdown':
                options_dict = json.loads(prediction_question.options) if isinstance(prediction_question.options, str) else prediction_question.options
                for dropdown_name, choices in options_dict.items():
                    self.fields[dropdown_name] = forms.ChoiceField(choices=[(choice, choice) for choice in choices], required=True)
            else:
                self.fields['answer'] = forms.CharField(widget=forms.TextInput())

class TeamSelectionForm(forms.ModelForm):
    # Standard fields for team selection
    tier_1_driver = forms.ModelChoiceField(
        queryset=Driver.objects.filter(tier=1),
        label="Select a Tier 1 Driver",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    tier_2_drivers = forms.ModelMultipleChoiceField(
        queryset=Driver.objects.filter(tier=2).order_by('-price'),
        label="Select Tier 2 Drivers",
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = TeamSelection
        fields = ['tier_1_driver', 'tier_2_drivers']

    def __init__(self, *args, **kwargs):
        self.prediction_question = kwargs.pop('prediction_question', None)
        self.prediction_answer_instance = kwargs.pop('prediction_answer_instance', None)
        super().__init__(*args, **kwargs)

        self.fields['tier_1_driver'].queryset = Driver.objects.filter(tier=1).order_by('-price')
        self.fields['tier_1_driver'].label_from_instance = lambda obj: f"{obj.name} - ${obj.price}M"

        self.fields['tier_2_drivers'].queryset = Driver.objects.filter(tier=2).order_by('-price')
        self.fields['tier_2_drivers'].label_from_instance = lambda obj: f"{obj.name} - ${obj.price}M"

        # Handle prediction question customization
        if self.prediction_question:
            if self.prediction_question.question_type == 'multiple_choice':
                self.fields['prediction_answer'] = forms.ChoiceField(
                    choices=[(option, option) for option in self.prediction_question.options],
                    label=self.prediction_question.question_text,
                    widget=forms.Select(attrs={'class': 'form-control'})
                )
            elif self.prediction_question.question_type == 'multi_dropdown':
                # Dynamically create fields for multiple dropdowns
                options_dict = json.loads(self.prediction_question.options) if isinstance(self.prediction_question.options, str) else self.prediction_question.options
                for dropdown_name, choices in options_dict.items():
                    self.fields[dropdown_name] = forms.ChoiceField(
                        choices=[(choice, choice) for choice in choices],
                        label=dropdown_name.replace('_', ' ').title(),
                        widget=forms.Select(attrs={'class': 'form-control'}),
                        required=True
                    )

        # Prepopulate the prediction answer fields
        if self.prediction_answer_instance:
            if self.prediction_question.question_type == 'multi_dropdown':
                answer_dict = json.loads(self.prediction_answer_instance.answer) if isinstance(self.prediction_answer_instance.answer, str) else self.prediction_answer_instance.answer
                for dropdown_name in answer_dict:
                    if dropdown_name in self.fields:
                        self.initial[dropdown_name] = answer_dict[dropdown_name]
            else:
                self.initial['prediction_answer'] = self.prediction_answer_instance.answer

    def save(self, commit=True):
        team_selection = super().save(commit=False)
        if commit:
            team_selection.save()
            team_selection.drivers.clear()
            if self.cleaned_data['tier_1_driver']:
                team_selection.drivers.add(self.cleaned_data['tier_1_driver'])
            for driver in self.cleaned_data['tier_2_drivers']:
                team_selection.drivers.add(driver)
            self.save_m2m()

        # Save Prediction Answer
        if self.prediction_question:
            if not self.prediction_answer_instance:
                prediction_answer = PredictionAnswer(
                    prediction_question=self.prediction_question,
                    team=team_selection.team,
                )
            else:
                prediction_answer = self.prediction_answer_instance
            
            # Store multiple answers as JSON
            if self.prediction_question.question_type == 'multi_dropdown':
                prediction_answer.answer = json.dumps({
                    field_name: self.cleaned_data[field_name]
                    for field_name in self.prediction_question.options.keys()
                })
            else:
                prediction_answer.answer = self.cleaned_data.get('prediction_answer', "")

            if commit:
                prediction_answer.save()

        return team_selection