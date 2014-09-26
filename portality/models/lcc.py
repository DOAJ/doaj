from portality.dao import DomainObject

class LCC(DomainObject):
    __type__ = "lcc"

    def save(self, **kwargs):
        self.set_id("lcc")
        super(LCC, self).save(**kwargs)