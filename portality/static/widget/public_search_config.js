$.extend(true, doaj, {
    publicSearchConfig : {
        publicSearchPath : '/query/journal,article/_search?ref=fqw',
        lccTree: '{{ lcc_tree|tojson }}'
    }
});