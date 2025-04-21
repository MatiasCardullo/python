import argparse
import webbrowser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os


def build_search_url(engine, query):
    if engine == "google":
        return f"https://www.google.com/search?q={query}"
    elif engine == "duckduckgo":
        return f"https://duckduckgo.com/html/?q={query}"
    elif engine == "bing":
        return f"https://www.bing.com/search?q={query}"
    else:
        raise ValueError("Unsupported search engine")


def extract_links(engine, html, limit):
    soup = BeautifulSoup(html, 'html.parser')
    links = []

    if engine == "google":
        for g in soup.select('div.yuRUbf > a'):
            href = g.get('href')
            if href:
                links.append(href)
    elif engine == "duckduckgo":
        for a in soup.select('a.result__url'):
            href = a.get('href')
            if href:
                links.append(href)
    elif engine == "bing":
        for li in soup.select('li.b_algo h2 a'):
            href = li.get('href')
            if href:
                links.append(href)

    return links[:limit]


def save_history(query_str, engine, results):
    history_path = os.path.join(os.path.dirname(__file__), 'history.txt')
    with open(history_path, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]\n")
        f.write(f"Search: {query_str}\nEngine: {engine}\n")
        for idx, link in enumerate(results, start=1):
            f.write(f"[{idx}] {link}\n")
        f.write("\n")


def main():
    parser = argparse.ArgumentParser(description="Simple web search script")
    parser.add_argument('query', nargs='+', help='Search query')
    parser.add_argument('--engine', choices=['google', 'duckduckgo', 'bing'], default='google')
    parser.add_argument('--limit', type=int, default=5)
    parser.add_argument('--open', action='store_true')
    parser.add_argument('--print', dest='do_print', action='store_true', default=True)
    parser.add_argument('--no-print', dest='do_print', action='store_false')

    args = parser.parse_args()
    query_str = '+'.join(args.query)

    try:
        url = build_search_url(args.engine, query_str)
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        results = extract_links(args.engine, response.text, args.limit)

        if args.do_print:
            for idx, link in enumerate(results, start=1):
                print(f"[{idx}] {link}")

        if args.open:
            for link in results:
                webbrowser.open(link)

        save_history(' '.join(args.query), args.engine, results)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    main()
