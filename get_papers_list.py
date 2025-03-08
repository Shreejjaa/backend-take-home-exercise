import argparse
import pubmed_fetcher

def main():
    parser = argparse.ArgumentParser(description="Fetch research papers from PubMed.")
    parser.add_argument("query", type=str, help="Search query for fetching papers.")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("-f", "--file", type=str, help="Output file to save results")

    args = parser.parse_args()
    
    if args.debug:
        print(f"Fetching papers for query: {args.query}")

    papers = pubmed_fetcher.get_papers(args.query, max_results=10)

    if args.file:
        pubmed_fetcher.save_to_csv(papers, args.file)
        print(f"Results saved to {args.file}")
    else:
        for paper in papers:
            print(paper)

if __name__ == "__main__":
    main()
