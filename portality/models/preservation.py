from portality.dao import DomainObject
from datetime import datetime


class Preserve(DomainObject):
    """Model class for preservation feature"""
    __type__ = "preserve"

    @property
    def status(self):
        return self.data.get("status")

    @status.setter
    def status(self, value):
        self.data["status"] = value

    @property
    def filename(self):
        return self.data.get("filename")

    @property
    def owner(self):
        return self.data.get("owner")

    @property
    def created_timestamp(self):
        if "created_date" not in self.data:
            return None
        return datetime.strptime(self.data["created_date"], "%Y-%m-%dT%H:%M:%SZ")

    @property
    def error(self):
        return self.data.get("error")

    @property
    def error_details(self):
        return self.data.get("error_details")

    def initiated(self, owner, filename, status="initiated"):
        self.data["filename"] = filename
        self.data["owner"] = owner
        self.status = status

    def validated(self):
        self.status = "validated"

    def pending(self):
        self.status = "pending"

    def uploaded_to_ia(self):
        self.status = "Uploaded to IA"

    def failed(self, message, details=None):
        self.status = "failed"
        self.data["error"] = message
        if details is not None:
            self.data["error_details"] = details