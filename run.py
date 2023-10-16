from run_experiment import *


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
    while ans.lower() != 'y':
        user_input = 0
        while user_input not in range(1, 5):
            user_input = input("Choose your method (default: pyshacl): "
                               "\n1. pyshacl \n2. pyshacl-rdfs \n3. pyshacl-owl \n4. reshacl")
            if user_input.isnumeric():
                user_input = int(user_input)
            else:
                print(f"{user_input} is not an option. Please enter a number between 1 and 4")
                continue

        ans = input(f"You selected '{methods[user_input - 1]}', is that correct? y/N")
        while ans.lower() != 'y' and ans.lower() != 'n':
            ans = input()

    print(f"{variable_name}: '{methods[user_input - 1]}' set")

    return methods[user_input - 1]


if __name__ == '__main__':
    dataset_name = get_input_from_user("dataset folder name")
    dataset_uri = get_input_from_user("dataset filepath")
    shapes_graph_uri = get_input_from_user("shapes filepath")
    method = get_selection_from_user("method", ['pyshacl', 'pyshacl-rdfs', 'pyshacl-owl', 'reshacl'])
    print(f"Running experiment {dataset_name} using method {method}")
    run_experiment(dataset_name, dataset_uri, shapes_graph_uri, method)
