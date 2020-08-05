# coding=UTF-8

from copy import deepcopy
from portality.harvester.epmc import models


class EPMCFixtureFactory(object):

    @classmethod
    def epmc_metadata(cls):
        return models.EPMCMetadata(deepcopy(EPMC_JSON))

    @classmethod
    def epmc_empty_metadata(cls):
        return models.EPMCMetadata({})


class HarvestStateFactory(object):

    @classmethod
    def harvest_state(cls):
        return deepcopy(STATE)


STATE = {
    "id" : "oqwiwfqwjfwejfw",
    "created_date": "1970-01-01T00:00:00Z",
    "last_updated" : "1970-01-01T00:00:00Z",
    "issn" : "1234-5678",
    "account" : "123456789",
    "status" : "active",
    "last_harvest" : [
        {
            "plugin" : "epmc",
            "date" : "1970-01-01T00:00:00Z"
        }
    ]
}


EPMC_JSON = {
    "id": "20981092",
    "source": "MED",
    "pmid": "20981092",
    "pmcid": "PMC3042601",
    "title": "A map of human genome variation from population-scale sequencing.",
    "authorString": "1000 Genomes Project Consortium, Abecasis GR, Altshuler D, Auton A, Brooks LD, Durbin RM, Gibbs RA, Hurles ME, McVean GA.",
    "authorList": {
        "author": [
            {
                "collectiveName": "1000 Genomes Project Consortium"
            },
            {
                "fullName": "Abecasis GR",
                "firstName": "Gonçalo R",
                "lastName": "Abecasis",
                "initials": "GR"
            },
            {
                "fullName": "Altshuler D",
                "firstName": "David",
                "lastName": "Altshuler",
                "initials": "D"
            },
            {
                "fullName": "Auton A",
                "firstName": "Adam",
                "lastName": "Auton",
                "initials": "A"
            },
            {
                "fullName": "Brooks LD",
                "firstName": "Lisa D",
                "lastName": "Brooks",
                "initials": "LD"
            },
            {
                "fullName": "Durbin RM",
                "firstName": "Richard M",
                "lastName": "Durbin",
                "initials": "RM"
            }
        ]
    },
    "journalInfo": {
        "issue": "7319",
        "volume": "467",
        "journalIssueId": 1778804,
        "dateOfPublication": "2010 Oct",
        "monthOfPublication": 10,
        "yearOfPublication": 2010,
        "printPublicationDate": "2010-10-01",
        "journal": {
            "title": "Nature",
            "medlineAbbreviation": "Nature",
            "essn": "1476-4687",
            "issn": "0028-0836",
            "isoabbreviation": "Nature",
            "nlmid": "0410462"
        }
    },
    "pageInfo": "1061-1073",
    "abstractText": "The 1000 Genomes Project aims to provide a deep characterization of human genome sequence variation as a foundation for investigating the relationship between genotype and phenotype. Here we present results of the pilot phase of the project, designed to develop and compare different strategies for genome-wide sequencing with high-throughput platforms. We undertook three projects: low-coverage whole-genome sequencing of 179 individuals from four populations; high-coverage sequencing of two mother-father-child trios; and exon-targeted sequencing of 697 individuals from seven populations. We describe the location, allele frequency and local haplotype structure of approximately 15 million single nucleotide polymorphisms, 1 million short insertions and deletions, and 20,000 structural variants, most of which were previously undescribed. We show that, because we have catalogued the vast majority of common variation, over 95% of the currently accessible variants found in any individual are present in this data set. On average, each person is found to carry approximately 250 to 300 loss-of-function variants in annotated genes and 50 to 100 variants previously implicated in inherited disorders. We demonstrate how these results can be used to inform association and functional studies. From the two trios, we directly estimate the rate of de novo germline base substitution mutations to be approximately 10(-8) per base pair per generation. We explore the data with regard to signatures of natural selection, and identify a marked reduction of genetic variation in the neighbourhood of genes, due to selection at linked sites. These methods and public data will support the next phase of human genetic research.",
    "language": "eng",
    "pubModel": "Print",
    "fullTextUrlList": {
        "fullTextUrl": [
            {
                "availability": "Free",
                "availabilityCode": "F",
                "documentStyle": "pdf",
                "site": "Europe_PMC",
                "url": "http://europepmc.org/articles/PMC3042601?pdf=render"
            },
            {
                "availability": "Free",
                "availabilityCode": "F",
                "documentStyle": "html",
                "site": "Europe_PMC",
                "url": "http://europepmc.org/articles/PMC3042601"
            },
            {
                "availability": "Free",
                "availabilityCode": "F",
                "documentStyle": "html",
                "site": "PubMedCentral",
                "url": "http://www.pubmedcentral.nih.gov/articlerender.fcgi?tool=EBI&pubmedid=20981092"
            },
            {
                "availability": "Free",
                "availabilityCode": "F",
                "documentStyle": "pdf",
                "site": "PubMedCentral",
                "url": "http://www.pubmedcentral.nih.gov/picrender.fcgi?tool=EBI&pubmedid=20981092&action=stream&blobtype=pdf"
            },
            {
                "availability": "Subscription required",
                "availabilityCode": "S",
                "documentStyle": "doi",
                "site": "DOI",
                "url": "http://dx.doi.org/10.1038/nature09534"
            }
        ]
    },
    "isOpenAccess": "N",
    "inEPMC": "Y",
    "inPMC": "Y",
    "hasPDF": "Y",
    "hasBook": "N",
    "citedByCount": 2614,
    "hasReferences": "Y",
    "hasTextMinedTerms": "Y",
    "hasDbCrossReferences": "N",
    "hasLabsLinks": "Y",
    "hasTMAccessionNumbers": "N",
    "dateOfCompletion": "2010-12-14",
    "dateOfCreation": "2010-10-28",
    "dateOfRevision": "2015-08-13",
    "firstPublicationDate": "2010-10-01",
    "luceneScore": "NaN",
    "doi": "10.1038/nature09534"
}