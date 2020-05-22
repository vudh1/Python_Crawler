import re
from urllib.parse import urlparse
import time
from bs4 import BeautifulSoup
from bs4.element import Comment


all_links = dict()
visited_links = dict()
visited_texts = dict()

html_elements = ['head', 'title', 'meta', 'style', 'script', '[document]']

domain_lists = ["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu", "today.uci.edu"]
today_uci_edu_path = "/department/information_computer_sciences"

stop_words = ["a","about","above","after","again","against","all","am","an","and","any","are","aren't","as","at"
                ,"be","because","been","before","being","below","between","both","but","by"
                ,"can't","cannot","could","couldn't"
                ,"did","didn't","do","does","doesn't","doing","don't","down","during"
                ,"each"
                ,"few","for","from","further"
                ,"had","hadn't","has","hasn't","have","haven't","having","he","he'd","he'll","he's","her","here","here's","hers","herself","him","himself","his","how","how's"
                ,"i","i'd","i'll","i'm","i've","if","in","into","is","isn't","it","it's","its","itself"
                ,"let's"
                ,"me","more","most","mustn't","my","myself"
                ,"no","nor","not"
                ,"of","off","on","once","only","or","other","ought","our","ours","ourselves","out","over","own"
                ,"same","shan't","she","she'd","she'll","she's","should","shouldn't","so","some","such"
                ,"than","that","that's","the","their","theirs","them","themselves","then","there","there's","these","they","they'd","they'll","they're","they've","this","those","through","to","too"
                ,"under","until","up"
                ,"very"
                ,"was","wasn't","we","we'd","we'll","we're","we've","were","weren't","what","what's","when","when's","where","where's","which","while","who","who's","whom","why","why's","with","won't","would","wouldn't"
                ,"you","you'd","you'll","you're","you've","your","yours","yourself","yourselves"]


def get_tokens(text):
    tokens = dict()
    num_words = 0
    text = modify_text(text)

    for word in text.split():
        if len(word) >= 2:
            if word not in stop_words:
                if word not in tokens:
                    tokens[word] = 1
                else:
                    tokens[word] += 1
            num_words += 1

    return num_words, tokens

def is_html_visible(element):
    if element.parent.name in html_elements:
        return False
    if isinstance(element, Comment):
        return False
    return True

def store_visited_links(url):
    parsed = urlparse(url)
    parsed_url = parsed.netloc.replace("www.", '') + parsed.path.lower()
    parsed_url = parsed_url.rstrip('/')
    visited_links[parsed_url] = True

def scraper(url, resp):
    links, num_words, tokens = extract_next_links(url, resp)
    valid_links = []

    if links is not None and len(links) > 0:
        for link in links:
            if is_valid(link):
                parsed = urlparse(link)
                parsed_link = parsed.netloc.replace("www.", '')+parsed.path.lower()
                parsed_link = parsed_link.rstrip('/')
                if parsed_link not in all_links and parsed_link not in domain_lists:
                    all_links[parsed_link] = True
                    valid_links.append(link)
        return valid_links, num_words, tokens
    else:
        return None, None, None

def modify_text(text):
    new_text = re.sub("[^.a-zA-Z0-9\\-\\']+", ' ', text)
    new_text = new_text.replace('-',' ')
    new_text = new_text.replace('.', '')
    new_text = new_text.lower()

    return new_text


def extract_next_links(url, resp):
    try:
        if resp is None or resp.get_status() != 200:
            return None, None, None

        store_visited_links(url)

        content = resp.raw_response.content
        html = BeautifulSoup(content, 'html.parser')
        text = html.find_all(text=True)
        text = ' '.join(filter(is_html_visible, text))

        if text in visited_texts:
            return None, None, None
        else:
            visited_texts[text] = True

        num_words, tokens = get_tokens(text)

        #if page contain less than 50 words
        if num_words < 50:
            return None, None, None

        links = []

        for a_tag in html.find_all('a'):
            link = a_tag['href']
            if link not in links:
                links.append(link)
            time.sleep(1)

        return links, num_words, tokens

    except Exception:
        return None, None, None

def is_valid(url):
    try:
        parsed = urlparse(url)

        if parsed.scheme not in set(["http", "https"]):
            return False

        domain = parsed.netloc.replace("www.", '')
        split_domain = '.'.join(domain.split('.')[-3:])

        if split_domain not in domain_lists:
            return False

        path = parsed.path.lower().rstrip('/')
        link = domain + path
        path_terms = re.split("[^a-z0-9A-Z]", path)

        if split_domain == domain_lists[4] and today_uci_edu_path not in path:
            return False

        if re.match("^.*?(/.+?/).*?\1.*$|^.*?/(.+?/)\2.*$", path):
            return False

        for term in path_terms:
            if term == "blog" or term == "calendar" or term == "page":
                return False

        if link in visited_links:
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower().rstrip('/'))

    except TypeError:
        print ("TypeError for ", parsed)
        #raise
        return False







