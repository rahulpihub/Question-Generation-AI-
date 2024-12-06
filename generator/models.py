from djongo import models

class Question(models.Model):
    topic = models.CharField(max_length=255)
    subtopic = models.CharField(max_length=255)
    level = models.CharField(max_length=50)
    question_type = models.CharField(max_length=50)
    question = models.TextField()
    option_1 = models.CharField(max_length=255, blank=True, null=True)
    option_2 = models.CharField(max_length=255, blank=True, null=True)
    option_3 = models.CharField(max_length=255, blank=True, null=True)
    option_4 = models.CharField(max_length=255, blank=True, null=True)
    answer = models.CharField(max_length=255)

    def __str__(self):
        return f"Question on {self.topic} - {self.question}"
