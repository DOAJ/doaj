from portality.clcsv import ClCsv

ISSNS = ["1234-5678", "2345-6789", "3456-7890"]

# FIXME: this needs to contain the actual list of questions in the spreadsheet, which should
# actually come from somewhere standard (like the re-application to spreadsheet crosswalk)
QUESTIONS = [
    'Q1',
    'Q2',
    'Q3',
    'Q4',
    'Q5',
    'Q6',
    'Q7',
    'Q8',
    'Q9',
    'Q10',
    'Q11',
    'Q12',
    'Q13',
    'Q14',
    'Q15',
    'Q16',
    'Q17',
    'Q18',
    'Q19',
    'Q20',
    'Q21',
    'Q22',
    'Q23',
    'Q24',
    'Q25',
    'Q26',
    'Q27',
    'Q28',
    'Q29',
    'Q30',
    'Q31',
    'Q32',
    'Q33',
    'Q34',
    'Q35',
    'Q36',
    'Q37',
    'Q38',
    'Q39',
    'Q40',
    'Q41',
    'Q42',
    'Q43',
    'Q44',
    'Q45',
    'Q46',
    'Q47',
    'Q48',
    'Q49',
    'Q50',
    'Q51',
    'Q52',
    'Q53',
    'Q54',
    'Q55',
    'Q56'
]

sheet = ClCsv("reapplication.csv")
sheet.set_column("", QUESTIONS)


