from django.db import models
import hashlib

# constants
STATUS_INITIALISED="Initialised"
STATUS_QUEUEING="Queueing"
STATUS_RUNNING="Running"
STATUS_COMPLETED="Completed"
STATUS_ERROR="Error"
STATUS_UNKNOWN="Unknown"
STATUS_CHOICES=( (st, st) for st in 
    (STATUS_INITIALISED, STATUS_QUEUEING, STATUS_RUNNING, STATUS_COMPLETED, STATUS_ERROR, ) )

# Create your models here.

class SelectTemplateTask(models.Model):
    """This class represents the model used for selecting the best structural template 
    for a protein sequence from CATH."""
    fasta = models.CharField(max_length=2000, blank=False, unique=False)

    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=STATUS_INITIALISED)
    message = models.CharField(max_length=150)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    results = models.CharField(max_length=5000, blank=True)

    ip = models.GenericIPAddressField(default="0.0.0.0")

    def get_unique_key(self):
        m = hashlib.md5()
        m.update(str(self.fasta).encode('utf-8'))
        task_id = m.hexdigest()
        return task_id

    task_id = property( get_unique_key )

    def __str__(self):
        """Return a human readable representation of the select template task instance."""
        return "[{}] status:{}, started:{}, last_updated:{}".format( 
            self.task_id, self.status, self.date_created, self.date_modified )
