from django import forms
from django.db import models


class Hit(models.Model):
    """
    Saves data about the hit. That means, each time a user access a URL.
    """

    # Timestamp of the hit
    hit_timestamp = models.DateTimeField(auto_now_add=True, editable=False)

    # The user ID is given by a MD5 hash of the email address
    user_id = models.CharField(verbose_name="user id", max_length=32)

    # This is the name of the area where the click was made
    click_area = models.CharField(verbose_name="Click area name", max_length=100, null=True)

    # User agent of the request
    user_agent = models.CharField(max_length=100)

    # OS of the user
    user_os = models.CharField(verbose_name="user's OS", max_length=50, null=True)

    # Browser of the user
    user_browser = models.CharField(verbose_name="user's browser", max_length=50, null=True)

    # IP of the requesting user
    ip_address = models.GenericIPAddressField()

    # HTTP Headers
    http_headers = models.TextField()

    # Request path
    request_path = models.CharField(max_length=256)

    # Additional information
    additional_info = models.TextField(verbose_name="additional information", null=True)

    def __str__(self):
        """
        Return string representation
        :return:
        """
        string = "Hit on %s from %s" % (self.hit_timestamp.strftime('%Y-%m-%d %H:%M'), self.ip_address)

        if self.click_area is not None:
            string += " (%s)" % self.click_area

        return string


class Target(models.Model):
    """
    Maintains the target list.
    """

    # Email of the user
    email = models.EmailField(unique=True)

    # User ID, given by the hash of the field
    user_id = models.CharField(max_length=32)


    def __str__(self):
        """
        Return string representation.
        :return:
        """
        return "Email (%s)" % self.email
