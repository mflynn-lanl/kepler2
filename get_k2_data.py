from bs4 import BeautifulSoup
import requests
import os

dirs = ['COOL', 'HOT']
parent_dirs = ['C4','C5', 'C6', 'C13']
proxies = {'http':'http://proxyout.lanl.gov:8080', 'https':'http://proxyout.lanl.gov:8080'}
base_url = 'http://astronomy.nmsu.edu/jasonj/JOYCE/FIGURES/K2_FIGS/DATA/'
for pdir in parent_dirs:
    for cdir in dirs:
        tail_url = pdir + '/' + cdir + '/'
        url = base_url + tail_url
        r = requests.get(url, proxies=proxies)
        data = r.text
        soup = BeautifulSoup(data)

        for link in soup.find_all('tr'):
            if link.find_all('th'):
                pass
            else:
                for newlink in link.find_all('a'):
                    fname = newlink.get('href')
                    req = requests.get(url + fname, proxies=proxies)
                    if req.status_code == 200:
                        new_path = os.path.join('/Devel/k2/data2/' + tail_url)
                        if not os.path.exists(new_path):
                            os.makedirs(new_path)
                        with open('/Devel/k2/data2/' + tail_url + fname, 'w') as fp:
                            fp.write(req.content)
                            print(fname)
