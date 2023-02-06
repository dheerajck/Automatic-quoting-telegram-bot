from django.db import models


class Questions(models.Model):
    question_order = models.IntegerField()
    question = models.CharField(max_length=50)


class Conversations(models.Model):
    user_id = models.BigIntegerField()
    question_order = models.IntegerField()
    question = models.CharField(max_length=50)
    response = models.CharField(max_length=50)


class AdminChannel(models.Model):
    group_id = models.BigIntegerField()


class BrokerChannel(models.Model):
    group_id = models.BigIntegerField()


class ConversationBackups(models.Model):
    convesation_id = models.BigIntegerField()
    user_id = models.BigIntegerField()
    question_order = models.IntegerField()
    question = models.CharField(max_length=50)
    response = models.CharField(max_length=50)
