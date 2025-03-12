from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    created_at and updated_at fields.
    """
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteModel(models.Model):
    """
    An abstract base class model that provides a is_deleted
    field for soft deletion.
    """
    is_deleted = models.BooleanField(_('deleted'), default=False)

    class Meta:
        abstract = True

    def soft_delete(self):
        """
        Soft delete the object (set is_deleted=True).
        """
        self.is_deleted = True
        self.save()

    def restore(self):
        """
        Restore a soft-deleted object.
        """
        self.is_deleted = False
        self.save()
