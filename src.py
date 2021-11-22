import json


class WikiObj:
    def __init__(self, page_id, first_link, num_words, num_sections,
                 num_ext_links, num_int_links):
        self.page_id = page_id
        self.first_link = first_link
        self.num_words = num_words
        self.num_sections = num_sections
        self.num_ext_links = num_ext_links
        self.num_int_links = num_int_links

    def __str__(self):
        return "Page ID: " + str(self.page_id) + ", First Link: " + str(
            self.first_link) + ", Number of Words: " + str(self.num_words) + \
               ", Number of Sections"


def parse_obj(data):
    page_id = data["page_id"]

    first_link = data["sections"][0]["target_page_ids"][0]

    num_words = 0
    for section in data["sections"]:
        num_words += len(section["text"])

    num_sections = len(data["sections"])

    num_ext_links = 0
    last_section = data["sections"][num_sections - 1]
    if last_section["name"] == "External links":
        num_ext_links = len(last_section["target_page_ids"])

    int_links = set()
    for section in data["sections"]:
        int_links.union(set(section["target_page_ids"]))
    num_int_links = len(int_links)

    return WikiObj(page_id, first_link, num_words, num_sections,
                   num_ext_links, num_int_links)


def create_tree():
    f = open('test.jsonl', 'r')
    data = json.load(f)

    for i in data.keys():
        print(i)
    f.close()

tree = {}
create_tree()