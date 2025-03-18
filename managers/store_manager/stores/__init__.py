from managers.store_manager.stores.authority_games_mesa_az import Authority_Games_Mesa_Arizona

STORE_REGISTRY = {
    "authority_games_mesa_az": Authority_Games_Mesa_Arizona
}

def store_list(store_list):
    list_of_objects = []
    for x in store_list:
        list_of_objects.append(STORE_REGISTRY[x.slug])
    return list_of_objects