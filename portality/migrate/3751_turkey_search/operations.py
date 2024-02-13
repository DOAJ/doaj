from portality.models.v2.journal import JournalLikeObject


def correct_turkey(obj):
    obj: JournalLikeObject
    if obj.data.get('index', {}).get('country') == 'Turkey':
        print(f'fix {obj.id}, {obj.bibjson().title} ')
        obj.data['index']['country'] = 'Türkiye'
    return obj
