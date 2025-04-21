import argparse
import webbrowser
from datetime import datetime
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup


def search(query: str, engine="duck", open_results=False, print_results=True, history_path="search_history.txt") -> list:
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    if engine == "duck":
        url = f"https://lite.duckduckgo.com/lite/?q={quote_plus(query)}"
    elif engine == "startpage":
        url = f"https://www.startpage.com/sp/search?query={quote_plus(query)}"
    else:
        raise ValueError("Unsupported engine")

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    with open(engine+".html", "w", encoding="utf-8") as f:
        f.write(response.text)

    soup = BeautifulSoup(response.text, "html.parser")

    if engine == "duck":
        links = [a["href"] for a in soup.select("a.result-link")]
    elif engine == "startpage":
        links = [a["href"] for a in soup.select("a.w-gl__result-title")]

    if print_results:
        for i, link in enumerate(links, 1):
            print(f"[{i}] {link}")

    if open_results:
        for link in links:
            webbrowser.open(link)

    # Save to history
    with open(history_path, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] ({engine}) {query}\n")
        for link in links:
            f.write(f"  {link}\n")
        f.write("\n")

    return links


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simple web search tool.")
    parser.add_argument("query", nargs="+", help="Search query")
    parser.add_argument("--engine", choices=["duck", "startpage"], default="duck", help="Search engine to use")
    parser.add_argument("--open", action="store_true", help="Open results in browser")
    parser.add_argument("--no-print", action="store_true", help="Don't print results to terminal")
    parser.add_argument("--history", default="search_history.txt", help="Path to save search history")
    args = parser.parse_args()

    query_string = " ".join(args.query)
    search(
        query=query_string,
        engine=args.engine,
        open_results=args.open,
        print_results=not args.no_print,
        history_path=args.history
    )
