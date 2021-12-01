import jsonlines
import matplotlib.pyplot as plt
import graphviz
import random
import spacy
import csv
import numpy as np
from scipy.stats import gaussian_kde

PHILOSOPHY_PAGE_ID = 13692155
nlp = spacy.load('en_core_web_lg')


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
               ", Number of Sections: " + str(self.num_sections) + ", Number " \
                                                                   "of " \
                                                                   "External " \
                                                                   "Links: " \
               + str(self.num_ext_links) + ", Number of Internal Links: " + \
               str(self.num_int_links)


def find_first_link_target(text, link_offsets, target_page_ids):
    in_parens = False
    for i in range(len(text)):
        if text[i] == '(':
            in_parens = True

        elif text[i] == ')':
            in_parens = False

        elif not in_parens and i in link_offsets:
            index = link_offsets.index(i)
            return target_page_ids[index]

    return None


def parse_obj(data):
    page_id = data["page_id"]

    text_in_first_section = data["sections"][0]["text"]
    link_offsets = data["sections"][0]["link_offsets"]
    target_page_ids = data["sections"][0]["target_page_ids"]
    first_link = find_first_link_target(text_in_first_section, link_offsets,
                                        target_page_ids)

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
        int_links = int_links.union(set(section["target_page_ids"]))
    num_int_links = len(int_links)

    return WikiObj(page_id, first_link, num_words, num_sections,
                   num_ext_links, num_int_links)


def find_first_link_dist(curr_dist, curr_page_id, visited, tree_to_bfs,
                         memoized_data):
    if curr_page_id == PHILOSOPHY_PAGE_ID:
        return curr_dist

    if curr_page_id in visited:
        return None  # means we found a loop before we reached Philosophy;
        # i.e. there is no first link path

    if curr_page_id in memoized_data.keys():
        if memoized_data[curr_page_id] is None:
            return None
        return curr_dist + memoized_data[curr_page_id]

    visited.append(curr_page_id)

    if curr_page_id is None or \
            curr_page_id not in tree_to_bfs.keys() or \
            tree_to_bfs[curr_page_id] is None:
        return None

    return find_first_link_dist(curr_dist + 1, tree_to_bfs[curr_page_id][1],
                                visited, tree_to_bfs, memoized_data)


def populate_first_link_dist_map(tree_to_bfs):
    first_link_dist_map = {}
    f = open("first_link_dist.txt", "w")
    count = 1
    total_num_pages = len(tree_to_bfs.keys())

    for page_id in tree_to_bfs.keys():
        print("Processing page " + str(page_id) + " out of " + str(
            total_num_pages))
        dist = find_first_link_dist(0, page_id, [], tree_to_bfs,
                                    first_link_dist_map)
        first_link_dist_map[page_id] = dist
        f.write(str(page_id) + " " + str(dist) + "\n")
        count += 1

    f.close()
    return first_link_dist_map


def create_tree():
    # keys are page IDs, values are tuples of (wiki_obj, first link ID)
    result_tree = {}

    with jsonlines.open('link_annotated_text.jsonl') as reader:

        for obj in reader:
            wiki_obj = parse_obj(obj)
            print("Processing page " + str(wiki_obj.page_id))
            result_tree[wiki_obj.page_id] = (wiki_obj, wiki_obj.first_link)

    return result_tree


def display_figures(first_link_dist_map, phil_tree):
    first_link_dists = []
    num_words = []
    num_sections = []
    num_ext_links = []
    num_int_links = []

    for page_id in first_link_dist_map.keys():
        wiki_obj = phil_tree[page_id][0]

        if not first_link_dist_map[page_id] is None:
            first_link_dists.append(first_link_dist_map[page_id])

            num_words.append(wiki_obj.num_words)
            num_sections.append(wiki_obj.num_sections)
            num_ext_links.append(wiki_obj.num_ext_links)
            num_int_links.append(wiki_obj.num_int_links)

    plt.figure(0)
    plt.scatter(first_link_dists, num_words, alpha=0.05)
    plt.title("First Link Distances vs Number of Words")
    plt.xlabel("First Link Distance From Philosophy")
    plt.ylabel("Number of Words in Article")
    plt.show()

    plt.figure(1)
    plt.scatter(first_link_dists, num_sections, alpha=0.05)
    plt.title("First Link Distances vs Number of Sections")
    plt.xlabel("First Link Distance From Philosophy")
    plt.ylabel("Number of Sections in Article")
    plt.show()

    plt.figure(2)
    plt.scatter(first_link_dists, num_ext_links, alpha=0.05)
    plt.title("First Link Distances vs Number of External Links")
    plt.xlabel("First Link Distance From Philosophy")
    plt.ylabel("Number of External Links in Article")
    plt.show()

    plt.figure(3)
    plt.scatter(first_link_dists, num_int_links, alpha=0.05)
    plt.title("First Link Distances vs Number of Internal Links")
    plt.xlabel("First Link Distance From Philosophy")
    plt.ylabel("Number of Internal Links in Article")
    plt.show()


