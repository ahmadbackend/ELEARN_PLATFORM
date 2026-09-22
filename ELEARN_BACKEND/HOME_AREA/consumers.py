"""
Websocket consumers. The platform exposes exactly one room: the private
learner <-> tutor conversation behind ws/peerchat/<instructor>/<student>/.

The message is saved here from the authenticated scope user, never from
anything the browser sends, so a client cannot post as somebody else.
"""
import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from django.contrib.contenttypes.models import ContentType

from HOME_AREA.access import resolve_peer_pair, can_peer_chat
from HOME_AREA.models import PeerChat

MESSAGE_MAX = 1000


class PeerChatConsumer(WebsocketConsumer):
    def connect(self):
        user = self.scope['user']
        instructor_name = self.scope['url_route']['kwargs']['instructor']
        student_name = self.scope['url_route']['kwargs']['student']

        pair = resolve_peer_pair(user, instructor_name, student_name)
        # not enrolled, blocked, or trying to read somebody else's room
        if pair is None:
            self.close()
            return
        self.instructor, self.student = pair
        self.user = user
        self.content_type = ContentType.objects.get_for_model(user.__class__)
        self.room_group_name = PeerChat.group_name(self.instructor, self.student)

        async_to_sync(self.channel_layer.group_add)(self.room_group_name, self.channel_name)
        self.accept()

    def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)

    def receive(self, text_data):
        try:
            message = json.loads(text_data).get('message', '')
        except (ValueError, AttributeError):
            return
        message = message.strip() if isinstance(message, str) else ''
        if not message:
            return
        # re-checked on every message so a drop or a block takes effect immediately
        if not can_peer_chat(self.student, self.instructor):
            self.close()
            return

        chat = PeerChat.objects.create(
            student=self.student,
            instructor=self.instructor,
            message=message[:MESSAGE_MAX],
            content_type=self.content_type,
            object_id=self.user.id,
        )

        async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
            'type': 'peer.message',
            'message': chat.message,
            'userName': self.user.USER_NAME,
            'userCat': self.user.user_cat,
            'timeStamp': chat.TimeStamp.isoformat(),
        })

    def peer_message(self, event):
        self.send(text_data=json.dumps({
            'message': event['message'],
            'userName': event['userName'],
            'userCat': event['userCat'],
            'timeStamp': event['timeStamp'],
        }))
