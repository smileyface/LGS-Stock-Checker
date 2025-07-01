from .authority_games_mesa_az import Authority_Games_Mesa_Arizona

# Instantiate all store scraper classes
authority_games = Authority_Games_Mesa_Arizona()

# The registry maps store slugs to their implementation instances.
# This is the single source of truth for all available stores.
STORE_REGISTRY = {
    authority_games.slug: authority_games,
    # Add other stores here as they are implemented
}