def graph_viz(phil_tree):
    dot = graphviz.Digraph(comment='First Link Connections Between Wikipedia '
                                   'Articles')

    for page_id in phil_tree.keys():
        wiki_obj = phil_tree[page_id][0]
        dot.edge(str(page_id), str(wiki_obj.first_link))

    f = open("wiki_dot_source.txt", "w")
    f.write(dot.source)
    f.close()

    # dot.render('wiki.gv', view=True)
    dot.render('doctest-output/wiki.gv').replace('\\', '/')


def find_closest_ancestor(page1, page2, phil_tree, first_link_dist_map):
    if first_link_dist_map[page1] is None or first_link_dist_map[page2] is None:
        # ensures that both pages are in the same (biggest) connected component
        return None

    visited1 = []
    visited2 = []

    curr_page1 = page1
    curr_page2 = page2

    while PHILOSOPHY_PAGE_ID not in visited1 or \
            PHILOSOPHY_PAGE_ID not in visited2:
        visited1.append(curr_page1)
        visited2.append(curr_page2)

        if curr_page1 in visited2:
            return curr_page1

        if curr_page2 in visited1:
            return curr_page2

        wiki_obj1 = phil_tree[curr_page1][0]
        wiki_obj2 = phil_tree[curr_page2][0]

        curr_page1 = wiki_obj1.first_link
        curr_page2 = wiki_obj2.first_link

    print("something's gone awry!")
    return PHILOSOPHY_PAGE_ID


def sample_article(phil_tree):
    num_keys = len(phil_tree.keys())
    rand_index = int(random.random() * num_keys)
    rand_page = list(phil_tree.keys())[rand_index]
    return rand_page


def get_titles():
    result = {}
    with open('page.csv') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            try:
                result[int(row[0])] = row[2]
            except ValueError:
                pass
    return result


def find_one_pair_similarity(phil_tree, first_link_dist_map, ids_to_titles):
    page1 = sample_article(phil_tree)
    while page1 not in ids_to_titles.keys() or ' ' in ids_to_titles[page1]:
        page1 = sample_article(phil_tree)

    page2 = sample_article(phil_tree)
    while page2 == page1 or \
            page2 not in ids_to_titles.keys() or \
            ' ' in ids_to_titles[page2]:
        page2 = sample_article(phil_tree)

    ancestor = find_closest_ancestor(page1, page2, phil_tree,
                                     first_link_dist_map)
    print("ancestor:", ancestor)

    if ancestor is None:
        return None

    # calculate distances to ancestor
    page1_to_phil = first_link_dist_map[page1]
    page2_to_phil = first_link_dist_map[page2]
    ancestor_to_phil = first_link_dist_map[ancestor]
    avg_dist_to_ancestor = ((page1_to_phil - ancestor_to_phil) + (
        page2_to_phil - ancestor_to_phil)) / 2

    title1 = nlp(ids_to_titles[page1])
    title2 = nlp(ids_to_titles[page2])
    similarity = title1.similarity(title2)
    if similarity < 0:
        print('SIMILARITY NEGATIVE. WORDS ARE ', title1, title2)

    return avg_dist_to_ancestor, similarity


def find_many_pair_similarity_graph(phil_tree, first_link_dist_map,
                                    ids_to_titles):
    avg_distances = []
    similarities = []
    for i in range(1000):
        print("on trial:", i)
        result = find_one_pair_similarity(phil_tree, first_link_dist_map,
                                          ids_to_titles)
        if result is not None:
            dist, sim = result
            avg_distances.append(dist)
            similarities.append(sim)

    plt.figure(4)
    plt.scatter(avg_distances, similarities)
    plt.title("Average Distance to Common Ancestor vs Title Similarity")
    plt.xlabel("Average Distance to Common Ancestor")
    plt.ylabel("Title Similarity")
    plt.show()


tree = create_tree()
dist_map = populate_first_link_dist_map(tree)
display_figures(dist_map, tree)
# graph_viz(tree)
# #ids_to_tile = get_titles()
#find_many_pair_similarity_graph(tree, dist_map, ids_to_tile)
