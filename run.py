from run_experiment import *
import glob


def find_datasets(selected_dataset):
    found_datasets = glob.glob(os.path.join("source/Datasets", '*.ttl'))
    found_datasets = [x for x in found_datasets if selected_dataset.lower() in x.lower()]

    return found_datasets


def find_shapes_graphs(selected_dataset):
    if selected_dataset.lower() == "lubm":
        return glob.glob(os.path.join("source/ShapesGraphs/lubm", '*.ttl'))
    if selected_dataset.lower() == "ende":
        return ["source/ShapesGraphs/Shape_30.ttl"]


def get_dataset_name_from_uri(selected_dataset, dataset_uri):
    if selected_dataset.lower() == "lubm":
        dataset_parts = dataset_uri.split("-")
        index = dataset_parts[2].split(".")[0]
        return f"lubm/{dataset_parts[1]}{index}"
    if selected_dataset.lower() == "ende":
        dataset_part = dataset_uri.split("(")[0]
        return dataset_part.split("/")[-1]


def get_input_from_user(variable_name, custom_msg=""):
    ans = ''
    user_input = ''
    while ans.lower() != 'y':
        if custom_msg == "":
            user_input = input(f"Enter the {variable_name}")
        else:
            user_input = input(custom_msg)
        ans = input(f"You entered '{user_input}', is that correct? y/N")
        while ans.lower() != 'y' and ans.lower() != 'n':
            ans = input()

    print(f"{variable_name}: '{user_input}' set")
    return user_input


def get_selection_from_user(variable_name, methods):
    ans = ''
    num_methods = len(methods)
    input_string = f"Choose your {variable_name}: "
    index = 1
    for method in methods:
        input_string += f"\n{index}. {method}"
        index += 1

    while ans.lower() != 'y':
        user_input = 0
        while user_input not in range(1, num_methods+1):
            user_input = input(input_string)
            if user_input.isnumeric():
                user_input = int(user_input)
            else:
                print(f"{user_input} is not an option. Please enter a number between 1 and {num_methods}")
                continue

        ans = input(f"You selected '{methods[user_input - 1]}', is that correct? y/N")
        while ans.lower() != 'y' and ans.lower() != 'n':
            ans = input()

    print(f"{variable_name}: '{methods[user_input - 1]}' set")

    return methods[user_input - 1]


# def select_dataset_by_user():

def user_wants_prebuilt_dataset():
    return get_selection_from_user("method", ["Built-in", "Custom"]) == "Built-in"


if __name__ == '__main__':
    user_wants_prebuilt = user_wants_prebuilt_dataset()
    if user_wants_prebuilt:
        selected_dataset = get_selection_from_user("dataset", ["EnDe", "LUBM"])
        datasets = find_datasets(selected_dataset)
        dataset_uri = get_selection_from_user("dataset", datasets)
        dataset_name = get_dataset_name_from_uri(selected_dataset, dataset_uri)
        print(dataset_name)
        shapes_graphs = find_shapes_graphs(selected_dataset)
        shapes_graph_uri = get_selection_from_user("shapes graph", shapes_graphs)
    else:
        dataset_name = get_input_from_user("dataset folder name")
        dataset_uri = get_input_from_user("dataset filepath")
        shapes_graph_uri = get_input_from_user("shapes filepath")

    method = get_selection_from_user("method", ['pyshacl', 'pyshacl-rdfs', 'pyshacl-owl', 'reshacl'])
    print(f"Running experiment {dataset_name} using method {method}")
    run_experiment(dataset_name, dataset_uri, shapes_graph_uri, method)
