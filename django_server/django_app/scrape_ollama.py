import requests
from bs4 import BeautifulSoup


def get_model_description(model_soup):
    model_description = model_soup.find("meta", attrs={"content": True})["content"]

    return model_description


def get_parameter_size_pairs(model_soup):
    sections = model_soup.find_all("section")

    words = sections[0].get_text().split()
    stripped_words = [word.strip() for word in words]
    useful_information = stripped_words[1:-4]
    pairs = list(zip(useful_information[::2], useful_information[1::2]))

    return pairs


def parse_number(number_str):
    if "," in number_str:
        return float(number_str.replace(",", ""))

    if "K" in number_str:
        return float(number_str.replace("K", "")) * 1_000
    elif "M" in number_str:
        return float(number_str.replace("M", "")) * 1_000_000
    else:
        return float(number_str)


def scrape_ollama():
    base_url = "https://ollama.com/library/"

    response = requests.get(base_url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")

        models = soup.find_all("h2")
        models.pop(0)

        for model in models:
            title = model.get_text().strip()

            if title == "":
                continue

            url = base_url + title

            model_response = requests.get(url)
            model_soup = BeautifulSoup(model_response.content, "html.parser")

            pull_count = model_soup.find(
                "span", attrs={"x-test-pull-count": True}
            ).get_text()
            pull_count_number = parse_number(pull_count)

            if pull_count_number < 500_000:
                continue

            model_description = get_model_description(model_soup)
            parameter_size_pairs = get_parameter_size_pairs(model_soup)

            for parameters, size in parameter_size_pairs:
                server_url = "http://localhost:8000/ai-models/"

                request_data = {
                    "name": title,
                    "model": title,
                    "description": model_description,
                    "popularity": int(pull_count_number),
                    "can_process_image": "false",
                    "parameters": parameters,
                    "size": size,
                }

                response = requests.post(
                    server_url,
                    json=request_data,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 201:
                    print(f"Model {title} added successfully")
                elif response.status_code == 200:
                    print(f"Model {title} updated successfully")
                else:
                    print(f"Model {title} failed to add")


if __name__ == "__main__":
    scrape_ollama()
