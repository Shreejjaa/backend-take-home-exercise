import requests
import csv
import re
from typing import List, Dict, Optional

PUBMED_API_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

HEADERS = {"User-Agent": "PubMedPaperFetcher/1.0"}

NON_ACADEMIC_KEYWORDS = ["Inc", "Ltd", "Pharmaceutical", "Biotech", "Corp", "LLC"]
ACADEMIC_DOMAINS = [".edu", ".ac.", ".gov"]

def clean_publication_date(text: str) -> str:
    """Extracts and formats the publication date from XML."""
    year_match = re.search(r"<Year>(\d{4})</Year>", text)
    month_match = re.search(r"<Month>([A-Za-z]+|\d{1,2})</Month>", text)
    day_match = re.search(r"<Day>(\d{1,2})</Day>", text)

    year = year_match.group(1) if year_match else "Unknown"
    month = month_match.group(1) if month_match else "Unknown"
    day = day_match.group(1) if day_match else ""

    if day:
        return f"{year}-{month}-{day}"
    elif month != "Unknown":
        return f"{year}-{month}"
    return year  # If only the year is found

def fetch_paper_ids(query: str, max_results: int = 10) -> List[str]:
    """Fetch paper IDs based on a user query."""
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": max_results
    }
    response = requests.get(PUBMED_API_URL, params=params, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    return data.get("esearchresult", {}).get("idlist", [])

def fetch_paper_details(paper_id: str) -> Dict[str, Optional[str]]:
    """Fetch details of a paper using PubMed's eFetch API."""
    params = {
        "db": "pubmed",
        "id": paper_id,
        "retmode": "xml"
    }
    response = requests.get(PUBMED_FETCH_URL, params=params, headers=HEADERS)
    response.raise_for_status()
    text = response.text

    title = re.search(r"<ArticleTitle>(.*?)</ArticleTitle>", text)
    publication_date = clean_publication_date(text)
    authors = re.findall(r"<Author>(.*?)</Author>", text)
    affiliations = re.findall(r"<Affiliation>(.*?)</Affiliation>", text)

    non_academic_authors, companies = [], set()
    for i, aff in enumerate(affiliations):
        if any(keyword in aff for keyword in NON_ACADEMIC_KEYWORDS):
            non_academic_authors.append(authors[i] if i < len(authors) else "Unknown")
            companies.add(aff)  # Using a set to remove duplicates

    email_match = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", text)
    corresponding_email = email_match.group(0) if email_match else "Not found"

    return {
        "PubmedID": paper_id,
        "Title": title.group(1) if title else "N/A",
        "Publication Date": publication_date,
        "Non-academic Author(s)": ", ".join(non_academic_authors) if non_academic_authors else "None",
        "Company Affiliation(s)": ", ".join(companies) if companies else "None",
        "Corresponding Author Email": corresponding_email
    }

def save_to_csv(papers: List[Dict[str, str]], filename: str):
    """Save paper details to a CSV file."""
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=papers[0].keys())
        writer.writeheader()
        writer.writerows(papers)

def get_papers(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """Fetch and filter papers based on query."""
    paper_ids = fetch_paper_ids(query, max_results)
    papers = [fetch_paper_details(paper_id) for paper_id in paper_ids]
    return papers
