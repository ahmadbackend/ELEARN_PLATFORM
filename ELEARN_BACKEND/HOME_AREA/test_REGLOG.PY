from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from INSTRUCTOR.models import INSTRUCTOR, CODE_GENERATOR_INSTR
from unittest.mock import patch
from .forms import instructor

def test_instructor_reg_form_valid_data(self, mock_send_email):
    # Mocking an image file upload
    picture = SimpleUploadedFile(name='example.jpeg', content=b'', content_type='image/jpeg')
    
    # Data to submit to the form
    data = {
        'EMAIL': 'test@example.com',
        'PASSWORD': 'password123S',
        'FIRST_NAME': 'John',
        'LAST_NAME': 'Doe',
        "USER_NAME":"KINGKONG",
        "PHONE":"2365985",
        'picture': picture  
    }

    response = self.client.post(self.url, data, follow=True)
    
    # Check form errors
    form = response.context['form']
    if not form.is_valid():
        print(form.errors)  # Print any form errors to the console for debugging
    
    # Assert that the INSTRUCTOR object is created
    self.assertTrue(INSTRUCTOR.objects.filter(EMAIL='test@example.com').exists())
    self.assertTrue(CODE_GENERATOR_INSTR.objects.filter(EMAIL='test@example.com').exists())

    # Check that send_email was called with the correct arguments
    self.assertTrue(mock_send_email.called)
    self.assertIn('test@example.com', mock_send_email.call_args[0])

    def test_instructor_reg_form_invalid_data(self):
        # Invalid data (e.g., missing required fields)
        data = {
            'EMAIL': '',
            'PASSWORD': '',
            
        }

        response = self.client.post(self.url, data)

        # Check that the form is invalid and the same template is rendered with errors
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'instructorForm.html')
        self.assertFalse(INSTRUCTOR.objects.filter(EMAIL='').exists())
