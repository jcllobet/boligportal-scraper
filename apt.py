from selenium import webdriver
from bs4 import BeautifulSoup
import json 
from time import sleep
import vlc 
from tqdm import tqdm  
from selenium.webdriver.chrome.options import Options


APT_URL = 'https://www.boligportal.dk/find?placeIds=19%2C817%2C14%2C49%2C106%2C24%2C44&housingTypes=1%2C3%2C4&maxRent=10500'
seen_apartments = {}

MAX_PRICE = 10400


def get_apartment_str(title, location, price, url): 
    return f'{title}-{location}-{price}-{url}'


def new_apartments(apartments): 
    new_apartments = []
    for title, location, price, url in apartments: 

        if url not in seen_apartments and price < MAX_PRICE: 
            new_apartments.append((title, location, price, url))

        seen_apartments[url] = {
            'title': title, 
            'location': location, 
            'price': price
        }
    
    return new_apartments


def print_apartment(title, location, price, url): 
    url = f'https://www.boligportal.dk{url}'

    bottom_line_length = len(url)
    bottom_line = ''.join(['-' for _ in range(bottom_line_length)])
    bottom_line = f'--|----{bottom_line}'

    title_line = f'--|--- {title}'
    title_line_missing = len(bottom_line) - len(title_line) - 1
    title_line += ' '
    title_line += ''.join(['-' for _ in range(title_line_missing)])
    
    print()
    print(f'{title_line}')
    print(f'  |    kr. {price}')
    print(f'  |    {location}')
    print(f'  |    {url}')
    print(f'{bottom_line}')
    print()


if __name__ == '__main__': 

    with open('apartments.json') as fp: 
        seen_apartments = json.load(fp)

    while True: 
        try:
            print(f'Fetching pages...')
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox") # linux only
            chrome_options.add_argument("--headless")
            # Get the URL and execute the JavaScript so we have the contents
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(APT_URL)
            rendered_source = driver.page_source

            print(f'Soupifying the contents...')
            # Soupify the contents
            soup = BeautifulSoup(rendered_source, features="html.parser")

            print(f'Getting all the ad_cards on the page...')
            # Get all the ad_cards on the page
            ad_cards = soup.find_all('a', {'class': ['AdCard']})

            print(f'Extracting the title, location, and price...')
            # Extract the title, location, and price of all ad cards
            titles = [card.find_all('div', {'class': ['AdCard__title']})[0].decode_contents() for card in ad_cards]
            locations = [card.find_all('div', {'class': ['AdCard__location']})[0].decode_contents() for card in ad_cards]
            prices = [card.find_all('div', {'class': ['AdCard__price']})[0].decode_contents() for card in ad_cards]
            prices = [int(price.replace(',-', '').replace('.', '').strip()) for price in prices]
            urls = [card['href'] for card in ad_cards]

            print(f'Constructing apartment objects...')
            # Construct apartment objects
            apartments = zip(titles, locations, prices, urls)

            unseen_apartments = new_apartments(apartments)

            print("We have found some apartments")

            if unseen_apartments != {}: 

                # Play sound
                p = vlc.MediaPlayer("done-for-you.mp3")
                p.play()

                # Print the apartments
                for title, location, price, url in unseen_apartments: 
                    print_apartment(title, location, price, url)
                    
                
                with open('apartments.json', 'w+') as fp: 
                    json.dump(seen_apartments, fp, indent=True, ensure_ascii=True)
            
            for _ in tqdm(range(60), desc='Waiting before refresh...'): 
                sleep(1)

        except Exception as err: 
            sleep(5)
            continue
