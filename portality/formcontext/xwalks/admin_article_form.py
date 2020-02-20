from portality.crosswalks.article_form import ArticleFormXWalk
from portality.view import forms


class AdminArticleFormXwalk(ArticleFormXWalk):
    """
    ImmutableMultiDict([ ('authors-0-name', ''), ('authors-0-affiliation', ''), ('authors-1-name', ''), ('authors-1-affiliation', ''), ('authors-2-name', ''), ('authors-2-affiliation', ''), ('authors-3-name', 'Mitidieri, André Luis'), ('authors-3-affiliation', ''), ('authors-4-name', 'Guimarães, Letícia Batista'), ('authors-4-affiliation', ''), ('authors-5-name', 'Mazzutti, Luciana Helena Cajas'), ('authors-5-affiliation', ''), ('abstract', 'O presente artigo centra-se em Las memorias del General (1996) e Las vidas del General (2004), do ficcionista e jornalista argentino Tomás Eloy Martínez, enfatizando o sujeito do enunciado e o referente histórico. Apresentamos as reformulações julgadas significativas entre a primeira e a segunda dessas edições, antes de procedermos à análise do papel desempenhado pela memória, pela narrativa e pela reescrita do eu nos artigos que as compõem: 1) \x93Las memorias de Puerta de Hierro\x94; 2) \x93Días de exilio en Madrid \x94; 3) \x93Perón y sus novelas\x94. A voz autobiográfica do ex-presidente da Argentina, impressa nas entrevistas concedidas a Martínez, passa pelas reavaliações do autor no primeiro artigo, deposita-se residualmente no segundo texto, de caráter biográfico, e se une à própria voz autobiográfica do escritor no terceiro e nos paratextos dos livros analisados, em processo que permite notar as fronteiras contíguas entre narrativas memorialísticas, biográficas, históricas e autobiográficas'), ('keywords', 'LITERATURA ARGENTINA,ESCRITORES ARGENTINOS - CRÍTICA E INTERPRETAÇÃO,MARTINEZ,TOMÁS ELOY - CRÍTICA E INTERPRETAÇÃO,AUTOBIOGRAFIAS,PERONISMO (ARGENTINA),PERON,JUAN DOMINGO - BIOGRAFIA'), ('fulltext', 'http://revistaseletronicas.pucrs.br/ojs/index.php/fale/article/view/15435/10129'), ('publication_month', '1'), ('publication_year', '2013'), ('pissn', '0101-3335'), ('eissn', ''), ('volume', '48'), ('number', '4'), ('start', '431'), ('end', '440')])
    """
    @classmethod
    def data2form(cls,form_data, form):
        if form_data["title"]:
            form.title.data = form_data["title"]
        if form_data["doi"]:
            form.doi.data = form_data["doi"]
        if form_data["keywords"]:
            form.keywords.data = form_data["keywords"]
        if form_data["fulltext"]:
            form.fulltext.data = form_data["fulltext"]
        if form_data["publication_month"]:
            form.publication_month.data = form_data["publication_month"]
        if form_data["publication_year"]:
            form.publication_year.data = form_data["publication_year"]
        if form_data["pissn"]:
            form.pissn.data = form_data["pissn"]
        if form_data["eissn"]:
            form.eissn.data = form_data["eissn"]
        if form_data["volume"]:
            form.volume.data = form_data["volume"]
        if form_data["number"]:
            form.number.data = form_data["number"]
        if form_data["start"]:
            form.start.data = form_data["start"]
        if form_data["end"]:
            form.end.data = form_data["end"]
        if form_data["abstract"]:
            form.abstract.data = form_data["abstract"]

        authors = [(k,v) for k, v in form_data.items() if k.startswith('author')]
        tmp_names = ["" for i in range(10)]
        tmp_aff = ["" for i in range(10)]
        tmp_orcid = ["" for i in range(10)]
        for a in authors:
            key = a[0].split("-")
            if key[2] == "name":
                tmp_names[int(key[1])] = a[1]
            elif key[2] == "affiliation":
                tmp_aff[int(key[1])] = a[1]
            elif key[2] == "orcid_id":
                tmp_orcid[int(key[1])] = a[1]

        for i in range(len(tmp_names)):
            author = forms.AuthorForm()
            if tmp_names[i] != "":
                author.name = tmp_names[i]
                author.affiliation = tmp_aff[i]
                author.orcid_id = tmp_orcid[i]
                form.authors.append_entry(author)