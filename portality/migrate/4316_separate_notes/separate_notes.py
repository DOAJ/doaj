from copy import deepcopy
import dictdiffer

from portality.models import Application, Journal, DraftApplication, JournalLikeObject
from portality.models.note import Note

MODELS = [
    Application, Journal, DraftApplication
]

MAX_BATCH = 1000

def extract_notes(model_class, jl:dict) -> tuple[JournalLikeObject, list[Note]]:
    notes = deepcopy(jl.get("admin", {}).get("notes", []))
    if len(notes) > 0:
        del jl["admin"]["notes"]

    jl_obj = model_class(**jl)

    for note_data in notes:
        del note_data["id"] # Notes may share IDs across objects, because they've never been globally unique before
        # This will also sort out any flags
        jl_obj.add_note_by_dict(note_data)

    note_objects = jl_obj.note_objects

    return jl_obj, note_objects

def _diff(original, current):
    thediff = {}
    context = thediff

    def recurse(context, c, o):
        dd = dictdiffer.DictDiffer(c, o)
        changed = dd.changed()
        added = dd.added()

        for a in added:
            context[a] = c[a]

        for change in changed:
            sub = c[change]
            if isinstance(c[change], dict):
                context[change] = {}
                recurse(context[change], c[change], o[change])
            else:
                context[change] = sub

    recurse(context, current, original)
    return thediff

for model_class in MODELS:
    jbatch = []
    nbatch = []

    for result in model_class.iterate(wrap=False):
        original = deepcopy(result)
        new_jl, notes = extract_notes(model_class, result)

        new_jl.prep()
        jl_data = new_jl.data
        jbatch.append(jl_data)

        for note in notes:
            nbatch.append(note.data)

        if len(jbatch) > MAX_BATCH or len(nbatch) > MAX_BATCH:
            print(f"batch {len(jbatch)}, nbatch {len(nbatch)}")
            model_class.bulk(jbatch, action="index")
            Note.bulk(nbatch)
            jbatch = []
            nbatch = []

    if len(jbatch) > 0:
        model_class.bulk(jbatch, action="index")
    if len(nbatch) > 0:
        Note.bulk(nbatch)



