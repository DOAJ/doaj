$.extend(true, doaj, {
    publicSearchConfig : {
        publicSearchPath : 'http://localhost:5004/query/journal,article/_search?ref=fqw',
        lccTree: '{{ lcc_tree|tojson }}'
    }
});