from django.db import models


class Questions(models.Model):
    question_order = models.IntegerField()
    question = models.CharField(max_length=50)

    regex_pattern = models.CharField(max_length=50, default='')
    invalid_response = models.CharField(max_length=50, default='')

    private_question = models.BooleanField()


class Conversations(models.Model):
    user_id = models.BigIntegerField()
    question_order = models.IntegerField()
    question = models.CharField(max_length=50)
    response = models.CharField(max_length=50)

    regex_pattern = models.CharField(max_length=50, default='')
    invalid_response = models.CharField(max_length=50, default='')

    private_question = models.BooleanField()


class AdminChannel(models.Model):
    group_id = models.BigIntegerField(unique=True)
    title = models.CharField(max_length=50)


class BrokerChannel(models.Model):
    group_id = models.BigIntegerField(unique=True)
    title = models.CharField(max_length=50)


class ConversationIdentifier(models.Model):
    user_id = models.BigIntegerField()
    added = models.DateTimeField()
    quote_id = models.CharField(max_length=50)


class ConversationBackups(models.Model):
    conversation_identifier = models.ForeignKey(ConversationIdentifier, on_delete=models.CASCADE)
    question_order = models.IntegerField()
    question = models.CharField(max_length=50)
    response = models.CharField(max_length=50)

    private_question = models.BooleanField()


class BotAdmins(models.Model):
    user_id = models.BigIntegerField(unique=True)
    name = models.CharField(max_length=50)
