from doajtest.fixtures.v2.applications import ApplicationFixtureFactory
import string, random
from portality import models
from portality import constants
from portality.lib import dates
from datetime import datetime
from copy import deepcopy
from typing import Union, List
import time


class ResolutionException(Exception):
    def __init__(self, msg):
        self.msg = msg
        super(ResolutionException, self).__init__()


class FixtureFactory():
    @classmethod
    def make(cls, *args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def create_random_str(cls, n_char=10):
        s = string.ascii_letters + string.digits
        return ''.join(random.choices(s, k=n_char))

    @classmethod
    def factor(cls, cmds, on_complete=None):
        posts = []

        results = {}
        # first, all the simple constructs
        for name, cmd in cmds.items():
            if isinstance(cmd, list):
                for i, entry in enumerate(cmd):
                    res = cls._run_cmd(entry)
                    if res is not None:
                        if name not in results:
                            results[name] = []
                        results[name].append(res)
                    if "post" in entry[1]:
                        posts.append({"name": name, "result_num": len(results[name]) - 1, "cmd_num": i})
            else:
                res = cls._run_cmd(cmd)
                if res is not None:
                    results[name] = res
                if "post" in cmd[1]:
                    posts.append({"name": name})

        # second all those with substitutions, which may fail on their try if their dependencies have not yet been made,
        # in which case we record them as requiring a revisits
        revisits = []
        for name, cmd in cmds.items():
            if isinstance(cmd, list):
                for i, entry in enumerate(cmd):
                    res, revisit = cls._run_subbed_cmd(entry, results)
                    if res is not None:
                        if name not in results:
                            results[name] = []
                        results[name].append(res)
                    if revisit:
                        revisits.append({"name": name, "result_num": len(results[name]) - 1, "cmd_num": i})
                    if "post" in entry[1]:
                        posts.append({"name": name, "result_num": len(results[name]) - 1, "cmd_num": i})
            else:
                res, revisit = cls._run_subbed_cmd(cmd, results)
                if res is not None:
                    results[name] = res
                if revisit:
                    revisits.append({"name": name})
                if "post" in cmd[1]:
                    posts.append({"name": name})

        # for any creations which errored during initial construction, we continually revisit them until
        # they are all resolved or we cannot resolve them all
        while len(revisits) > 0:
            still_revisit = []
            for r in revisits:
                cmd = cmds[r["name"]]
                if "cmd_num" in r:
                    cmd = cmd[r["cmd_num"]]
                    #current = results[r["name"]][r["result_num"]]
                    res, revisit = cls._run_subbed_cmd(cmd, results)
                    if res is not None:
                        results[r["name"]][r["result_num"]] = res
                    if revisit:
                        still_revisit.append(r)
                else:
                    #current = results[r["name"]]
                    res, revisit = cls._run_subbed_cmd(cmd, results)
                    if res is not None:
                        results[r["name"]] = res
                    if revisit:
                        still_revisit.append(r)

            if len(still_revisit) == len(revisits):
                raise ResolutionException("Unable to resolve all references")

            revisits = still_revisit

        # all records which have a "post" script, get them and run the post scripts
        for post in posts:
            cmd = cmds[post["name"]]
            if "cmd_num" in post:
                cmd = cmd[post["cmd_num"]]
                rec = results[post["name"]][post["result_num"]]
                for fn in cmd[1].get("post", []):
                    fn(rec, results)
            else:
                rec = results[post["name"]]
                for fn in cmd[1].get("post", []):
                    fn(rec, results)

        if on_complete is not None:
            on_complete(results)

        return results

    @classmethod
    def _run_cmd(cls, cmd):
        fn = cmd[0]
        props = cmd[1]
        if "subs" in props:
            return None
        result = fn(*props.get("args", []), **props.get("kwargs", {}))
        return result

    @classmethod
    def _run_subbed_cmd(cls, cmd, results):
        revisit = False
        fn = cmd[0]
        props = cmd[1]
        if "subs" not in props:
            return None, False
        nkwargs = {}
        for n, vfn in props.get("subs", {}).get("kwargs", {}).items():
            try:
                nv = vfn(results)
            except:
                revisit = True
                nv = None
            nkwargs[n] = nv
        kwargs = props.get("kwargs", {})
        kwargs.update(nkwargs)
        result = fn(*props.get("args", []), **kwargs)
        return result, revisit

    # @classmethod
    # def fixed_spread(cls, factory, count, fixed_args=None, fixed_kwargs=None, fixed_sub_kwargs=None):
    #     factories = []
    #     for i in range(count):
    #         props = {}
    #         if fixed_args is not None:
    #             props["args"] = deepcopy(fixed_args)
    #         if fixed_kwargs is not None:
    #             props["kwargs"] = deepcopy(fixed_kwargs)
    #         if fixed_sub_kwargs is not None:
    #             props["kwsubs"] = deepcopy(fixed_sub_kwargs)
    #         factories.append((factory, props))
    #     return factories

    # @classmethod
    # def constrained_spread(cls, factory, count, fixed_args=None, fixed_kwargs=None, fixed_sub_kwargs=None, variant_kwargs=None):
    #     factories = []
    #     for i in range(count):
    #         props = {}
    #         if fixed_args is not None:
    #             props["args"] = deepcopy(fixed_args)
    #         if fixed_kwargs is not None:
    #             props["kwargs"] = deepcopy(fixed_kwargs)
    #         if fixed_sub_kwargs is not None:
    #             props["kwsubs"] = deepcopy(fixed_sub_kwargs)
    #         if variant_kwargs is not None:
    #             v_kwargs = {k: fn(i) for k, fn in variant_kwargs.items()}
    #             if "kwargs" in props:
    #                 props["kwargs"].update(v_kwargs)
    #             else:
    #                 props["kwargs"] = v_kwargs
    #         factories.append((factory, props))
    #     return factories
    #
    # @classmethod
    # def variant_spread(cls, factory, variants, fixed_kwargs, variant_kwargs, sub_kwargs):
    #     factories = []
    #     for v in variants:
    #         base_kwargs = deepcopy(fixed_kwargs)
    #         v_kwargs = {k: fn(v) for k, fn in variant_kwargs.items()}
    #         base_kwargs.update(v_kwargs)
    #
    #         s_kwargs = {k: fn(v) for k, fn in sub_kwargs.items()}
    #
    #         props = {
    #             "kwargs": base_kwargs,
    #             "kwsubs": s_kwargs
    #         }
    #         factories.append((factory, props))
    #     return factories

    @classmethod
    def spread(cls, variants: Union[int, List],
               args_fixed=None,
               args_variant=None,
               kwargs_fixed=None,
               kwargs_variant=None,
               subs_args_fixed=None,
               subs_args_variant=None,
               subs_kwargs_fixed=None,
               subs_kwargs_variant=None,
               factory=None):

        if isinstance(variants, int):
            variants = range(variants)

        if factory is None:
            factory = cls.make

        factories = []
        for entry in variants:
            args = []
            kwargs = {}
            sargs = []
            skwargs = {}

            if args_fixed is not None:
                args = deepcopy(args_fixed)

            if kwargs_fixed is not None:
                kwargs = deepcopy(kwargs_fixed)

            if subs_args_fixed is not None:
                sargs = deepcopy(subs_args_fixed)

            if subs_kwargs_fixed is not None:
                skwargs = deepcopy(subs_kwargs_fixed)

            if args_variant is not None:
                vargs = [x(entry) for x in args_variant]
                args += vargs

            if kwargs_variant is not None:
                vkwargs = {k: fn(entry) for k, fn in kwargs_variant.items()}
                kwargs.update(vkwargs)

            if subs_args_variant is not None:
                vsargs = [x(entry) for x in subs_args_variant]
                sargs += vsargs

            if subs_kwargs_variant is not None:
                vskwargs = {k: fn(entry) for k, fn in subs_kwargs_variant.items()}
                skwargs.update(vskwargs)

            props = {}
            if len(args) > 0:
                props["args"] = args
            if len(kwargs) > 0:
                props["kwargs"] = kwargs
            if len(sargs) > 0 or len(skwargs) > 0:
                props["subs"] = {}
            if len(sargs) > 0:
                props["subs"]["args"] = sargs
            if len(skwargs) > 0:
                props["subs"]["kwargs"] = skwargs

            factories.append((factory, props))
        return factories


class AccountFactory(FixtureFactory):
    @classmethod
    def make(cls, email=None, username=None, name=None, roles=None, password=None):
        if username is None:
            username = cls.create_random_str()

        if email is None:
            email = username + "@example.com"

        if name is None:
            name = "User " + username

        if password is None:
            password = cls.create_random_str()

        acc = models.Account.make_account(email, username, name, roles)
        acc.set_password(password)
        return acc


class EditorialGroupFactory(FixtureFactory):
    @classmethod
    def make(cls, name=None, associates=None):
        eg = models.EditorGroup(**{
            "name": name
        })

        if associates is not None:
            for acc in associates:
                eg.add_associate(acc)

        return eg


class AppFixtureFactory(FixtureFactory):
    @classmethod
    def make(cls, title=None, lmu_diff=None, cd_diff=None, status=None, editor=None, last_updated=None, related_journal=None):
        source = ApplicationFixtureFactory.make_application_source()
        ap = models.Application(**source)
        if title is not None:
            ap.bibjson().title = title
        ap.remove_current_journal()
        ap.remove_related_journal()
        ap.application_type = constants.APPLICATION_TYPE_NEW_APPLICATION
        ap.set_id(ap.makeid())
        if lmu_diff is not None:
            ap.set_last_manual_update(dates.before(datetime.utcnow(), lmu_diff))
        if last_updated is not None:
            ap.set_last_updated(last_updated)
        if cd_diff is not None:
            ap.set_created(dates.before(datetime.utcnow(), cd_diff))
        if status is not None:
            ap.set_application_status(status)

        if editor is not None:
            ap.set_editor(editor)

        if related_journal is not None:
            ap.set_related_journal(related_journal)

        return ap


class JournalFactory(FixtureFactory):
    @classmethod
    def make(cls, id=None, related_application=None):
        j = models.Journal()

        if id is None:
            id = j.makeid()
        j.set_id(id)

        if related_application is not None:
            j.add_related_application(related_application)

        return j


w = 7 * 24 * 60 * 60
pw = FixtureFactory.create_random_str()
# acc = AccountFactory.make(roles=[constants.ROLE_ASSOCIATE_EDITOR], password=pw)
# eg = EditorialGroupFactory.make(name="Todo Associate Group " + acc.id, associates=[acc])
# app1 = AppFixtureFactory.make(title=acc.id + " Stalled Application", lmu_diff=3 * w, cd_diff=3 * w, status=constants.APPLICATION_STATUS_IN_PROGRESS, editor=acc)
# app2 = AppFixtureFactory.make(title=acc.id + " Old Application", lmu_diff=6 * w, cd_diff=6 * w, status=constants.APPLICATION_STATUS_IN_PROGRESS, editor=acc)

acc = (AccountFactory.make, {
    "kwargs": {"roles": [constants.ROLE_ASSOCIATE_EDITOR], "password": pw}
})
eg = (EditorialGroupFactory.make, {
    "kwsubs": {
        "name": lambda ctx: "Todo Associate Group " + ctx["acc"].id,
        "associates": lambda ctx: [ctx["acc"].id]
    }
})
app1 = (AppFixtureFactory.make, {
    "kwargs": { "lmu_diff": 3 * w, "cd_diff": 3 * w, "status": constants.APPLICATION_STATUS_IN_PROGRESS},
    "kwsubs": {
        "title": lambda ctx: ctx["acc"].id + " Stalled Application",
        "editor": lambda ctx: ctx["acc"]
    }
})


# def variant_closure(title_suffix):
#     return lambda ctx: ctx["acc"].id + " " + title_suffix
#
# variants = [("Stalled Application", 3), ("Old Application", 6)]
# apps = []
# for v in variants:
#     apps.append((AppFixtureFactory.make, {
#         "kwargs" : { "lmu_diff": v[1] * w, "cd_diff": v[1] * w, "status": constants.APPLICATION_STATUS_IN_PROGRESS},
#         "kwsubs": {
#             "title": variant_closure(v[0]),
#             "editor": lambda ctx: ctx["acc"]
#         }
#     }))

# make a bunch of applications which are similar in that they are all in the same status
# similar = FixtureFactory.fixed_spread(AppFixtureFactory.make, 10, fixed_kwargs={"status": constants.APPLICATION_STATUS_IN_PROGRESS})

# make a bunch of applications which vary according to specified variations
variants = [
    {"title_suffix": "Stalled Allication", "week_multiplier": 3},
    {"title_suffix": "Old Allication", "week_multiplier": 6},
]

fixed_kwargs = {"status": constants.APPLICATION_STATUS_IN_PROGRESS}

variant_kwargs = {
    "lmu_diff": lambda v: v["week_multiplier"] * w,
    "cd_diff": lambda v: v["week_multiplier"] * w
}

sub_kwargs = {
    "title": lambda v: lambda ctx: ctx["acc"].id + " " + v["title_suffix"],
    "editor": lambda v: lambda ctx: ctx["acc"]
}

#specified = FixtureFactory.variant_spread(AppFixtureFactory.make, variants, fixed_kwargs, variant_kwargs, sub_kwargs)

# make a bunch of applications which all differ in a specific way
fixed_kwargs = {"status": constants.APPLICATION_STATUS_IN_PROGRESS}
variant_kwargs = {"last_updated": lambda i: dates.random_date(dates.before(datetime.utcnow(), 3600), datetime.utcnow())}
#differ = FixtureFactory.constrained_spread(AppFixtureFactory.make, 10, fixed_kwargs=fixed_kwargs, variant_kwargs=variant_kwargs)

# cmds = {"acc": acc, "eg": eg, "app1": app1, "specified": specified, "similar": similar, "differ": differ}
# results = FixtureFactory.factor(cmds)
#
# print(results["acc"])
# print(results["eg"])
# print(results["app1"])
# print(results["specified"])
# print(results["similar"])
# print(results["differ"])


w = 7 * 24 * 60 * 60
pw = FixtureFactory.create_random_str()
cmds = {
    "acc": (AccountFactory.make, {
        "kwargs": {"roles": [constants.ROLE_ASSOCIATE_EDITOR], "password": pw}
    }),
    "eg": (EditorialGroupFactory.make, {
        "subs": {
            "kwargs": {
                "name": lambda ctx: "Todo Associate Group " + ctx["acc"].id,
                "associates": lambda ctx: [ctx["acc"].id]
            }
        }
    }),
    "journal": (JournalFactory.make, {
        "kwargs": { "id": FixtureFactory.create_random_str() },
        "subs": {
            "kwargs": {
                "related_application": lambda ctx: ctx["similar"][0].id
            }
        },
        "post": [
            lambda record, ctx: record.set_in_doaj(True),
            # lambda record, ctx: record.set_related_application(ctx["similar"][0].id) #,
            # lambda record, ctx: record.save()
        ]
    }),
    "similar": AppFixtureFactory.spread(10,
                kwargs_fixed={"status": constants.APPLICATION_STATUS_IN_PROGRESS},
                subs_kwargs_fixed={"related_journal": lambda ctx: ctx["journal"].id}
    ),
    "specified": AppFixtureFactory.spread(
                variants=[
                    {"title_suffix": "Stalled Allication", "week_multiplier": 3},
                    {"title_suffix": "Old Allication", "week_multiplier": 6},
                ],
                kwargs_fixed={"status": constants.APPLICATION_STATUS_IN_PROGRESS},
                kwargs_variant={
                    "lmu_diff": lambda v: v["week_multiplier"] * w,
                    "cd_diff": lambda v: v["week_multiplier"] * w
                },
                subs_kwargs_variant={
                    "title": lambda v: lambda ctx: ctx["acc"].id + " " + v["title_suffix"],
                    "editor": lambda v: lambda ctx: ctx["acc"]
                }
    ),
    "differ": AppFixtureFactory.spread(10,
                kwargs_fixed={"status": constants.APPLICATION_STATUS_IN_PROGRESS},
                kwargs_variant={"last_updated": lambda i: dates.random_date(dates.before(datetime.utcnow(), 3600), datetime.utcnow())}
    )
}



def write_all(results):
    type_ids = {}
    for k, v in results.items():
        if isinstance(v, list):
            for entry in v:
                entry.save()
                if entry.__type__ not in type_ids:
                    type_ids[entry.__type__] = {"class": entry.__class__, "ids": []}
                type_ids[entry.__type__]["ids"].append((entry.id, entry.last_updated))
        else:
            v.save()
            if v.__type__ not in type_ids:
                type_ids[v.__type__] = {"class": v.__class__, "ids": []}
            type_ids[v.__type__]["ids"].append((v.id, v.last_updated))

    for k, v in type_ids.items():
        v["class"].blockall(v["ids"])

results = FixtureFactory.factor(cmds, write_all)

print(models.Journal.pull(results["journal"].id))

print(results["acc"])
print(results["eg"])
print(results["journal"])
print(results["specified"])
print(results["similar"])
print(results["differ"])
