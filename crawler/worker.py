from threading import Thread
import os
from utils.download import download
from utils import get_logger
from scraper import scraper
import time

total_tokens = dict()
output_folder_name = 'output/'

class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        super().__init__(daemon=True)
        
    def run(self):
        if os.path.exists('./'+output_folder_name) == False:
            os.mkdir(output_folder_name)

        while True:
            try:
                tbd_url = self.frontier.get_tbd_url()
                if not tbd_url:
                    self.logger.info("Frontier is empty. Stopping Crawler.")
                    break
                resp = download(tbd_url, self.config, self.logger)
                self.logger.info(
                    f"Downloaded {tbd_url}, status <{resp.status}>, "
                    f"using cache {self.config.cache_server}.")

                scraped_urls, scraped_num_words, scraped_tokens = scraper(tbd_url, resp)

                if scraped_urls:
                    # add scraped urls to the frontier
                    for s_url in scraped_urls:
                        self.frontier.add_url(s_url)
                    self.frontier.mark_url_complete(tbd_url)
                    # add tbd url and its scraped data to a file
                    with open(output_folder_name+'crawler_all_info.txt', 'a') as f1:
                        f1.write(tbd_url+": "+str(scraped_num_words)+" -> "+str(scraped_tokens)+'\n')
                    with open(output_folder_name+'crawler_num_words.csv', 'a') as f2:
                        f2.write(tbd_url+","+str(scraped_num_words)+'\n')

                    # print('Length: '+str(scraped_num_words)+':'+str(len(scraped_tokens))+'\n')

                    f3 = open(output_folder_name+'crawler_total_freq.csv', 'w')

                    for token,freq in scraped_tokens.items():
                        if token in total_tokens.keys():
                            total_tokens[token] += freq
                        else:
                            total_tokens[token] = freq
                    
                    for token,freq in total_tokens.items():
                        print(str(token)+","+str(freq),file = f3)

                    f3.close()

                time.sleep(self.config.time_delay)
            except Exception:
                continue

