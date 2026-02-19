import re
import sys
import time

import requests
from bs4 import BeautifulSoup


def get_model_description(model_soup):
    model_description = model_soup.find("meta", attrs={"content": True})["content"]
    return model_description


def get_parameter_size_pairs(model_soup):
    """
    Improved function to extract parameter and size pairs from model page.
    Tries multiple methods to find the model variants.
    """
    pairs = []

    # Method 1: Look for the models table/section with specific selectors
    try:
        models_section = None

        sections = model_soup.find_all("section")
        for section in sections:
            text = section.get_text().lower()
            if "models" in text or "size" in text or "parameters" in text:
                models_section = section
                break

        if models_section:
            table = models_section.find("table")
            if table:
                rows = table.find_all("tr")[1:]
                for row in rows:
                    cells = row.find_all(["td", "th"])
                    if len(cells) >= 2:
                        param_cell = cells[0].get_text().strip()
                        size_cell = cells[1].get_text().strip()
                        param_cleaned = clean_parameter_string(param_cell)
                        if param_cleaned:
                            pairs.append((param_cleaned, size_cell))
            else:
                # Method 2: Parse text content more intelligently
                text_content = models_section.get_text()
                pairs = parse_model_variants_from_text(text_content)
    except Exception as e:
        print(f"Error in method 1: {e}")

    # Method 3: Look for specific CSS classes or data attributes
    if not pairs:
        try:
            model_variants = model_soup.find_all(
                class_=re.compile(r"model|variant|size", re.I)
            )
            for variant in model_variants:
                text = variant.get_text().strip()
                if re.search(r"\d+[BM]?.*\d+[BM]", text):
                    parsed = parse_single_variant(text)
                    if parsed:
                        pairs.append(parsed)
        except Exception as e:
            print(f"Error in method 3: {e}")

    # Method 4: Fallback to original method with improvements
    if not pairs:
        try:
            sections = model_soup.find_all("section")
            if sections:
                words = sections[0].get_text().split()
                stripped_words = [word.strip() for word in words if word.strip()]
                pairs = extract_pairs_from_word_list(stripped_words)
        except Exception as e:
            print(f"Error in fallback method: {e}")

    # Method 5: Look for pre-formatted code blocks or specific tags
    if not pairs:
        try:
            code_blocks = model_soup.find_all(["pre", "code"])
            for block in code_blocks:
                text = block.get_text()
                if ":" in text and ("B" in text or "M" in text):
                    pairs.extend(parse_model_variants_from_text(text))
        except Exception as e:
            print(f"Error in method 5: {e}")

    cleaned_pairs = []
    seen_combinations = set()

    for param, size in pairs:
        cleaned_param = clean_parameter_string(param)
        if cleaned_param and (cleaned_param, size) not in seen_combinations:
            cleaned_pairs.append((cleaned_param, size))
            seen_combinations.add((cleaned_param, size))

    return cleaned_pairs if cleaned_pairs else [("unknown", "unknown")]


def clean_parameter_string(param_str):
    if not param_str:
        return None

    if ":" in param_str:
        param_str = param_str.split(":")[-1]

    match = re.search(r"(\d+(?:\.\d+)?)[bB]", param_str)
    if match:
        return match.group(1) + "b"

    return None


def parse_model_variants_from_text(text):
    """
    Parse model variants from raw text using regex patterns.
    """
    pairs = []

    # Pattern 1: "model:variant size" (e.g., "llama2:7b 3.8GB")
    pattern1 = re.findall(
        r"(\w+:[^\s]+)\s+(\d+(?:\.\d+)?[KMGT]?B)", text, re.IGNORECASE
    )
    for param, size in pattern1:
        cleaned_param = clean_parameter_string(param)
        if cleaned_param:
            pairs.append((cleaned_param, size))

    # Pattern 2: "variant parameter size" (e.g., "7b 3.8GB")
    pattern2 = re.findall(r"(\d+(?:\.\d+)?[bB])\s+(\d+(?:\.\d+)?[KMGT]?B)", text)
    for param, size in pattern2:
        cleaned_param = clean_parameter_string(param)
        if cleaned_param:
            pairs.append((cleaned_param, size))

    # Pattern 3: Lines with parameter counts and sizes
    lines = text.split("\n")
    for line in lines:
        line = line.strip()
        if re.search(r"\d+(?:\.\d+)?[bB]", line) and re.search(
            r"\d+(?:\.\d+)?[KMGT]?B", line
        ):
            parts = line.split()
            param_part = None
            size_part = None

            for part in parts:
                if re.match(r".*\d+(?:\.\d+)?[bB]", part):
                    cleaned = clean_parameter_string(part)
                    if cleaned:
                        param_part = cleaned
                elif re.match(r"\d+(?:\.\d+)?[KMGT]?B", part):
                    size_part = part

            if param_part and size_part:
                pairs.append((param_part, size_part))

    return pairs


