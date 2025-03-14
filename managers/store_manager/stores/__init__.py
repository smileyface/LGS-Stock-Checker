from managers.store_manager.stores.authority_games_mesa_az import Authority_Games_Mesa_Arizona

STORE_REGISTRY = {
    "authority_games_mesa_az": Authority_Games_Mesa_Arizona()
}

def store_list(slug_list):
    list_of_objects = []
    for x in slug_list:
        list_of_objects.append(STORE_REGISTRY[x])
    return list_of_objects