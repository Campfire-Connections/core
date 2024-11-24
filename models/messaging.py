# core/models/messaging.py

from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class Message(models.Model):
    """
    Represents a message sent between users.
    
    Args:
        sender: The user who sent the message.
        receiver: The user who received the message.
        content: The content of the message.
        timestamp: The timestamp when the message was sent.
        read: Indicates if the message has been read.
    """
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f'Message from {self.sender} to {self.receiver}'


class Notification(models.Model):
    """
    Represents a notification for a user.
    
    Args:
        user: The user associated with the notification.
        message: The message related to the notification.
        content: The content of the notification.
        timestamp: The timestamp when the notification was created.
        read: Indicates if the notification has been read.
    """
    user = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE)
    message = models.ForeignKey(Message, related_name='notifications', on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f'Notification for {self.user}'