def parse_single_variant(text):
    match = re.search(
        r"(\d+(?:\.\d+)?[bB])\s*.*?(\d+(?:\.\d+)?[KMGT]?B)", text, re.IGNORECASE
    )
    if match:
        cleaned_param = clean_parameter_string(match.group(1))
        if cleaned_param:
            return (cleaned_param, match.group(2))

    return None


def extract_pairs_from_word_list(words):
    pairs = []

    noise_words = {
        "models",
        "view",
        "all",
        "name",
        "size",
        "context",
        "input",
        "text",
        "latest",
    }
    filtered_words = [w for w in words if w.lower() not in noise_words]

    i = 0
    while i < len(filtered_words) - 1:
        current_word = filtered_words[i]
        next_word = filtered_words[i + 1]

        cleaned_param = clean_parameter_string(current_word)
        if cleaned_param and re.match(
            r"\d+(?:\.\d+)?[KMGT]?B", next_word, re.IGNORECASE
        ):
            pairs.append((cleaned_param, next_word))
            i += 2
        else:
            i += 1

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


def can_process_images(text):
    key_words = [
        "image",
        "vision",
        "multimodal",
        "image generation",
        "image processing",
        "visual",
        "photo",
        "picture",
    ]

    return any(word in text.lower() for word in key_words)


def scrape_ollama(min_pull_count: int) -> bool:
    base_url = "https://ollama.com/library/"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    response = requests.get(base_url, headers=headers)
    time.sleep(1)

    if response.status_code != 200:
        return False

    soup = BeautifulSoup(response.content, "html.parser")

    models = soup.find_all("h2")
    models.pop(0)

    model_index = 1
    processed_models = set()

    for model in models:
        title = model.get_text().strip()

        if title == "":
            continue

        url = base_url + title

        try:
            model_response = requests.get(url, headers=headers)
            time.sleep(1)
            model_soup = BeautifulSoup(model_response.content, "html.parser")

            pull_count = model_soup.find("span", attrs={"x-test-pull-count": True})

            if not pull_count:
                continue

            pull_count_number = parse_number(pull_count.get_text())

            if pull_count_number < min_pull_count:
                continue

            model_description = get_model_description(model_soup)
            parameter_size_pairs = get_parameter_size_pairs(model_soup)

            for parameters, size in parameter_size_pairs:
                model_variant_id = f"{title}:{parameters}:{size}"

                if model_variant_id in processed_models:
                    continue

                processed_models.add(model_variant_id)

                server_url = "http://localhost:8000/ai-models/"

                can_model_process_images = can_process_images(
                    title
                ) or can_process_images(model_description)

                request_data = {
                    "name": title,
                    "model": title,
                    "description": model_description,
                    "popularity": int(pull_count_number),
                    "can_process_image": str(can_model_process_images).lower(),
                    "parameters": parameters,
                    "size": size,
                    "index": model_index,
                }

                response = requests.post(
                    server_url,
                    json=request_data,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 201:
                    print(f"Model {title} ({parameters}) added successfully")
                elif response.status_code == 200:
                    print(f"Model {title} ({parameters}) updated successfully")
                else:
                    print(
                        f"Model {title} ({parameters}) failed to add - : {response.status_code}: {response.text}"
                    )

        except Exception as e:
            print(f"Error processing {title}: {e}")
            continue

        model_index += 1

    return True


if __name__ == "__main__":
    program_parameters = sys.argv

    min_pull_count = 200_000

    if len(program_parameters) > 1:
        min_pull_count = int(program_parameters[1])

    scrape_ollama(min_pull_count)
