
import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from HOME_AREA.models import COURSES
from INSTRUCTOR.models import BLOCK_LIST

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        user = self.scope["user"]
        self.course = self.scope["url_route"]["kwargs"]["course"]


        #user entered chatroom manually in browser tab
        try:
            course =  COURSES.objects.get(COURSE_NAME=self.course)
        except COURSES.DoesNotExist:
            self.close()
            return
         #kick out from chat room
        if BLOCK_LIST.objects.filter(students=user, instructors=course.instructor).exists():
            self.close()
            return

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        user_name = text_data_json['userName']

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": "chat.message", 
                                    "message": message,
                                    'userName': user_name,}
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event["message"]
        user_name = event["userName"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message, 'userName':user_name}))
