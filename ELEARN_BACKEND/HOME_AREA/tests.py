from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from INSTRUCTOR.models import INSTRUCTOR, CODE_GENERATOR_INSTR
from unittest.mock import patch
from STUDENT.models import STUDENT, CODE_GENERATOR
from .forms import instructor
import os
from .tasks import send_email
from ELEARN_BACKEND.settings import BASE_DIR
# instructor registeration testing 
class InstructorFormTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('HOME_AREA:instructor_reg_form') 
    @patch('HOME_AREA.REGLOG.instructor_reg_form')  
    def test_instructor_reg_form_valid_data(self, mock_send_email):
        #so tedious to fake image 
        pathway =BASE_DIR / 'media/forms1.png'
        with open(pathway, 'rb') as img:
            picture = SimpleUploadedFile(name='forms1.png', content=img.read(), content_type='image/png')        
        # Data to submit to the form
        data = {
            'EMAIL': 'test@example.com',
            'PASSWORD': 'password123S',
            'FIRST_NAME': 'John',
            'LAST_NAME': 'Doe',
            "USER_NAME": "KINGKONG",
            "PHONE": "2365985",
            'PICTURE': picture  
        }

        response = self.client.post(self.url, data, follow=True)
        
        # Check form errors
        form = response.context['form']
        if not form.is_valid():
            print(form.errors)  # Print any form errors to the console for debugging
        
        # Assert that the INSTRUCTOR object is created
        instructor_exists = INSTRUCTOR.objects.filter(EMAIL='test@example.com').exists()
        print(f"INSTRUCTOR exists: {instructor_exists}")

        self.assertTrue(INSTRUCTOR.objects.filter(EMAIL='test@example.com').exists())
        print(INSTRUCTOR.objects.filter(EMAIL='test@example.com'))
        self.assertTrue(CODE_GENERATOR_INSTR.objects.filter(EMAIL='test@example.com').exists())

  

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
        ##------------------------------------------------------------------------------##################
        #student registeration testing 

class StudentFormTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('HOME_AREA:student_reg_form') 
    @patch('HOME_AREA.REGLOG.student_reg_form')  
    def test_student_reg_form_valid_data(self, mock_send_email):
        #so tedious to fake image 
        pathway =BASE_DIR / 'media/forms1.png'
        with open(pathway, 'rb') as img:
            picture = SimpleUploadedFile(name='forms1.png', content=img.read(), content_type='image/png')        
        # Data to submit to the form
        data = {
            'EMAIL': 'test@example.com',
            'PASSWORD': 'password123S',
            'FIRST_NAME': 'John',
            'LAST_NAME': 'Doe',
            "USER_NAME": "KINGKONG",
            "PHONE": "2365985",
            'PICTURE': picture  
        }

        response = self.client.post(self.url, data, follow=True)
        
        # Check form errors
        form = response.context['form']
        if not form.is_valid():
            print(form.errors)  # Print any form errors to the console for debugging
        
        # Assert that the INSTRUCTOR object is created
        student_exists = STUDENT.objects.filter(EMAIL='test@example.com').exists()

        self.assertTrue(STUDENT.objects.filter(EMAIL='test@example.com').exists())
        print(STUDENT.objects.filter(EMAIL='test@example.com'))
        self.assertTrue(CODE_GENERATOR.objects.filter(EMAIL='test@example.com').exists())

  

    def test_student_reg_form_invalid_data(self):
        # Invalid data (e.g., missing required fields)
        data = {
            'EMAIL': '',
            'PASSWORD': '',
        }

        response = self.client.post(self.url, data)

        # Check that the form is invalid and the same template is rendered with errors
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'studentForm.html')
        self.assertFalse(STUDENT.objects.filter(EMAIL='').exists())
        ###################################################################################
                            ## testing log in functionality ##############
